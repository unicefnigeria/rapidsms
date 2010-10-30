#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django import template
register = template.Library()
from locations.models import *
from datetime import datetime

all_months = {1:'January', 2:'February', 3:'March', 4:'April', 
    5:'May', 6:'June', 7:'July', 8:'August', 9:'September', 
    10:'October', 11:'November', 12:'December'}

@register.inclusion_tag("vlm/partials/states_list.html")
def states(baseurl, state_id=0):
    states = []
    # we want to ignore national and regional stores
    state_facilities = Facility.objects.filter(location__type__name="STATE").exclude(code__startswith='n').exclude(code__startswith='s')
    for state in state_facilities:
        states.append({'name': "%s" % (state.name), \
            'code': state.code, 'selected': 1 if (state_id == state.code) else 0 })
    return { "states": states, "baseurl": baseurl }

@register.inclusion_tag("vlm/partials/months_list.html")
def months(baseurl, state_id=0, year=0, month=0):
    months = []
    current_year = datetime.now().year
    for mth in range(1, 13):
        months.append({'name': "%s, %d" % (all_months[mth], current_year), \
            'year': current_year, 'month': mth,
            'selected': 1 if (int(month) == mth) else 0 })
    return { "months": months, "month_baseurl": baseurl, 'month_state_id': state_id }
