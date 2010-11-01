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

@register.inclusion_tag("vlm/partials/logistics.html")
def logistics_summary(campaign_id, state_id):
    all_locations = []
    state = None

    if campaign_id:
        campaign = Campaign.objects.get(id=campaign_id)
    if campaign:
        if not state_id:
            state = campaign.campaign_states()[0]
        else:
            state = Location.objects.get(pk=state_id)

        # retrieve all campaign locations
        all_locations.append(state)

        # fetch all of the LGAs that we want to display
        lgas = campaign.campaign_lgas(state)

    # called to fetch and assemble the data structure
    # for each LGA, containing the flow of stock
    def __lga_data(lga):
        incoming = PartialTransaction.objects.filter(destination=lga, type__in=["R", "I"]).order_by("-date")
        outgoing = PartialTransaction.objects.filter(origin=lga, type__in=["R", "I"]).order_by("-date")
        return {
            "name":         unicode(lga),
            "transactions": incoming | outgoing, 
            "logistician": lga.one_contact('SM', True)}
    
    # process and return data for ALL LGAs for this report
    if campaign and state:
        return { "lgas": map(__lga_data, lgas) }
    else:
        return { "lgas": None }
