from django.conf.urls import patterns, url

from meter import views

urlpatterns = patterns('',
  url(r'^(?P<name>power)/$', views.index, name='index'),
  url(r'^(?P<name>power)/data/$', views.power, name='power'),
  url(r'^(?P<name>power)/data/(?P<start>\d+)/(?P<end>\d+)/$', views.power, name='power'),
  url(r'^(?P<name>gas)/$', views.index, name='index'),
  url(r'^(?P<name>gas)/data/$', views.gas, name='gas'),
  url(r'^(?P<name>gas)/data/(?P<start>\d+)/(?P<end>\d+)/$', views.gas, name='gas'),
  url(r'^(?P<name>cost)/$', views.index, name='index'),
  url(r'^(?P<name>cost)/data/$', views.cost, name='cost'),
  url(r'^(?P<name>cost)/data/(?P<start>\d+)/(?P<end>\d+)/$', views.cost, name='cost')
)
