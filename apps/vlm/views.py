#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseServerError, Http404
from django.template import RequestContext
from django.views.decorators.cache import cache_page
from models import *
from rapidsms.webui.utils import render_to_response
from datetime import datetime, timedelta
# The import here newly added for serializations

def dashboard(req):
    return render_to_response(req, "vlm/vlm_dashboard.html")

# default to Kaduna State
def state_summary(req, state=19, year=0, month=0):
    month_year = datetime.now().year if not year else int(year)
    month_month = datetime.now().month if not month else int(month)

    start_period = datetime(year=month_year, month=month_month, day=1)
    end_period = datetime(year=month_year, month=month_month + 1, day=1) - timedelta(0, 0, 1)
    stock_balances = Stock.objects.filter(facility__code=state)
    return render_to_response(req, "vlm/vlm_state_summary.html", {
        'stock': stock_balances, 'state_id': state, 'month_year': month_year,
        'month_month': month_month
    })
