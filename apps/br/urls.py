#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
import br.views as views

urlpatterns = patterns('',
    url(r'^br/?(?P<state>\d*)/?(?P<year>\d*)/?(?P<month>\d*)/?$', views.dashboard),
    url(r'^br/monthly/?(?P<state>\d*)/?(?P<year>\d*)/?(?P<month>\d*)/?$', views.monthly_dashboard),
)
