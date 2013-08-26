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
import os
import serial
import fileinput
import argparse
import time, datetime
import signal

"""
P1 Addresses (OBIS references) according to the dutch standard table definition
"""
TOTAL_GAS_USED          = "0-1:24.2.0"
TOTAL_KWH_USED_HIGH     = "1-0:1.8.1"
TOTAL_KWH_USED_LOW      = "1-0:1.8.2"
TOTAL_KWH_RETURNED_HIGH = "1-0:2.8.1"
TOTAL_KWH_RETURNED_LOW  = "1-0:2.8.2"
CURRENT_USED_KW         = "1-0:1.7.0"
CURRENT_RETURNED_KW     = "1-0:2.7.0"
CURRENT_KWH_TARIFF      = "0-0:96.14.0"

"""
High and low tariff cost of power per kWh according to my energy company
(energiedirect.nl) and gas cost per cubic meter. All in euros.
"""
HIGH_COST_KWH = 0.23678
LOW_COST_KWH  = 0.21519
GAS_COST_M3   = 0.63661
TARIFF        = {1:"L", 2:"H"}

class P1Parser:
  def __init__(self, args):
    self.filename = args.output
    self.kwh_price = {1:args.kwh1, 2:args.kwh2}
    self.gas_price = args.gas
    self.verbose = args.verbose
    self.reset()

  def value(self, msg, key):
    begin = msg.find(key)
    match = re.search("[0-9]*\.[0-9]*|0[0-9]*", msg[begin + len(key):])
    return (begin > 0, match.group())

  def parse(self, msg):
    val = self.value(msg, CURRENT_KWH_TARIFF)
    self.tariff = int(val[1])

    val = self.value(msg, TOTAL_GAS_USED)
    if (val[0]):
      self.gas += float(val[1])

    val = self.value(msg, CURRENT_USED_KW)
    curkw = float(val[1])
    self.kw += curkw
    self.kwh_monthly_cost += curkw * self.kwh_price[self.tariff]
    self.counter += 1
    
  def store(self):
    assert(self.counter > 0)
    self.gas /= self.counter
    self.kw /= self.counter
    self.kwh_monthly_cost /= self.counter
    self.kwh_monthly_cost = (self.kwh_monthly_cost * 24.0 * 365.0) / 12.0
    self.gas_cost = self.gas * self.gas_price
    self.kw *= 1000.0
    f = open(self.filename, 'w')
    f.write('%f %d %f %d\n' % (self.kw, round(self.gas*1000), self.kwh_monthly_cost, round(self.gas_cost*100)))
    f.close()
    if (self.verbose):
      print "Wrote to '%s' at %s:\n  %8.3f\tWatt (%s)\n  %8.3f\tCubic meter (m3)\n  %8.3f\t€ per/month on power\n  %8.3f\t€ total on gas\n" % (self.filename, str(datetime.datetime.now()), self.kw, TARIFF[self.tariff], self.gas, self.kwh_monthly_cost, self.gas_cost)
    self.reset()
    
  def reset(self):
    self.tariff = 0
    self.kw = 0.0
    self.gas = 0.0
    self.kwh_monthly_cost = 0.0
    self.gas_cost = 0.0
    self.counter = 0

class Reader:
  def __init__(self, args, parser):
    self.parser      = parser
    self.p1          = serial.Serial()
    self.p1.baudrate = 9600
    self.p1.bytesize = serial.SEVENBITS
    self.p1.parity   = serial.PARITY_EVEN
    self.p1.stopbits = serial.STOPBITS_ONE
    self.p1.xonxoff  = 0
    self.p1.rtscts   = 0
    self.p1.timeout  = 20
    self.p1.port     = args.port

  def fromFile(self, f):
    msg = ""
    started = False
    for line in f:
      if (line[0] == '/'):
        started = True
      if (not started):
        continue
      msg += line
      if (line[0] == '!'):
        self.parser.parse(msg)
        msg = ""
        started = False
    f.close()
    self.parser.store()

  def fromP1(self):
    try:
      self.p1.open()
    except:
      sys.exit("Could not open serial port '%s'\n" % self.p1.port)

    msg = line = ""
    started = False
    start_time = time.time()
    while (True):
      try:
        line = self.p1.readline()
      except:
        sys.stderr.write("Could not read from device '%s'\n" % self.p1.name)
        break

      if (line[0] == '/'):
        started = True
      if (not started):
        continue
      msg += line
      if (line[0] == '!'):
        self.parser.parse(msg)
        msg = ""
        started = False
        cur_time = time.time()
        if (cur_time - start_time >= 300.0):
          start_time = cur_time
          self.parser.store()
      time.sleep(0.001)
      sys.stdout.flush()

    try:
      self.p1.close()
    except:
      sys.exit("Could not close device '%s'" % self.p1.name)

def sighandler(signum, frame):
  sys.exit("Trapped signal '%d' exit now" % (signum))

if __name__ == "__main__":
  signal.signal(signal.SIGTERM, sighandler)
  signal.signal(signal.SIGINT, sighandler)

  argparser = argparse.ArgumentParser(description='Smart meter logger')
  argparser.add_argument('--input', type=argparse.FileType('r'), help='Read data from file, for testing')
  argparser.add_argument('--output', default='/tmp/energy.dat', help='File to write output to')
  argparser.add_argument('--verbose', action='store_true', help='Print debug info to screen')
  argparser.add_argument('--kwh1', type=float, default=LOW_COST_KWH, help='Price of a kWh at night tariff')
  argparser.add_argument('--kwh2', type=float, default=HIGH_COST_KWH, help='Price of a kWh at day tariff')
  argparser.add_argument('--gas', type=float, default=GAS_COST_M3, help='Price of a cubic meter of gas (m3)')
  argparser.add_argument('--port', default='/dev/ttyUSB0', help='Serial port to read from')

  args = argparser.parse_args()

  p1 = P1Parser(args)
  reader = Reader(args, p1)
  if (args.input):
    reader.fromFile(args.input)
  else:
    reader.fromP1()
    
