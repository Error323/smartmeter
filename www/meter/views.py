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

def cost(request):
  types = {'day':'e-1d','month':'e-1m','year':'e-1y'}
  totals = {'day':0,'month':0,'year':0}
  entries = []
  row = {}

  for k in types:
    row[k] = powercost(types[k])
    if row[k] != None:
      totals[k] += row[k]
    else:
      row[k] = '-'
  row['type'] = 'Power'
  entries.append(row)
  row = {}

  for k in types:
    row[k] = gascost(types[k])
    if row[k] != None:
      totals[k] += row[k]
    else:
      row[k] = '-'
  row['type'] = 'Gas'
  entries.append(row)
  row = {}

  for k in types:
    row[k] = totals[k]
  row['type'] = 'Total'
  entries.append(row)

  return render(request, 'meter/index.html', {'cost_table': entries},
          content_type="application/xhtml+xml")

def realtime(request):
  end = rrdtool.last(RRDPWR)
  raw = rrdtool.fetch(RRDPWR, 'AVERAGE', 
                      '-r', '1800',
                      '-s', 'e-1d', 
                      '-e', str(end))
  
  data = {'power':[], 'gas':[]}
  time = raw[0][0]
  for i in range(len(raw[2])):
    time += raw[0][2]
    if raw[2][i][0] == None:
      data['power'].append((time*1000, None))
    else:
      data['power'].append((time*1000, round(raw[2][i][0])))

  end = rrdtool.last(RRDGAS)
  raw = rrdtool.fetch(RRDGAS, 'AVERAGE', 
                      '-s', 'e-1d', 
                      '-e', str(end))
  
  time = raw[0][0]
  for i in range(len(raw[2])):
    time += raw[0][2]
    if raw[2][i][0] == None:
      data['gas'].append((time*1000, None))
    else:
      data['gas'].append((time*1000, round(raw[2][i][0], 3)))

  return HttpResponse(json.dumps(data))
  

def last(request):
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

def gascost(start):
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
    return None

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
  return round(cost, 2)

def powercost(start):
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
    return None

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
  return round(cost, 2)
