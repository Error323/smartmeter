from django.conf.urls import patterns, url

from meter import views

urlpatterns = patterns('',
  url(r'^power/$', views.index, name='index'),
  url(r'^power/data/$', views.power, name='power'),
  url(r'^power/data/(?P<start>\d+)/(?P<end>\d+)/$', views.power, name='power')
)
