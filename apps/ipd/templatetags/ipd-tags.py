#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django import template

register = template.Library()

from datetime import datetime, timedelta
from reporters.models import *
from locations.models import *
from ipd.models import *

population_target = 19040.0

@register.inclusion_tag("ipd/partials/stats.html")
def ipd_stats():
    
    return { "stats": [
        {
            "caption": "Reporters",
            "value":   Reporter.objects.count()
        },
        {
            "caption": "Active Locations",
            "value": Report.objects.values("location").distinct().count()
        },
        {
            "caption": "Immunization Reports",
            "value":   Report.objects.count()
        },
        {
            "caption": "Reported Shortages",
            "value":   Shortage.objects.count()
        },
        {
            "caption": "Total Immunized",
            "value":   sum(Report.objects.values_list("immunized", flat=True))
        },
        {
            "caption": "Total Missed",
            "value":   int((population_target - sum(Report.objects.values_list("immunized", flat=True))))
			#sum(Report.objects.filter(**args).values_list("immunized", flat=True))
        },
        {
            "caption": "Active Responders",
            "value":   len(Reporter.objects.filter(location__type=LocationType.objects.get(name__startswith="LGA")))
        },
    ]}


@register.inclusion_tag("ipd/partials/progress.html")
def daily_progress():
    start = datetime(2009, 12, 01)
    end = datetime(2009, 12, 15)
    days = []
    
    
    # how high should we aim?
    # 48 wards * 9 mobilization teams = 482?
    # but at least 2 lgas are summing teams
    # and reporting once by ward, so maybe 48 * 4?
    report_target    = 192.0

    # Dawakin Kudu      99,379
    # Garum Mallam      51,365
    # Kano Municipal    161,168
    # Kura              63,758
    coupon_target    = 375670.0

    # Dawakin Kudu      248,447
    # Garun Mallam      128,412
    # Kano Municipal    402,919
    # Kura              159,394
    recipient_target = 939172.0
    
    
    for d in range(0, (end - start).days):
        date = start + timedelta(d)
        
        args = {
            "time__year":  date.year,
            "time__month": date.month,
            "time__day":   date.day
        }
        
        data = {
            "number": d+1,
            "date": date,
            "in_future": date > datetime.now()
        }
        
        if not data["in_future"]:
            data.update({
                "reports": Report.objects.filter(**args).count(),
                "immunized": sum(Report.objects.filter(**args).values_list("immunized", flat=True)),
               #"notimmunized": (population_target- sum(Report.objects.filter(**args).values_list("immunized", flat=True))),
			   "commodity": Report.objects.filter(**args).count()
            })
        
            data.update({
                "reports_perc":    int((data["reports"]    / report_target)    * 100) if (data["reports"]    > 0) else 0,
                "immunized_perc":    int((data["immunized"]    / population_target)    * 100) if (data["immunized"]    > 0) else 0,
                #"notimmunized_perc":    int((data["notimmunized"]    / population_target)    * 100) if (data["notimmunized"]    > 0) else 0,
				"notimmunized_perc":	int(((population_target-data["immunized"]) / population_target) * 100 ) if ((population_target-data["immunized"])>0) else 0,
            })
        days.append(data)
    
    total_immunized = sum(Report.objects.all().values_list("immunized", flat=True))

    #total_notimmunized = sum(Report.objects.all().values_list("notimmunized", flat=True))
    #total_notimmunized = (population_target - sum(Report.objects.filter(**args).values_list("immunized", flat=True)))
    total_notimmunized = (population_target - sum(Report.objects.all().values_list("immunized", flat=True)))
    notimmunized_stats = int((float(total_notimmunized) / population_target) * 100) if (total_notimmunized > 0) else 0
    immunized_stats = int((float(total_immunized) / population_target) * 100) if (total_immunized > 0) else 0

    return { "days": days, 
            "immunized_stats": immunized_stats,
            "notimmunized_stats": notimmunized_stats,
            "total_immunized": total_immunized,
            "total_notimmunized": total_notimmunized}


@register.inclusion_tag("ipd/partials/pilot.html")
def pilot_summary():
    
    # fetch all of the LGAs that we want to display
    lga_names = ["ALIERO", "AREWA DANDI", "ARGUNGU", "AUGIE"]
    lgas = LocationType.objects.get(name="LGA").locations.filter(name__in=lga_names)
    
    # called to fetch and assemble the
    # data structure for each pilot ward
    def __ward_data(ward):
        locations = ward.descendants(True)
        nc_reports = NonCompliance.objects.filter(location__in=locations)
        immunization_reports = Report.objects.filter(location__in=locations)
        
        return {
            "name":          ward.name,
            "contact":       ward.one_contact('WS', True),
            "immunization_reports": immunization_reports.count(),
            "nc_reports":    nc_reports.count(),
            "immunized":     sum(immunization_reports.values_list("immunized", flat=True)),
            "notimmunized":  (population_target - sum(immunization_reports.values_list("immunized", flat=True))),
            "commodity":      sum(immunization_reports.values_list("commodity", flat=True)),
            "cases":         sum(nc_reports.values_list("cases", flat=True)),
       } 
    # called to fetch and assemble the
    # data structure for each pilot LGA
    def __lga_data(lga):
        projections = {
            "population" : {
                        "ALIERO" : 15672.0,
                        "AREWA DANDI" : 15672.0,
						"ARGUNGU" : 15672.0,
						"AUGIE" : 15672.0,
            }
        }

        wards = lga.children.filter(type__name="Ward")
        
        ward_data = map(__ward_data, wards)
        def __wards_total(key):
            return sum(map(lambda w: w[key], ward_data))
        
        def __stats(key):
            return int(float(__wards_total(key)) / projections[key][str(lga.name)] * 100) if (__wards_total(key) > 0) else 0 

        return {
            "name":                     lga.name,
            "population_projected":  int(projections['population'][str(lga.name)]),
            "immunized_total":      int(__wards_total("immunized")),
            "notimmunized_total":   int(__wards_total("notimmunized")),
            "commodity_used":             int(__wards_total("commodity")),
            "wards":                    ward_data,
        }

    return { "pilot_lgas": map(__lga_data, lgas) }


@register.inclusion_tag("ipd/partials/immunization_summary_charts.html")
def immunization_summary_charts():
    summary = pilot_summary()
    netcards_projected = []
    netcards_total = []
    nets_total = []
    population_projected = []
    immunized_total = []
    notimmunized_total = []
    commodity_used = []
    lga_names = []
    pie_data = []
    data =[]
    #TODO: This must definitely be removed from here. It's a wild hack.
    compliance_summary = lambda x: int(sum(NonCompliance.objects.filter(reason=x).values_list('cases', flat=True)))
    # data = [ {"label":reason, "data":compliance_summary(reason_id)} for (reason_id, reason) in NonCompliance.NC_REASONS} ]

    #TODO: These should definitely leave here, and reside in their appropriate methods
    for reason_id, reason in NonCompliance.NC_REASONS:
        if compliance_summary(reason_id):
            pie_data.append((compliance_summary(reason_id), reason))

    pie_data_str = "[%s]" % ",".join(["{\"label\": \"%s\", \"data\": %d}" % (label,data) for (data, label) in pie_data])

    pilot_lgas = summary['pilot_lgas']
    for lga in pilot_lgas:
        population_projected.append("[%f, %f]" % (pilot_lgas.index(lga) * 4 + 0.5, lga['population_projected']))
        immunized_total.append("[%d, %d]" % (pilot_lgas.index(lga) * 4 + 1, lga['immunized_total']))
        notimmunized_total.append("[%f, %f]" % (pilot_lgas.index(lga) * 4 + 1.5, lga['notimmunized_total']))
        commodity_used.append("[%d, %d]" % (pilot_lgas.index(lga) * 4 + 2, lga['commodity_used']))
        lga_names.append("[%d, '%s']" % (pilot_lgas.index(lga) * 4 + 2, lga['name']))

    
    return {
        "population_projected": "[%s]" % ",".join(population_projected),
        "immunized_total": "[%s]" % ",".join(immunized_total),
        "notimmunized_total": "[%s]" % ",".join(notimmunized_total),
        "commodity_used": "[%s]" % ",".join(commodity_used),
        "netcards_projected": "[%s]" % ",".join(netcards_projected),
        "netcards_total": "[%s]" % ",".join(netcards_total),
        "pie_data": pie_data_str,
        "nets_total": "[%s]" % ",".join(nets_total),
        "lgas": "[%s]" % ",".join(lga_names)
    }
