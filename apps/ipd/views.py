#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseServerError, Http404
from django.template import RequestContext
from reporters.models import Location, LocationType, Reporter
from ipd.models import NonCompliance, Shortage, Report
from campaigns.models import Campaign
from rapidsms.webui.utils import render_to_response
from django.db import models
# The import here newly added for serializations
from django.core import serializers
from random import randrange, seed
from django.utils import simplejson

import time
import sys
import datetime

#Parameter for paging reports outputs
ITEMS_PER_PAGE = 20

#This is required for ***unicode*** characters***
# do we really need to reload it?  TIM to check
reload(sys)
sys.setdefaultencoding('utf-8')

#Views for handling summary of Reports Displayed as Location Tree
#@permission_required('ipd.can_view')
def dashboard(req, campaign_id=None, stateid=None):
    campaign = None
    all_locations = []
    vaccinations = []
    cases = []
    shortages = []
    reporters = []
    no_of_vaccinations = 0
    no_of_cases = 0
    no_of_shortages = 0
    no_of_reporters = 0
    active_locations = 0
    lga_vaccination_summary_data = {}
    lga_noncompliance_summary_data = {}
    commodities = []
    reasons = []
    
    # Obtain campaign data per day
    campaign_vaccinations = []
    campaign_cases = {}


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
        vaccinations = campaign.cro(Report, state, all_locations)
        cases = campaign.cro(NonCompliance, state, all_locations)
        shortages = campaign.cro(Shortage, state, all_locations)
        reporters = Reporter.objects.filter(location__in=all_locations)
        no_of_vaccinations = vaccinations.count()
        no_of_cases = cases.count()
        no_of_shortages = shortages.count()
        no_of_reporters = reporters.count()
        active_locations = vaccinations.values("location").distinct().count()

        # Retrieve vaccination commodities to determine which table columns to display in the
        # report
        commodities = vaccinations.values_list('commodity', flat=True).distinct()

        # mapping functions for non-compliance case values
        reason_map = {'0':"", '1':"OPV", '2':"CS", '3':"RB", '4':"NFN", '5':"PD", '6':"NCG", '7':"IP", '8':"TMR", '9':"RNG"}

        # retrieves data for the non-compliance table
        reasons = map(lambda x: reason_map[x], cases.values_list('reason', flat=True).distinct())
        try:
            reasons.remove("")
        except ValueError:
            pass

        # initialize campaign data per day
        # we do not want to display all the days of the campaign if we the campaign
        # is still ongoing so we find the extent to which we've gone in the campaign
        campaign_end_date = datetime.date.today() if (datetime.date.today() < campaign.end_date) else campaign.end_date

        for day_delta in range((campaign_end_date - campaign.start_date).days):
            date = campaign.start_date + datetime.timedelta(day_delta)
            args = { 'time__year': date.year, 'time__month': date.month, 'time__day': date.day }

            data = {
                "date": date,
                "total": sum(vaccinations.filter(**args).values_list('immunized', flat=True)),
            }

            for commodity in commodities:
                args['commodity'] = commodity
                data.update({ commodity: sum(vaccinations.filter(**args).values_list('immunized', flat=True))})

            campaign_vaccinations.append(data)


        lga_vaccination_summary_data = {}

        for lga in campaign.campaign_lgas(state):
            lga_vaccination_summary_data[lga.name] = {}
            lga_vaccination_summary_data[lga.name]['name'] = lga.name
            lga_vaccination_summary_data[lga.name]['data'] = {}
            lga_totals = {}

            for ward in lga.get_children():
                lga_vaccination_summary_data[lga.name]['data'][ward.name] = {}
                lga_vaccination_summary_data[lga.name]['data'][ward.name]['name'] = ward.name
                lga_vaccination_summary_data[lga.name]['data'][ward.name]['data'] = {}

                ward_totals = {}
                
                ward_locations = [ward]
                ward_locations.extend(ward.get_descendants())
                
                ward_reports = vaccinations.filter(location__in=ward_locations,time__range=(campaign.start_date, campaign.end_date)).values('commodity','immunized')
                for ward_report in ward_reports:
                    ward_totals['total'] = ward_totals['total'] + ward_report['immunized'] if ward_totals.has_key('total') else ward_report['immunized']
                    lga_totals['total'] = lga_totals['total'] + ward_report['immunized'] if lga_totals.has_key('total') else ward_report['immunized']
                    ward_totals[ward_report['commodity']] = ward_totals[ward_report['commodity']] + ward_report['immunized'] if ward_totals.has_key(ward_report['commodity']) else ward_report['immunized']
                    lga_totals[ward_report['commodity']] = lga_totals[ward_report['commodity']] + ward_report['immunized'] if lga_totals.has_key(ward_report['commodity']) else ward_report['immunized']

                # ensure that every commodity has a value
                for commodity in commodities:
                    if not ward_totals.has_key(commodity):
                        ward_totals[commodity] = 0

                lga_vaccination_summary_data[lga.name]['data'][ward.name]['data'] = ward_totals

            lga_vaccination_summary_data[lga.name]['total'] = lga_totals
            lga_vaccination_summary_data[lga.name]['reporters'] = Reporter.objects.filter(location__in=lga.get_descendants()).count()

        lga_noncompliance_summary_data = {}

        for lga in campaign.campaign_lgas(state):
            lga_noncompliance_summary_data[lga.name] = {}
            lga_noncompliance_summary_data[lga.name]['name'] = lga.name
            lga_noncompliance_summary_data[lga.name]['data'] = {}
            lga_totals = {}

            for ward in lga.get_children():
                lga_noncompliance_summary_data[lga.name]['data'][ward.name] = {}
                lga_noncompliance_summary_data[lga.name]['data'][ward.name]['name'] = ward.name
                lga_noncompliance_summary_data[lga.name]['data'][ward.name]['data'] = {}

                ward_totals = {}
                
                ward_locations = [ward]
                ward_locations.extend(ward.get_descendants())
                
                ward_reports = cases.filter(location__in=ward_locations,time__range=(campaign.start_date, campaign.end_date)).values('cases','reason')
                for ward_report in ward_reports:
                    ward_totals['total'] = ward_totals['total'] + ward_report['cases'] if ward_totals.has_key('total') else ward_report['cases']
                    lga_totals['total'] = lga_totals['total'] + ward_report['cases'] if lga_totals.has_key('total') else ward_report['cases']
                    ward_totals[reason_map[ward_report['reason']]] = ward_totals[reason_map[ward_report['reason']]] + ward_report['cases'] if ward_totals.has_key(reason_map[ward_report['reason']]) else ward_report['cases']
                    lga_totals[reason_map[ward_report['reason']]] = lga_totals[reason_map[ward_report['reason']]] + ward_report['cases'] if lga_totals.has_key(reason_map[ward_report['reason']]) else ward_report['cases']

                # ensure that every reason has a value
                for reason in reasons:
                    if not ward_totals.has_key(reason):
                        ward_totals[reason] = 0

                lga_noncompliance_summary_data[lga.name]['data'][ward.name]['data'] = ward_totals

            lga_noncompliance_summary_data[lga.name]['total'] = lga_totals
            lga_noncompliance_summary_data[lga.name]['reporters'] = Reporter.objects.filter(location__in=lga.get_descendants()).count()


    else:
        pass
    return render_to_response(req, "ipd/ipd_dashboard.html", 
        {
        'no_of_vaccinations': no_of_vaccinations,
        'no_of_cases': no_of_cases,
        'lga_vaccination_summary': lga_vaccination_summary_data,
        'lga_noncompliance_summary': lga_noncompliance_summary_data,
        'no_of_shortages': no_of_shortages,
        'reasons': reasons,
        'campaign_vaccinations': campaign_vaccinations,
        'campaign_cases': campaign_cases,
        'commodities': commodities,
        'no_of_reporters': no_of_reporters,
        'active_locations': active_locations,
        'campaign_id': campaign_id,
        'state_id': stateid,
        })

@permission_required('ipd.can_view')
def lga_summary(req, campaign_id=None, locid=None):
    return render_to_response(req, 'ipd/lga_summary.html')

@permission_required('ipd.can_view')
def index(req, locid=None):
    if not locid:
        locid = 1
    try:
        location = Location.objects.get(id=locid)
        location.non_compliance_total  =  NonCompliance.non_compliance_total(location)
    except Location.DoesNotExist:
        pass
    return render_to_response(req,"ipd/index.html", {'location':location})

@permission_required('ipd.can_view')
def compliance_summary(req, locid=1):
    bar_data=[]
    expected_data=[]
    nets_data=[]
    discrepancy_data = []
    labels=[]
    loc_children=[]
    time_data=[]
    type = ""
    index = 0
    pie_data=[]
    parent=None
    location=None
    NC_REASONS = (
             ('1', 'OPV Safety'),
             ('2', 'Child Sick'),
             ('3', 'Religious Belief'),
             ('4', 'No Felt Need'),
             ('5', 'Political Differences'),
             ('6', 'No Care Giver Consent'),
             ('7', 'Unhappy With Immunization Personnel'),
             ('8', 'Too Many Rounds'),
             ('9', 'Reason Not Given'),
     )

    try:
        location = Location.objects.get(id=locid)
        parent = location.parent
        location_type = Location.objects.get(pk=locid).type
        loc_children = []
        for reason in NC_REASONS:
            
            pie_data.append({"label": reason, "data":NonCompliance.get_reason_total(reason, location)})
            print pie_data

    except:
        pass
    
    return render_to_response(req,"ipd/compliance_summary.html", {'pie_data':pie_data, 'location':location})

def generate(req):
   pass 

def immunization_summary(req, frm, to, range):
    pass

def shortage_summary(req, locid=1):
    pass
