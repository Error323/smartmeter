#!/usr/bin/python

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

"""
P1 Addresses (OBIS references) according to the dutch standard table definition
"""
TOTAL_KWH_USED_DAY       = "1-0:1.8.1"
TOTAL_KWH_USED_NIGHT     = "1-0:1.8.2"
TOTAL_KWH_RETURNED_DAY   = "1-0:2.8.1"
TOTAL_KWH_RETURNED_NIGHT = "1-0:2.8.2"
CURRENT_USED_KW          = "1-0:1.7.0"
CURRENT_RETURNED_KW      = "1-0:2.7.0"
TOTAL_GAS_USED           = "0-1:24.2.1"
CURRENT_KWH_TARIFF       = "0-0:96.14.0"

"""
Day and night cost of power per kWh according to my energy company
(energiedirect.nl) and gas cost per cubic meter. All in euros.
"""
DAY_COST_KWH   = 0.23678
NIGHT_COST_KWH = 0.21519
GAS_COST_M3    = 0.63661
POWER_COST_KWH = {1:NIGHT_COST_KWH, 2:DAY_COST_KWH}

class P1Reader:
  def __init__(self):
    self.p1          = serial.Serial()
    self.p1.baudrate = 9600
    self.p1.bytesize = serial.SEVENBITS
    self.p1.parity   = serial.PARITY_EVEN
    self.p1.stopbits = serial.STOPBITS_ONE
    self.p1.xonxoff  = 0
    self.p1.rtscts   = 0
    self.p1.timeout  = 20
    self.p1.port     = "/dev/ttyUSB0"

class P1Parser:
  def __init__(self, filename='energyavg.dat'):
    self.filename = filename
    self.reset()

  def value(self, msg, key):
    begin = msg.find(key)
    match = re.search("[0-9]*\.[0-9]*|0[0-9]*", msg[begin + len(key):])
    return (begin > 0, match.group())

  def parse(self, msg):
    assert(msg[0] == '/')
    assert(msg[-2] == '!')

    val = self.value(msg, CURRENT_KWH_TARIFF)
    assert(val[0])
    self.tariff = int(val[1])

    val = self.value(msg, TOTAL_GAS_USED)
    if (val[0]):
      self.gas += float(val[1])
      self.gas_cost += self.gas * GAS_COST_M3

    val = self.value(msg, CURRENT_USED_KW)
    assert(val[0])
    curkw = float(val[1])
    self.kw += curkw
    self.kwh_monthly_cost += (curkw/3600.0) * POWER_COST_KWH[self.tariff]
    self.counter += 1
    
  def store(self):
    assert(self.counter > 0)
    self.gas /= self.counter
    self.kw /= self.counter
    self.kwh_monthly_cost /= self.counter
    self.kwh_monthly_cost = (self.kwh_monthly_cost * 6.0 * 60.0 * 24.0 * 356.0) / 12.0
    self.gas_cost /= self.counter
    f = open(self.filename, 'w')
    f.write('%f %f %f %f\n' % (self.kw, self.gas, self.kwh_monthly_cost, self.gas_cost))
    f.close()
    self.reset()
    
  def reset(self):
    self.tariff = 0
    self.kw = 0.0
    self.gas = 0.0
    self.kwh_monthly_cost = 0.0
    self.gas_cost = 0.0
    self.counter = 0

class Emulator:
  def __init__(self, parser):
    self.parser = parser

  def file(self, filename):
    f = open(filename, 'r')
    data = [line for line in f.readline()]
    f.close()
    i = 0
    while (True):
      started = False
      msg = ""
      for line in data[i:]:
        i += 1
        if (line[0] == '/'):
          started = True
        if (not started):
          continue
        msg += line
        if (line[0] == '!'):
          break

      if (not started):
        break
      self.parser.parse(msg)

    self.parser.store()

if __name__ == "__main__":
  argparser = argparse.ArgumentParser(description='Smart meter logger')
  argparser.add_argument('--input', type=argparse.FileType('r'), 
                         help='Read data from file, for testing')
  argparser.add_argument('--output', type=argparse.FileType('w'),
                         help='File to write output to')
  argparser.add_argument('--verbose', action="store_true", help='Print debug info to screen')
  argparser.add_argument('--kwh1', type=float, default=DAY_COST_KWH,
                         help='Price of a kWh at day tariff')
  argparser.add_argument('--kwh2', type=float, default=NIGHT_COST_KWH,
                         help='Price of a kWh at night tariff')
  argparser.add_argument('--gas', type=float, default=GAS_COST_M3,
                         help='Price of a cubic meter of gas (m3)')

  args = argparser.parse_args()
  print args
