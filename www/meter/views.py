import sys
import os
from django.http import HttpResponse
from django.shortcuts import render

DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(DIR + '/../../') # add root path
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

def gascost(request, start):
  char = start[-1]
  if (char == 'y'):
    res = 32*3600
    mul = int(start[-2])*24*365
  elif (char == 'm'):
    res = 16*3600
    mul = int(start[-2])*24*365/12
  elif (char == 'd'):
    res = 4*3600
    mul = int(start[-2])*24
  else:
    return HttpResponseNotFound('<h1>Page not found</h1>')

  end = rrdtool.last(RRDGASCOST)
  end = str(int(end/float(res))*res)
  raw = rrdtool.fetch(RRDGASCOST, 'AVERAGE', '-r', str(res), '-s', str(start), '-e', end)

  cost = 0.0
  N = 0
  for i in range(len(raw[2])):
    if (raw[2][i][0] != None):
      cost += raw[2][i][0]
      N += 1
  if N != 0:
    cost /= N
  cost *= mul
  return HttpResponse(json.dumps(cost))

def powercost(request, start):
  char = start[-1]
  if (char == 'y'):
    res = 16384*10
    mul = int(start[-2])*360*24*365
  elif (char == 'm'):
    res = 8192*10
    mul = int(start[-2])*360*24*365/12
  elif (char == 'd'):
    res = 1024*10
    mul = int(start[-2])*360*24
  else:
    return HttpResponseNotFound('<h1>Page not found</h1>')

  end = rrdtool.last(RRDPWRCOST)
  end = str(int(end/float(res))*res)
  raw = rrdtool.fetch(RRDPWRCOST, 'AVERAGE', '-r', str(res), '-s', str(start), '-e', end)

  cost = 0.0
  N = 0
  for i in range(len(raw[2])):
    if (raw[2][i][0] != None):
      cost += raw[2][i][0]
      N += 1
  if N != 0:
    cost /= N
  cost *= mul
  return HttpResponse(json.dumps(cost))

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
