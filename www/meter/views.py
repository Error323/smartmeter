from django.http import HttpResponse
from django.shortcuts import render

import rrdtool
import json

RRDFILE = '/home/fhuizing/Workspace/smartmeter/data/power.rrd'
POINTS = 1000

def index(request):
  return render(request, 'meter/index.html')

def power(request, start=0, end=0):
  if start == 0 or end == 0:
    start = rrdtool.first(RRDFILE)
    end = rrdtool.last(RRDFILE)
  else:
    start = max(int(start)/1000, rrdtool.first(RRDFILE))
    end = min(int(end)/1000, rrdtool.last(RRDFILE))

  resolution = (end - start) / POINTS
  start = int(start/float(resolution)) * resolution
  end = int(end/float(resolution)) * resolution
  
  raw = rrdtool.fetch(RRDFILE, 'AVERAGE', 
                      '-r', str(resolution), 
                      '-s', str(start), 
                      '-e', str(end))
  
  data = []
  time = raw[0][0]
  for i in range(len(raw[2])):
    time += raw[0][2]
    if raw[2][i][0] != None:
      data.append((time*1000, int(round(raw[2][i][0]))))

  return HttpResponse(json.dumps(data))
