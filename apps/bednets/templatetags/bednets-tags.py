#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django import template

register = template.Library()

from datetime import datetime, timedelta
from reporters.models import *
from locations.models import *
from supply.models import *
from bednets import constants
from bednets.models import *
from campaigns.models import *
from django.db.models import Q

current_campaign_location = Location.objects.get(name="KEBBI", type=LocationType.objects.get(name="State"))
current_campaign_location_descendants = current_campaign_location.descendants()

@register.inclusion_tag("bednets/partials/recent.html")
def recent_reporters(number=4):
    last_connections = PersistantConnection.objects.filter(reporter__isnull=False).order_by("-last_seen")[:number]
    last_reporters = [conn.reporter for conn in last_connections]
    return { "reporters": last_reporters }


@register.inclusion_tag("bednets/partials/stats.html")
def bednets_stats():
    return { "stats": [
#        {
#            "caption": "Callers",
#            "value":   PersistantConnection.objects.count()
#        },
        {
            "caption": "Reporters",
            "value":   Reporter.objects.filter(location__in=current_campaign_location_descendants).count()
        },
        {
            "caption": "Active Locations",
            "value":   PartialTransaction.objects.filter(destination__in=current_campaign_location_descendants).values("destination").distinct().count() +
                       CardDistribution.objects.filter(location__in=current_campaign_location_descendants).values("location").distinct().count()
        },
        {
            "caption": "Stock Transfers",
            "value":   PartialTransaction.objects.filter(Q(destination__in=current_campaign_location_descendants)|Q(origin__in=current_campaign_location_descendants)).count()
        },
        {
            "caption": "Net Card Reports",
            "value":   CardDistribution.objects.filter(location__in=current_campaign_location_descendants).count()
        },
        {
            "caption": "Net Cards Distributed",
            "value":   sum(CardDistribution.objects.filter(location__in=current_campaign_location_descendants).values_list("distributed", flat=True))
        },
        {
            "caption": "Net Reports",
            "value":   NetDistribution.objects.filter(location__in=current_campaign_location_descendants).count()
        },
        {
            "caption": "Nets Distributed",
            "value":   sum(NetDistribution.objects.filter(location__in=current_campaign_location_descendants).values_list("distributed", flat=True))
        },
#        {
#            "caption": "Coupon Recipients",
#            "value":   sum(CardDistribution.objects.values_list("people", flat=True))
#        }
    ]}


@register.inclusion_tag("bednets/partials/progress.html")
def daily_progress():
    start = datetime(2009, 12, 05)
    end = datetime(2009, 12, 10)
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
                "reports": CardDistribution.objects.filter(**args).count(),
                "coupons": sum(CardDistribution.objects.filter(**args).values_list("distributed", flat=True)),
                "recipients": sum(CardDistribution.objects.filter(**args).values_list("people", flat=True))
            })
        
            data.update({
                "reports_perc":    int((data["reports"]    / report_target)    * 100) if (data["reports"]    > 0) else 0,
                "coupons_perc":    int((data["coupons"]    / coupon_target)    * 100) if (data["coupons"]    > 0) else 0,
                "recipients_perc":    int((data["recipients"]    / recipient_target)    * 100) if (data["recipients"]    > 0) else 0,
            })
        days.append(data)
    
    total_netcards = sum(CardDistribution.objects.filter(location__in=current_campaign_location_descendants).values_list("distributed", flat=True))
    netcards_stats = int(float(total_netcards) / coupon_target * 100) if (total_netcards > 0) else 0

    total_beneficiaries = sum(CardDistribution.objects.filter(location__in=current_campaign_location_descendants).values_list("people", flat=True))
    beneficiaries_stats = int(float(total_beneficiaries) / recipient_target * 100) if (total_beneficiaries > 0) else 0

    return { "days": days, 
            "netcards_stats": netcards_stats, 
            "beneficiaries_stats": beneficiaries_stats,
            "total_netcards": total_netcards,
            "total_beneficiaries": total_beneficiaries}


@register.inclusion_tag("bednets/partials/distribution.html")
def distribution_summary(campaign_id, state_id):
    campaign = None
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
    
    # called to fetch and assemble the
    # data structure for each pilot ward
    def __ward_data(ward):
        locations = ward.descendants(True)
        reports = campaign.cro(CardDistribution, state, locations)
        nets_reports = campaign.cro(NetDistribution, state, locations)
        style = "" 
        if reports.count() == 0 and nets_reports.count() == 0:
            style = "warning" 

        return {
            "name":          ward.name,
            "contact":       ward.one_contact('WS', True),
            "reports":       reports.count(),
            "nets_reports":  nets_reports.count(),
            "netcards":      sum(reports.values_list("distributed", flat=True)),
            "nets":          sum(nets_reports.values_list("distributed", flat=True)),
            "beneficiaries": sum(reports.values_list("people", flat=True)),
            "class":         style}
    
    # called to fetch and assemble the
    # data structure for each pilot LGA
    def __lga_data(lga):
        wards = lga.children.all()
        reporters = Reporter.objects.filter(location__in=wards)
        supervisors = reporters.filter(role__code__iexact="WS").count()
        summary = "%d supervisors in %d wards" % (supervisors, len(wards))
        
        ward_data = map(__ward_data, wards)
        def __wards_total(key):
            return sum(map(lambda w: w[key], ward_data))
        
        return {
            "name":                     lga.name,
            "summary":                  summary,
            "netcards_total":           int(__wards_total("netcards")),
            "netcards_total_target":    lga.population / 5.0, # target = population / 5
            "netcards_total_coverage":  int(__wards_total("netcards")) / (lga.population / 5.0) * 100.0 if lga.population else 0,
            "beneficiaries_total":      int(__wards_total("beneficiaries")),
            "wards":                    ward_data,
            "reports":                  __wards_total("reports"),
            "nets_total":               __wards_total("nets"),
            "nets_total_target":        (lga.population / 5.0) * 2.0,
            "nets_total_coverage":      __wards_total("nets") / ((lga.population / 5.0) * 2.0) * 100.0 if lga.population else 0, # nets = cards * 2
            "nets_reports":             __wards_total("nets_reports"),
        }

    if campaign and state:
        return { "lgas_distribution": map(__lga_data, lgas) }
    else:
        return { "lgas_distribution": None }


@register.inclusion_tag("bednets/partials/logistics.html")
def logistics_summary(campaign_id, state_id):
    campaign = None
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

@register.inclusion_tag("bednets/partials/distribution_summary_charts.html")
def distribution_summary_charts():
    summary = pilot_summary()
    netcards_projected = []
    netcards_total = []
    nets_total = []
    beneficiaries_projected = []
    beneficiaries_total = []
    lga_names = []

    pilot_lgas = summary['pilot_lgas'][0:4]
    for lga in pilot_lgas:
        netcards_projected.append("[%d, %d]" % (pilot_lgas.index(lga) * 3 + 1, lga['netcards_projected']))
        netcards_total.append("[%d, %d]" % (pilot_lgas.index(lga) * 3 + 2, lga['netcards_total']))
        nets_total.append("[%d, %d]" % (pilot_lgas.index(lga) * 3 + 3, lga['nets_total']))
        beneficiaries_projected.append("[%d, %d]" % (pilot_lgas.index(lga) * 3 + 1, lga['beneficiaries_projected']))
        beneficiaries_total.append("[%d, %d]" % (pilot_lgas.index(lga) * 3 + 2, lga['beneficiaries_total']))
        lga_names.append("[%d, '%s']" % (pilot_lgas.index(lga) * 3 + 2, lga['name']))
    return {
        "beneficiaries_projected": "[%s]" % ",".join(beneficiaries_projected),
        "beneficiaries_total": "[%s]" % ",".join(beneficiaries_total),
        "netcards_projected": "[%s]" % ",".join(netcards_projected),
        "netcards_total": "[%s]" % ",".join(netcards_total),
        "nets_total": "[%s]" % ",".join(nets_total),
        "lgas": "[%s]" % ",".join(lga_names)
    }
