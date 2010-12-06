#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.views.decorators.cache import cache_page
from reporters.models import Location, Reporter
from models import BirthRegistration
from campaigns.models import Campaign
from rapidsms.webui.utils import render_to_response
# The import here newly added for serializations

import sys

#This is required for ***unicode*** characters***
# do we really need to reload it?  TIM to check
reload(sys)
sys.setdefaultencoding('utf-8')

#Views for handling summary of Reports Displayed as Location Tree
@cache_page(60 * 15)
def dashboard(req, campaign_id=None, stateid=None):
    campaign = None
    all_locations = []
    birthregistrations = None
    birthregistration_data = []
    boys_under5 = 0
    boys_over5 = 0
    girls_under5 = 0
    girls_over5 = 0
    
    if campaign_id:
        campaign = Campaign.objects.get(id=campaign_id)
    if campaign:
        if not stateid:
            stateid = campaign.campaign_states()[0]
        state = Location.objects.get(pk=stateid)
        all_locations.append(state)
        for lga in campaign.campaign_lgas(state):
            all_locations.append(lga)
            for desc in lga.get_descendants():
                all_locations.append(desc)
        birthregistrations = campaign.cro(BirthRegistration, state, all_locations)
        boys_under5 = sum(birthregistrations.values_list('boys_under5', flat=True))
        boys_over5 = sum(birthregistrations.values_list('boys_over5', flat=True))
        girls_under5 = sum(birthregistrations.values_list('girls_under5', flat=True))
        girls_over5 = sum(birthregistrations.values_list('girls_over5', flat=True))

        for lga in campaign.campaign_lgas(state):
            L = {'name': lga.name, 'girls_under5':0, 'girls_over5':0, 'boys_under5':0, 'boys_over5':0, 'data': []}

            for ward in lga.get_children():
                ward_data = {'name': ward.name, 'girls_under5':0, 'girls_over5':0, 'boys_under5':0, 'boys_over5':0}

                ward_reports = birthregistrations.filter(location__code__startswith=ward.code,time__range=(campaign.start_date, campaign.end_date)).values('boys_under5','boys_over5', 'girls_under5', 'girls_over5')

                for ward_report in ward_reports:
                    ward_data['girls_under5'] += ward_report['girls_under5'] 
                    ward_data['girls_over5'] += ward_report['girls_over5']
                    ward_data['boys_under5'] += ward_report['boys_under5'] 
                    ward_data['boys_over5'] += ward_report['boys_over5'] 

                    L['girls_under5'] += ward_report['girls_under5'] 
                    L['girls_over5'] += ward_report['girls_over5']
                    L['boys_under5'] += ward_report['boys_under5'] 
                    L['boys_over5'] += ward_report['boys_over5'] 
                
                L['data'].append(ward_data)
            L['reporters'] = Reporter.objects.filter(location__code__startswith=lga.code).count()

            birthregistration_data.append(L)

    else:
        pass

    return render_to_response(req, "br/br_dashboard.html", 
        {
        'birthregistration_data': birthregistration_data,
        'boys_under5': boys_under5,
        'boys_over5': boys_over5,
        'girls_under5': girls_under5,
        'girls_over5': girls_over5,
        'campaign_id': campaign_id,
        'state_id': stateid,
        })

