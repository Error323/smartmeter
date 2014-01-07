#!/usr/bin/python

import os
import time
import random
import rrdtool
import argparse

# RRD database files
DIR        = os.path.abspath(os.path.dirname(__file__))
RRDPWR     = DIR + '/data/power.rrd'
RRDGAS     = DIR + '/data/gas.rrd'
RRDPWRCOST = DIR + '/data/power-cost.rrd'
RRDGASCOST = DIR + '/data/gas-cost.rrd'

POINTS = 1000
TOTAL   = 60 * 60 * 24 * 365 * 3 # Three yrs in seconds

def rra(total, rtype='AVERAGE'):
  rras = []
  i = 0
  rows = total

  while rows > POINTS:
    step = 2**i
    rows = total / step
    rras.append('RRA:%s:0.5:%d:%d' % (rtype, step, rows))
    print '%2d %5d %10d' % (i,step,rows)
    i += 1
  
  return rras

if __name__ == "__main__":
  argparser = argparse.ArgumentParser(description='Create rrd databases')
  argparser.add_argument('--fill', action='store_true', default=False,
    help='Fill db with random data')
  argparser.add_argument('--gas', action='store_true', default=False,
    help='Create gas databases')
  argparser.add_argument('--power', action='store_true', default=False,
    help='Create power databases')
  cmd_args = argparser.parse_args()
  path = os.path.abspath("data") + '/'

  # create power db
  updateinterval = 10
  total = TOTAL / updateinterval
  if (cmd_args.power):
    print '\nCreating power rrd-databases at:\n %s\n %s' % (RRDPWR, RRDPWRCOST)
    rrdtool.create(RRDPWR, 
                   '-s', str(updateinterval), 
                   'DS:usage:GAUGE:3600:0:U', 
                   'DS:return:GAUGE:3600:0:U', 
                   rra(total))
    rrdtool.create(RRDPWRCOST, 
                   '-s', str(updateinterval), 
                   'DS:cost:GAUGE:3600:0:U', 
                   rra(total))

  # create gas db
  if (cmd_args.gas):
    updateinterval = 60*60
    total = TOTAL / updateinterval
    print '\nCreating gas rrd-databases at:\n %s\n %s' % (RRDGAS, RRDGASCOST)
    rrdtool.create(RRDGAS, 
                   '-s', str(updateinterval), 
                   'DS:gas:GAUGE:5400:0:U', 
                   rra(total))
    rrdtool.create(RRDGASCOST, 
                   '-s', str(updateinterval), 
                   'DS:cost:GAUGE:5400:0:U', 
                   rra(total))

  if cmd_args.fill:
    print '\nFilling databases with random data'
    start = long(time.time())
    if (cmd_args.power):
      t = start
      step = 300
      for i in range(0, TOTAL, step):
        rrdtool.update(RRDPWR, '%d:%f:%f' % (t, random.random()*i, i))
        rrdtool.update(RRDPWRCOST, '%d:%f' % (t, random.random()*i))
        t += step

    if (cmd_args.gas):
      step = 3600
      t = start - (start % step) + step
      counter = 0
      for i in range(0, TOTAL, step):
        counter += 1
        if (random.randint(0,3) == 1):
          rrdtool.update(RRDGASCOST, '%d:U' % (t))
          rrdtool.update(RRDGAS, '%d:U' % (t))
        else:
          rrdtool.update(RRDGASCOST, '%d:%f' % (t, 1.0))
          rrdtool.update(RRDGAS, '%d:%d' % (t, counter))
        t += step
