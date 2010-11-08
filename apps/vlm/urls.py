#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
import views

urlpatterns = patterns('',
    url(r'^vlm/?$', views.dashboard),
    url(r'^vlm/(?P<zone>[a-zA-Z0-9]+)/?(?P<state>\d*)/?(?P<year>\d*)/?(?P<month>\d*)/?', views.location_summary),
)
