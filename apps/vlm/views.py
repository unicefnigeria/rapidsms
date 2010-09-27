#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseServerError, Http404
from django.template import RequestContext
from django.views.decorators.cache import cache_page
from reporters.models import Location, LocationType, Reporter
from rapidsms.webui.utils import render_to_response
# The import here newly added for serializations

def dashboard(req):
    return render_to_response(req, "vlm/vlm_dashboard.html")
