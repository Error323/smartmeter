#!/usr/bin/python

import os
import time
import random
import rrdtool
import argparse

# RRD database files
RRDPWR = os.path.abspath('data/power.rrd')
RRDGAS = os.path.abspath('data/gas.rrd')
RRDPWRCOST = os.path.abspath('data/power-cost.rrd')
RRDGASCOST = os.path.abspath('data/gas-cost.rrd')

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
  cmd_args = argparser.parse_args()
  path = os.path.abspath("data") + '/'

  # create power db
  updateinterval = 10
  total = TOTAL / updateinterval
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
  updateinterval = 60*60
  total = TOTAL / updateinterval
  print '\nCreating gas rrd-databases at:\n %s\n %s' % (RRDGAS, RRDGASCOST)
  rrdtool.create(RRDGAS, 
                 '-s', str(updateinterval), 
                 'DS:gas:GAUGE:3600:0:U', 
                 rra(total))
  rrdtool.create(RRDGASCOST, 
                 '-s', str(updateinterval), 
                 'DS:cost:GAUGE:3600:0:U', 
                 rra(total))

  if cmd_args.fill:
    print '\nFilling databases with random data'
    start = long(time.time())
    t = start
    step = 300
    for i in range(0, TOTAL, step):
      rrdtool.update(path + 'power.rrd', '%d:%d:%d' % (t, random.random()*i, i))
      t += step

    t = start
    step = 3600/4
    counter = 0
    for i in range(0, TOTAL, step):
      if step % 1800 == 0:
        counter += 1
      rrdtool.update(path + 'gas.rrd', '%d:%d' % (t, counter))
      t += step

    t = start
    step = 3600*24
    counter = 0
    for i in range(0, TOTAL, step):
      counter += random.randint(1, i+1)
      rrdtool.update(path + 'cost.rrd', '%d:%d:%d' % (t, random.random()-0.5, i*random.random()))
      t += step
