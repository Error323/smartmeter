from django.shortcuts import render
import datetime

class Data:
  def __init__(self):
    self.gasinterval = 24*3600*1000
    self.gasstart = 1388494750
    self.gasdata = [10, 3, 2, 6, 3, 7, 9, 0, 3, 5, 8, 1]
    self.powerinterval = 24*3600*1000
    self.powerstart = 1388494750
    self.powerdata = [7, 3, 2, 6, 3, 9, 9, 0, 3, 5, 8, 1]

def index(request):
  data = Data()
  return render(request, 'meter/index.html', {'data': data})
