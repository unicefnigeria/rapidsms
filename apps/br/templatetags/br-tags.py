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
def states(baseurl, state_id=""):
    states = []
    location_states = Location.objects.filter(type__name="State")
    for state in location_states:
        states.append({'name': "%s" % (state.name), \
            'code': state.code, 'selected': 1 if (state_id == state.code) else 0 })
    return { "states": states, "baseurl": baseurl }

@register.inclusion_tag("vlm/partials/months_list.html")
def months(baseurl, state_id="", year=0, month=0):
    months = []
    end_year = datetime.now().year
    start_year = 2010 # date displays start from 2010 up until the current year
    for yr in range(end_year, start_year, -1):
        for mth in range(1, 13):
            months.append({'name': "%s, %d" % (all_months[mth], yr), \
                'year': year, 'month': mth,
                'selected': 1 if (int(month) == mth and int(year) == yr) else 0 })
    return { "months": months, "month_baseurl": baseurl, 'month_state_id': state_id }

