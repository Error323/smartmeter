import sys
sys.path.append('.') # add root path
from django.http import HttpResponse
from django.shortcuts import render
from createdb import *

import rrdtool
import json
import os

def index(request, name='index'):
  return render(request, 'meter/' + name + '.html')

def power(request, name, start=0, end=0):
  data = rrddata(RRDPWR, start, end, 0)
  return HttpResponse(json.dumps(data))

def gas(request, name, start=0, end=0):
  data = rrddata(RRDGAS, start, end)
  return HttpResponse(json.dumps(data))

def cost(request, name, start=0, end=0):
  data = []
  return HttpResponse(json.dumps(data))

def realtime(request):
  power = float(rrdtool.info(RRDPWR)['ds[usage].last_ds'])
  gas = float(rrdtool.info(RRDGAS)['ds[gas].last_ds'])
  data = {'power': power, 'gas': gas}
  return HttpResponse(json.dumps(data))

def rrddata(name, start, end, dec=3):
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
      data.append((time*1000, round(raw[2][i][0], dec)))
      
  return data
