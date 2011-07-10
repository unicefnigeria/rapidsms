#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.views.decorators.cache import cache_page
from reporters.models import Location, Reporter
from models import BirthRegistration
from django.db.models import Max
from rapidsms.webui.utils import render_to_response
from datetime import datetime
import csv
from django.http import HttpResponse
# The import here newly added for serializations

import sys

#This is required for ***unicode*** characters***
# do we really need to reload it?  TIM to check
reload(sys)
sys.setdefaultencoding('utf-8')

#Views for handling summary of Reports Displayed as Location Tree
@cache_page(60 * 15)
def dashboard(req, prefix="", state="", year=0, month=0):
    month_year = datetime.now().year if not year else int(year)
    month_month = datetime.now().month if not month else int(month)
    state = state if state else "19"

    start_period = datetime(year=month_year, month=month_month, day=1) if prefix == 'monthly' else datetime(year=2010, month=1, day=1)
    end_period = datetime(year=month_year, month=month_month + 1 if month_month < 12 else 12, day=1)
    location_state = Location.objects.get(code=state)

    birthregistrations = None
    birthregistration_data = []
    boys_below1 = 0
    boys_1to4 = 0
    boys_5to9 = 0
    boys_10to18 = 0
    girls_below1 = 0
    girls_1to4 = 0
    girls_5to9 = 0
    girls_10to18 = 0
    
    rcs = Location.objects.filter(parent__parent=location_state,type__name="RC")

    birthregistrations = BirthRegistration.objects.filter(location__in=rcs, time__gte=start_period, time__lt=end_period).annotate(time=Max('time'))

    boys_below1 = sum(birthregistrations.values_list('boys_below1', flat=True))
    boys_1to4 = sum(birthregistrations.values_list('boys_1to4', flat=True))
    boys_5to9 = sum(birthregistrations.values_list('boys_5to9', flat=True))
    boys_10to18 = sum(birthregistrations.values_list('boys_10to18', flat=True))
    girls_below1 = sum(birthregistrations.values_list('girls_below1', flat=True))
    girls_1to4 = sum(birthregistrations.values_list('girls_1to4', flat=True))
    girls_5to9 = sum(birthregistrations.values_list('girls_5to9', flat=True))
    girls_10to18 = sum(birthregistrations.values_list('girls_10to18', flat=True))

    lgas = list(set([ rc.parent for rc in rcs ]))

    for lga in lgas:
        L = {'name': lga.name, 'boys_below1':0, 'boys_1to4':0, 'boys_5to9':0, 'boys_10to18':0, 'total_boys': 0, 'girls_below1':0, 'girls_1to4':0, 'girls_5to9':0, 'girls_10to18':0, 'total_girls':0, 'data': []}
        rcs = Location.objects.filter(parent=lga,type__name="RC")

        for rc in rcs:
            rc_data = {'name': rc.name, 'girls_below1':0, 'girls_1to4':0, 'girls_5to9':0, 'girls_10to18':0, 'total_girls':0, 'boys_below1':0, 'boys_1to4':0, 'boys_5to9':0, 'boys_10to18':0, 'total_boys':0}

            rc_reports = birthregistrations.filter(location__code__startswith=rc.code,time__range=(start_period, end_period)).values('girls_below1', 'girls_1to4', 'girls_5to9', 'girls_10to18', 'boys_below1', 'boys_1to4', 'boys_5to9', 'boys_10to18')

            for rc_report in rc_reports:
                rc_data['boys_below1'] += rc_report['boys_below1'] 
                rc_data['boys_1to4'] += rc_report['boys_1to4'] 
                rc_data['boys_5to9'] += rc_report['boys_5to9'] 
                rc_data['boys_10to18'] += rc_report['boys_10to18'] 
                rc_data['girls_below1'] += rc_report['girls_below1'] 
                rc_data['girls_1to4'] += rc_report['girls_1to4'] 
                rc_data['girls_5to9'] += rc_report['girls_5to9'] 
                rc_data['girls_10to18'] += rc_report['girls_10to18'] 

                L['girls_below1'] += rc_report['girls_below1'] 
                L['girls_1to4'] += rc_report['girls_1to4'] 
                L['girls_5to9'] += rc_report['girls_5to9'] 
                L['girls_10to18'] += rc_report['girls_10to18'] 
                L['boys_below1'] += rc_report['boys_below1'] 
                L['boys_1to4'] += rc_report['boys_1to4'] 
                L['boys_5to9'] += rc_report['boys_5to9'] 
                L['boys_10to18'] += rc_report['boys_10to18'] 
            
            rc_data['total_girls'] = rc_data['girls_below1'] + rc_data['girls_1to4'] + rc_data['girls_5to9'] + rc_data['girls_10to18']
            rc_data['total_boys'] = rc_data['boys_below1'] + rc_data['boys_1to4'] + rc_data['boys_5to9'] + rc_data['boys_10to18']
            
            L['data'].append(rc_data)
            
        L['reporters'] = Reporter.objects.filter(location__code__startswith=lga.code, role__code='BR').count()
        L['total_girls'] = L['girls_below1'] + L['girls_1to4'] + L['girls_5to9'] + L['girls_10to18']
        L['total_boys'] = L['boys_below1'] + L['boys_1to4'] + L['boys_5to9'] + L['boys_10to18']
        
        birthregistration_data.append(L)

    return render_to_response(req, "br/br_dashboard.html", 
        {
        'prefix': '/br/monthly' if prefix == 'monthly' else '/br',
        'birthregistration_data': birthregistration_data,
        'boys_below1': boys_below1,
        'boys_1to4': boys_1to4,
        'boys_5to9': boys_5to9,
        'boys_10to18': boys_10to18,
        'girls_below1': girls_below1,
        'girls_1to4': girls_1to4,
        'girls_5to9': girls_5to9,
        'girls_10to18': girls_10to18,
        'state': location_state,
        'month_month': month_month,
        'month_year': month_year,
        })

#Views for handling summary of Reports Displayed as Location Tree
@cache_page(60 * 15)
def csv_download(req, prefix="", state="", year=0, month=0):
    month_year = datetime.now().year if not year else int(year)
    month_month = datetime.now().month if not month else int(month)
    state = state if state else "19"

    # The start period should be the specified month for monthly data or Jan. 2010 for cummulative
    start_period = datetime(year=month_year, month=month_month, day=1) if prefix == 'monthly' else datetime(year=2010, month=1, day=1)
    end_period = datetime(year=month_year, month=month_month + 1 if month_month < 12 else 12, day=1)
    location_state = Location.objects.get(code=state)
    rcs = Location.objects.filter(parent__parent=location_state,type__name="RC")

    birthregistrations = BirthRegistration.objects.filter(location__in=rcs, time__gte=start_period, time__lt=end_period).order('-time')

    response = HttpResponse(mimetype="text/csv")
    response['Content-Disposition'] = 'attachment; filename=birthregistration_records_%s_%s_%d%.2d.csv' % ('monthly' if prefix == 'monthly' else 'cummulative', location_state.name.lower(), month_year, month_month)
    writer = csv.writer(response)
    
    header = ["Time", "Reporter", "Location", "Girls < 1", "Girls 1-4", "Girls 5-9", "Girls 10-18", "Boys < 1", "Boys 1-4", "Boys 5-9", "Boys 10-18"]
    writer.writerow(header)
    
    for record in birthregistrations:
        writer.writerow([ \
            record.time,
            "%s (%s)" % (record.reporter, record.reporter.connection().identity),
            record.location,
            record.girls_below1,
            record.girls_1to4,
            record.girls_5to9,
            record.girls_10to18,
            record.boys_below1,
            record.boys_1to4,
            record.boys_5to9,
            record.boys_10to18
        ])
    
    return response