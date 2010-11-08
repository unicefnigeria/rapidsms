#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django import template
register = template.Library()
from locations.models import *
from datetime import datetime

all_months = {1:'January', 2:'February', 3:'March', 4:'April', 
    5:'May', 6:'June', 7:'July', 8:'August', 9:'September', 
    10:'October', 11:'November', 12:'December'}

@register.inclusion_tag("vlm/partials/zones_list.html")
def zones(baseurl, zone_id=0):
    zones = []
    zone_stores = Facility.objects.filter(location__type__name="ZONE")
    for zone in zone_stores:
        zones.append({'name': "%s" % (zone.name), \
            'code': zone.code, 'selected': 1 if (zone_id == zone.code) else 0 })
    return { "zones": zones, "baseurl": baseurl }

@register.inclusion_tag("vlm/partials/states_list.html")
def states(baseurl, zone_id="", state_id=""):
    states = []
    if zone_id:
        zone_states = Location.objects.get(code=zone_id).children.all()
        state_facilities = Facility.objects.filter(location__in=zone_states)
        for state in state_facilities:
            states.append({'name': "%s" % (state.name), \
                'code': state.code, 'selected': 1 if (state_id == state.code) else 0 })
    return { "states": states, "baseurl": baseurl, "zone_id": zone_id }

@register.inclusion_tag("vlm/partials/months_list.html")
def months(baseurl, zone_id="", state_id="", year=0, month=0):
    months = []
    end_year = datetime.now().year
    start_year = 2009 # date displays start from 2010 up until the current year
    for yr in range(end_year, start_year, -1):
        for mth in range(12, 0, -1):
            months.append({'name': "%s, %d" % (all_months[mth], yr), \
                'year': year, 'month': mth,
                'selected': 1 if (int(month) == mth and int(year) == yr) else 0 })
    return { "months": months, "month_baseurl": baseurl, 'month_state_id': state_id, "month_zone_id": zone_id }

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
