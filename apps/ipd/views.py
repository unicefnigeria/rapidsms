#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseServerError, Http404
from django.template import RequestContext
from django.views.decorators.cache import cache_page
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
@cache_page(60 * 15)
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
    lga_vaccination_summary_data = []
    lga_noncompliance_summary_data = []
    commodities = []
    reasons = []
    
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
        no_of_vaccinations = sum(vaccinations.values_list('immunized', flat=True))
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

        for lga in campaign.campaign_lgas(state):
            L = {}
            L2 = {}
            
            L['name'] = lga.name
            L2['name'] = lga.name
            L['data'] = []
            L2['data'] = []
            
            lga_totals = {}
            lga_totals_nc = {}
            
            for ward in lga.get_children():
                ward_data_im = {}
                ward_data_nc = {}
                ward_data_im['name'] = ward.name
                ward_data_nc['name'] = ward.name

                ward_totals = {}
                ward_totals_nc = {}
                
                ward_reports = vaccinations.filter(location__code__startswith=ward.code,time__range=(campaign.start_date, campaign.end_date)).values('commodity','immunized')
                for ward_report in ward_reports:
                    ward_totals['total'] = ward_totals['total'] + int(ward_report['immunized']) if ward_totals.has_key('total') else int(ward_report['immunized'])
                    lga_totals['total'] = lga_totals['total'] + int(ward_report['immunized']) if lga_totals.has_key('total') else int(ward_report['immunized'])
                    ward_totals[ward_report['commodity']] = ward_totals[ward_report['commodity']] + int(ward_report['immunized']) if ward_totals.has_key(ward_report['commodity']) else int(ward_report['immunized'])
                    lga_totals[ward_report['commodity']] = lga_totals[ward_report['commodity']] + int(ward_report['immunized']) if lga_totals.has_key(ward_report['commodity']) else int(ward_report['immunized'])

                # ensure that every commodity has a value
                for commodity in commodities:
                    if not ward_totals.has_key(commodity):
                        ward_totals[commodity] = 0

                ward_reports_nc = cases.filter(location__code__startswith=ward.code,time__range=(campaign.start_date, campaign.end_date)).values('cases','reason')
                for ward_report in ward_reports_nc:
                    ward_totals_nc['total'] = ward_totals_nc['total'] + int(ward_report['cases']) if ward_totals_nc.has_key('total') else int(ward_report['cases'])
                    lga_totals_nc['total'] = lga_totals_nc['total'] + int(ward_report['cases']) if lga_totals_nc.has_key('total') else int(ward_report['cases'])
                    ward_totals_nc[reason_map[ward_report['reason']]] = ward_totals_nc[reason_map[ward_report['reason']]] + int(ward_report['cases']) if ward_totals_nc.has_key(reason_map[ward_report['reason']]) else int(ward_report['cases'])
                    lga_totals_nc[reason_map[ward_report['reason']]] = lga_totals_nc[reason_map[ward_report['reason']]] + int(ward_report['cases']) if lga_totals_nc.has_key(reason_map[ward_report['reason']]) else int(ward_report['cases'])
                
                # ensure that every reason has a value
                for reason in reasons:
                    if not ward_totals_nc.has_key(reason):
                        ward_totals_nc[reason] = 0

                ward_data_im['data'] = ward_totals
                L['data'].append(ward_data_im)
                ward_data_nc['data'] = ward_totals_nc
                L2['data'].append(ward_data_nc)

            L['total'] = lga_totals
            L2['total'] = lga_totals_nc

            L['reporters'] = L2['reporters'] = Reporter.objects.filter(location__code__startswith=lga.code).count()
            lga_vaccination_summary_data.append(L)
            lga_noncompliance_summary_data.append(L2)

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
