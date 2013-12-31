from django.conf.urls import patterns, url

from meter import views

urlpatterns = patterns('',
  url(r'^$', views.index, name='index')
)
