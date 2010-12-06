#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
import br.views as views

urlpatterns = patterns('',
    url(r'^br/?(?P<campaign_id>\d*)/?(?P<stateid>\d*)/?$', views.dashboard),
)
