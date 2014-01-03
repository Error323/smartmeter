from django.http import HttpResponse
from django.shortcuts import render

import rrdtool
import json
import os

RRDPWR = os.path.abspath('data/power.rrd')
RRDGAS = os.path.abspath('data/gas.rrd')
RRDCST = os.path.abspath('data/cost.rrd')
POINTS = 1000

def index(request, name):
  return render(request, 'meter/' + name + '.html')

def power(request, name, start=0, end=0):
  data = rrddata(RRDPWR, start, end)
  return HttpResponse(json.dumps(data))

def gas(request, name, start=0, end=0):
  data = rrddata(RRDGAS, start, end)
  return HttpResponse(json.dumps(data))

def cost(request, name, start=0, end=0):
  data = rrddata(RRDCST, start, end)
  return HttpResponse(json.dumps(data))

def rrddata(name, start, end):
  if start == 0 or end == 0:
    end = rrdtool.last(name)
    start = rrdtool.first(name)
  else:
    start = max(long(start)/1000, rrdtool.first(name))
    end = min(long(end)/1000, rrdtool.last(name))

  resolution = (end - start) / POINTS
  raw = rrdtool.fetch(name, 'AVERAGE', 
                      '-r', str(resolution), 
                      '-s', str(start), 
                      '-e', str(end))
  
  data = []
  time = raw[0][0]
  for i in range(len(raw[2])):
    time += raw[0][2]
    if raw[2][i][0] == None:
      data.append((time*1000, None))
    else:
      data.append((time*1000, int(round(raw[2][i][0]))))
      
  return data
