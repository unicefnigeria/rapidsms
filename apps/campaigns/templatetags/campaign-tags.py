#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django import template
register = template.Library()
from campaigns.models import *

@register.inclusion_tag("campaigns/partials/campaign_list.html")
def campaigns(baseurl, campaign_id=1, state_id=0):
    ''' Obtains a list of all the campaign data and renders a widget (drop down menu) with all the campaigns.
        The campaign and state may optionally be selected if specified.
        A baseurl is also required so the templatetag can be used in other apps. The url format is that of
        baseurl/campaign_id/state_id'''
    list_o_campaigns = Campaign.objects.all()
    campaigns = []
    campaign_id = int(campaign_id)
    state_id = int(state_id)
    for campaign in list_o_campaigns:
        for state in campaign.campaign_states():
            campaigns.append({'name': "%s (%s)" % (campaign, state), \
                'campaign_id': campaign.id, 'state_id': state.id, 'selected': 1 if (campaign_id == campaign.id and state_id == state.id) else 0 })
    return { "campaigns": campaigns, "baseurl": baseurl }
