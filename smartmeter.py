#!/usr/bin/python
# coding: latin-1

# p1-reader command for dutch smart meters over port p1 (RJ11)
# (C) 2013-08 Folkert Huizinga <folkerthuizinga@gmail.com>

#    This package is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; version 2 dated June, 1991.

#    This package is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this package; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
#    02111-1307, USA.

import re
import sys
import serial
import argparse
import time
import datetime
import signal
import logging, logging.handlers

# P1 Addresses (OBIS references) according to the dutch standard table
# definition
TOTAL_GAS_USED          = "0-1:24.2.0"
TIME_GAS_UPDATE         = "0-1:24.3.0"
TOTAL_KWH_USED_HIGH     = "1-0:1.8.1"
TOTAL_KWH_USED_LOW      = "1-0:1.8.2"
TOTAL_KWH_RETURNED_HIGH = "1-0:2.8.1"
TOTAL_KWH_RETURNED_LOW  = "1-0:2.8.2"
CURRENT_USED_KW         = "1-0:1.7.0"
CURRENT_RETURNED_KW     = "1-0:2.7.0"
CURRENT_KWH_TARIFF      = "0-0:96.14.0"

# High and low tariff cost of power per kWh according to my energy company
# (energiedirect.nl) and gas cost per cubic meter. All in euros.
HIGH_COST_KWH = 0.23678
LOW_COST_KWH  = 0.21519
GAS_COST_M3   = 0.63661
TARIFF        = {1:"L", 2:"H"}

class P1Parser:
  def __init__(self, output, kwh1, kwh2, gas):
    self.filename = output
    self.kw_in = 0.0
    self.kw_out = 0.0
    self.kwh_monthly_cost = 0.0
    self.counter = 0
    self.kwh_price = {1:kwh1, 2:kwh2}
    self.gas_price = gas
    self.gas_prev = -1.0
    self.gas_cur = 0.0
    self.gas = 0.0
    self.gas_monthly_cost = 0.0
    self.gas_time = None
    self.gas_time_prev = None

  def value(self, msg, key):
    begin = msg.find(key)
    match = re.search(r"\d{12}|\d*\.\d*|000[0-2]", msg[begin + len(key):])
    return (begin > 0, match.group())

  def parse(self, msg):
    # 1. Obtain kWh tariff
    tariff = self.value(msg, CURRENT_KWH_TARIFF)
    t = 0
    if (tariff[0]):
      t = int(tariff[1])
    else:
      logging.warning("Could not obtain kWh tariff")

    # 2. Compute gas usage and monthly cost
    #
    # Since this is an integration value, we need to do some checks here before
    # we subtract the current gas value from the previous gas value.
    gas = self.value(msg, TOTAL_GAS_USED)
    update = self.value(msg, TIME_GAS_UPDATE)
    if (gas[0] and update[0]):
      self.gas_cur = float(gas[1])
      self.gas_time = datetime.datetime.strptime(update[1], "%y%m%d%H%M%S")

      if (self.gas_time_prev != None and self.gas_time != None):
        delta_time = (self.gas_time - self.gas_time_prev).total_seconds()

        if (delta_time > 0 and self.gas_prev > -1.0):
          self.gas = (self.gas_cur - self.gas_prev) / (delta_time/300.0) # Usage per 5 min
          self.gas_monthly_cost = self.gas * self.gas_price * 730.0 # (24 * 365) / 12
          logging.info("g %f %f %s" % (self.gas, self.gas_monthly_cost,
                                         str(self.gas_time)))

      self.gas_prev = self.gas_cur
      self.gas_time_prev = self.gas_time
    else:
      logging.warning("Could not obtain gas usage")
      
    # 3. Compute kW usage and monthly cost
    kw_in = self.value(msg, CURRENT_USED_KW)
    if (kw_in[0]):
      curkw = float(kw_in[1])
      self.kw_in += curkw
      self.kwh_monthly_cost += curkw * self.kwh_price[t]
    else:
      logging.warning("Could not obtain kWh input")

    # 4. Compute kW returned and update monthly cost
    kw_out = self.value(msg, CURRENT_RETURNED_KW)
    if (kw_out[0]):
      curkw = float(kw_out[1])
      self.kw_out += curkw
      self.kwh_monthly_cost -= curkw * self.kwh_price[t]
    else:
      logging.warning("Could not obtain kWh output")

    self.counter += 1
    logging.info("r %s %s %s %s" % (kw_in[1], kw_out[1], gas[1], TARIFF[t]))
    
  def store(self):
    assert(self.counter > 0)
    self.kw_in /= self.counter
    self.kw_out /= self.counter
    self.kwh_monthly_cost /= self.counter
    self.kwh_monthly_cost *= 730.0 # (24 * 365) / 12
    self.kw_in *= 1000.0 # to Watt
    self.kw_out *= 1000.0 # to Watt
    output = open(self.filename, 'w')
    output.write('%f %f %f %f %f\n' % (self.kw_in, self.kw_out, self.gas,
                                       self.kwh_monthly_cost,
                                       self.gas_monthly_cost))
    output.close()
    logging.info("w %f %f %f %f %f" % (self.kw_in, self.kw_out, self.gas,
                                       self.kwh_monthly_cost,
                                       self.gas_monthly_cost)) 

    self.kw_in = 0.0
    self.kw_out = 0.0
    self.kwh_monthly_cost = 0.0
    self.counter = 0

class Reader:
  def __init__(self, port, parser):
    self.device          = serial.Serial()
    self.device.baudrate = 9600
    self.device.bytesize = serial.SEVENBITS
    self.device.parity   = serial.PARITY_EVEN
    self.device.stopbits = serial.STOPBITS_ONE
    self.device.xonxoff  = 0
    self.device.rtscts   = 0
    self.device.timeout  = 20
    self.device.port     = port
    self.parser          = parser

  def from_file(self, data):
    msg = ""
    started = False
    for line in data:
      if (line[0] == '/'):
        started = True
      if (not started):
        continue
      msg += line
      if (line[0] == '!'):
        logging.debug("\n" + msg)
        self.parser.parse(msg)
        msg = ""
        started = False
    data.close()
    self.parser.store()

  def from_p1(self):
    try:
      self.device.open()
    except IOError:
      sys.exit("Error: Could not open device '%s'" % self.device.name)

    msg = line = ""
    started = False
    start_time = time.time()
    while (True):
      try:
        line = self.device.readline()
      except IOError:
        logging.critical("Could not read from device '%s'" % self.device.name)
        break

      if (line[0] == '/'):
        started = True
      if (not started):
        continue
      msg += line
      if (line[0] == '!'):
        logging.debug("\n" + msg)
        self.parser.parse(msg)
        msg = ""
        started = False
        cur_time = time.time()
        if (cur_time - start_time >= 300.0):
          start_time = cur_time
          self.parser.store()
      time.sleep(0.001)

    try:
      self.device.close()
    except IOError:
      sys.exit("Error: Could not close device '%s'", self.device.name)

def sighandler(signum, frame):
  logging.critical("Trapped signal '%d' exit now" % (signum))
  sys.exit("Trapped signal '%d' exit now" % (signum))

if __name__ == "__main__":
  signal.signal(signal.SIGTERM, sighandler)
  signal.signal(signal.SIGINT, sighandler)

  argparser = argparse.ArgumentParser(description=\
    'A smart meter logger for the dutch smart meters with a P1 (RJ11) port.')
  argparser.add_argument('--data', type=argparse.FileType('r'), 
    help='Read data from file, for testing')
  argparser.add_argument('--output', default='/tmp/energy.dat', 
    help='File to write output to')
  argparser.add_argument('--kwh1', type=float, default=LOW_COST_KWH, 
    help='Price of a kWh at low tariff')
  argparser.add_argument('--kwh2', type=float, default=HIGH_COST_KWH, 
    help='Price of a kWh at high tariff')
  argparser.add_argument('--gas', type=float, default=GAS_COST_M3, 
    help='Price of a cubic meter of gas (m3)')
  argparser.add_argument('--port', default='/dev/ttyUSB0', 
    help='Serial port to read from')
  argparser.add_argument('--logfile', 
    help='File to log output to')
  argparser.add_argument('--loglvl', default='INFO', 
    help='Set the loglevel in {DEBUG, INFO, WARNING, ERROR, CRITICAL}')

  cmd_args = argparser.parse_args()

  logger = logging.getLogger()
  loglvl = getattr(logging, cmd_args.loglvl.upper(), None)

  if (not isinstance(loglvl, int)):
    sys.exit('Invalid log level: %s' % cmd_args.loglvl)

  logger.setLevel(loglvl)
  formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
  if (cmd_args.logfile):
    handler = logging.handlers.RotatingFileHandler(cmd_args.logfile,
    maxBytes=1048576, backupCount=10)
  else:
    handler = logging.StreamHandler()
  handler.setFormatter(formatter)
  logger.addHandler(handler)
  logger.info("Output file at '%s'" % (cmd_args.output))
  logger.info("Price for kWh € %f at low tariff" % (cmd_args.kwh1))
  logger.info("Price for kWh € %f at high tariff" % (cmd_args.kwh2))
  logger.info("Price for gas € %f" % (cmd_args.gas))
  logger.info("r = read, w = write, g = gas")

  p1 = P1Parser(cmd_args.output, cmd_args.kwh1, cmd_args.kwh2, cmd_args.gas)
  reader = Reader(cmd_args.port, p1)
  if (cmd_args.data):
    logger.info("Reading data from '%s'" % (cmd_args.data.name))
    reader.from_file(cmd_args.data)
  else:
    logger.info("Reading data from '%s'" % (cmd_args.port))
    reader.from_p1()
    
