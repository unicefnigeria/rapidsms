#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import os
from django.conf.urls.defaults import *
import ipd.views as views

urlpatterns = patterns('',
    url(r'^im/lga/(?P<campaign_id>\d*)/?(?P<locid>\d*)/?$', views.lga_summary),
    url(r'^im/?(?P<campaign_id>\d*)/?(?P<stateid>\d*)/?$', views.dashboard),
    url(r'^im/summary/(?P<locid>\d*)/?$', views.index),
    url(r'^im/compliance/summary/(?P<locid>\d*)/?$', views.compliance_summary),
)
