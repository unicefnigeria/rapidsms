#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import os
from django.conf.urls.defaults import *
import bednets.views as views

urlpatterns = patterns('',
    url(r'^bednets/?(?P<campaign_id>\d*)/?(?P<state_id>\d*)/?$', views.dashboard),
    url(r'^bednets/data/?(?P<campaign_id>\d*)/?(?P<state_id>\d*)/?$', views.export_data),
)
