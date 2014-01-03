#!/usr/bin/python

import os
import time
import random
import rrdtool
import argparse

MINROWS = 1000
TOTAL   = 60 * 60 * 24 * 365 * 3 # Three yrs in seconds

def rra(total):
  rras = []
  i = 0
  rows = total

  while rows > MINROWS:
    step = 2**i
    rows = total / step
    rras.append('RRA:AVERAGE:0.5:%d:%d' % (step, rows))
    print '%2d %5d %10d' % (i,step,rows)
    i += 1
  
  return rras

if __name__ == "__main__":
  argparser = argparse.ArgumentParser(description='Create rrd databases')
  argparser.add_argument('--fill', action='store_true', default=False,
    help='Fill db with random data')
  cmd_args = argparser.parse_args()
  path = os.path.abspath("data") + '/'

  # create power db
  updateinterval = 10
  total = TOTAL / updateinterval
  print '\nCreating power db at %s' % (path + 'power.rrd')
  rrdtool.create(path + 'power.rrd', 
                 '-s', str(updateinterval), 
                 'DS:Usage:GAUGE:3600:0:U', 
                 'DS:Return:GAUGE:3600:0:U', 
                 rra(total))

  # create gas db
  updateinterval = 60*60
  total = TOTAL / updateinterval
  print '\nCreating gas db at %s' % (path + 'gas.rrd')
  rrdtool.create(path + 'gas.rrd', 
                 '-s', str(updateinterval), 
                 'DS:gas:COUNTER:3600:0:U', 
                 rra(total))

  # create cost db
  updateinterval = 60*60*24
  total = TOTAL / updateinterval
  print '\nCreating cost db at %s' % (path + 'cost.rrd')
  rrdtool.create(path + 'cost.rrd', 
                 '-s', str(updateinterval), 
                 'DS:power:GAUGE:3600:0:U', 
                 'DS:gas:GAUGE:3600:0:U',
                 'RRA:AVERAGE:0.5:86400:1095',
                 'RRA:AVERAGE:0.5:2628000:36',
                 'RRA:AVERAGE:0.5:31536000:3')

  if cmd_args.fill:
    print '\nFilling databases with random data'
    start = long(time.time())
    t = start
    step = 300
    for i in range(0, TOTAL, step):
      rrdtool.update(path + 'power.rrd', '%d:%d:%d' % (t, random.random()*i, i))
      t += step

    t = start
    step = 3600
    counter = 0
    for i in range(0, TOTAL, step):
      counter += random.randint(1, i+1)
      rrdtool.update(path + 'gas.rrd', '%d:%d' % (t, counter))
      t += step

    t = start
    step = 3600*24
    counter = 0
    for i in range(0, TOTAL, step):
      counter += random.randint(1, i+1)
      rrdtool.update(path + 'cost.rrd', '%d:%d:%d' % (t, random.random()-0.5, i*random.random()))
      t += step
