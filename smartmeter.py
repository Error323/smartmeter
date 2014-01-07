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
import os
import sys
import serial
import argparse
import time
import datetime
import calendar
import signal
import logging, logging.handlers
import rrdtool
from createdb import *

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
  def __init__(self, kwh1, kwh2, gas):
    self.kwh_price = {1:kwh1, 2:kwh2}
    self.gas_price = gas
    self.gas_prev = None
    self.gas_time_prev = None

  def value(self, msg, key):
    begin = msg.find(key)
    match = re.search(r"\d{12}|\d*\.\d*|000[0-2]", msg[begin + len(key):])
    return (begin > 0, match.group())

  def parse(self, msg, time):
    # 1. Obtain kWh tariff
    tariff = self.value(msg, CURRENT_KWH_TARIFF)
    t = 0
    if (tariff[0]):
      t = int(tariff[1])
    else:
      logging.warning("Could not obtain kWh tariff")

    # 2. Update kW I/O and cost
    kw_in = self.value(msg, CURRENT_USED_KW)
    kw_out = self.value(msg, CURRENT_RETURNED_KW)
    if (kw_in[0] and kw_out[0]):
      rrdtool.update(RRDPWR, '%d:%f:%f' % (time, 
        float(kw_in[1])*1000.0, float(kw_out[1])*1000.0))
      kw_cost = (float(kw_in[1]) - float(kw_out[1])) * self.kwh_price[t]
      rrdtool.update(RRDPWRCOST, '%d:%f' % (time, kw_cost))
    else:
      logging.warning("Could not obtain kWh")

    # 3. Update gas usage and cost
    gas = self.value(msg, TOTAL_GAS_USED)
    update = self.value(msg, TIME_GAS_UPDATE)
    if (gas[0] and update[0]):
      gas_cur = float(gas[1])
      gas_time = datetime.datetime.strptime(update[1], "%y%m%d%H%M%S")

      if (self.gas_time_prev != None):
        delta_time = (gas_time - self.gas_time_prev).total_seconds()

        if (delta_time > 0):
          gas_diff = gas_cur - self.gas_prev
          gas_cost = gas_diff * self.gas_price

          time = calendar.timegm(gas_time.utctimetuple())
          rrdtool.update(RRDGAS, '%d:%f' % (time, gas_diff))
          rrdtool.update(RRDGASCOST, '%d:%f' % (time, gas_cost))
          logging.info("g %s %f %f" % (gas_time, gas_diff, gas_cost))

      self.gas_prev = gas_cur
      self.gas_time_prev = gas_time
    else:
      logging.warning("Could not obtain gas usage")
      
    logging.info("r %s %s %s %s" % (kw_in[1], kw_out[1], gas[1], TARIFF[t]))
    
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
    t = long(time.time())
    for line in data:
      if (line[0] == '/'):
        started = True
      if (not started):
        continue
      msg += line
      if (line[0] == '!'):
        self.parser.parse(msg, t)
        msg = ""
        started = False
        t += 10
    data.close()

  def from_p1(self):
    try:
      self.device.open()
    except IOError:
      sys.exit("Error: Could not open device '%s'" % self.device.name)

    msg = line = ""
    started = False
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
        t = calendar.timegm(datetime.datetime.now().utctimetuple())
        self.parser.parse(msg, t)
        msg = ""
        started = False

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
  logger.info("Price for kWh € %f at low tariff" % (cmd_args.kwh1))
  logger.info("Price for kWh € %f at high tariff" % (cmd_args.kwh2))
  logger.info("Price for gas € %f" % (cmd_args.gas))

  p1 = P1Parser(cmd_args.kwh1, cmd_args.kwh2, cmd_args.gas)
  reader = Reader(cmd_args.port, p1)
  if (cmd_args.data):
    logger.info("Reading data from '%s'" % (cmd_args.data.name))
    reader.from_file(cmd_args.data)
  else:
    logger.info("Reading data from '%s'" % (cmd_args.port))
    reader.from_p1()
    
