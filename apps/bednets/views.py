#!/USR/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseServerError, Http404
from django.template import RequestContext, Template, Context
from locations.models import Location, LocationType
from supply.models import Shipment, Transaction, Stock, PartialTransaction
from campaigns.models import Campaign
from bednets.models import NetDistribution, CardDistribution 
from reporters.models import *
from rapidsms.webui.utils import render_to_response
from django.db.models import Q

import time
import itertools

@permission_required('bednets.can_view')
def export_data(req, campaign_id=None, state_id=None):
    if campaign_id and state_id and req.POST.has_key('activity'):
        campaign =  Campaign.objects.get(pk=campaign_id)
        if req.POST['activity'] == 'cards':
            netcards = campaign.cro(CardDistribution, Location.objects.get(pk=state_id))
            netcards = netcards.order_by('location','time')
            t = Template('''id,location_name,location_code,distributed,settlements,people,time
{% for card in cards %}{{ card.pk }},{{ card.location.name }},{{ card.location.code }},{{ card.distributed }},{{ card.settlements }},{{ card.people }},{{ card.time }}
{% endfor %}''')
            c = Context({'cards': netcards })
            response = HttpResponse(t.render(c), mimetype="text/csv")
            response['Content-Disposition'] = 'attachment; filename=cards_data.csv'
        elif req.POST['activity'] == 'nets':
            nets = campaign.cro(NetDistribution, Location.objects.get(pk=state_id))
            nets = nets.order_by('location','time')
            t = Template('''id,location_name,location_code,distributed,expected,actual,discrepancy,time
{% for net in nets %}{{ net.pk }},{{ net.location.name }},{{ net.location.code }},{{ net.distributed }},{{ net.expected }},{{ net.actual }},{{ net.discrepancy }},{{ net.time }}
{% endfor %}''')
            c = Context({'nets': nets })
            response = HttpResponse(t.render(c), mimetype="text/csv")
            response['Content-Disposition'] = 'attachment; filename=nets_data.csv'
    else:
        response = HttpResponse()
    return response

#@permission_required('bednets.can_view')
def dashboard(req, campaign_id=None, state_id=None):
    campaign = None
    state=None
    all_locations = []
    netcards = []
    bednets = []
    supplies = []
    reporters = []
    no_of_card_reports = 0
    no_of_distributed_cards = 0
    no_of_distributed_cards_coverage = 0
    no_of_distributed_cards_target = 0
    no_of_stock_transfers = 0
    no_of_net_reports = 0
    no_of_distributed_nets = 0
    no_of_distributed_nets_coverage = 0
    no_of_distributed_nets_target = 0
    no_of_reporters = 0
    active_locations = 0
	
    if campaign_id:
        campaign = Campaign.objects.get(id=campaign_id)
    	
    if campaign:
        if not state_id:
            state = campaign.campaign_states()[0]
        else:
            state = Location.objects.get(pk=state_id)
        
        # retrieve all locations
        all_locations.append(state)
        for lga in campaign.campaign_lgas(state):
            all_locations.append(lga)
            for desc in lga.get_descendants():
                all_locations.append(desc)

        netcards = campaign.cro(CardDistribution, state, all_locations)
        bednets = campaign.cro(NetDistribution, state, all_locations)
        
        no_of_reporters = Reporter.objects.filter(location__in=all_locations).count()
        no_of_card_reports = netcards.count()
        no_of_net_reports = bednets.count()
        no_of_distributed_cards = sum(netcards.values_list('distributed', flat=True))
        no_of_distributed_cards_target = state.population / 5.0
        no_of_distributed_cards_coverage = (no_of_distributed_cards / no_of_distributed_cards_target) * 100.0 if no_of_distributed_cards_target else 0

        no_of_distributed_nets = sum(bednets.values_list('distributed', flat=True))
        no_of_distributed_nets_target = (state.population / 5.0) * 2.0
        no_of_distributed_nets_coverage = (no_of_distributed_nets / no_of_distributed_nets_target) * 100.0 if no_of_distributed_nets_target else 0

        card_report_locations = netcards.values_list('location', flat=True)
        nets_report_locations = bednets.values_list('location', flat=True)
        all_report_locations = [i for i in itertools.chain(card_report_locations, nets_report_locations)]
        active_locations = len(set(all_report_locations))
        no_of_stock_transfers = PartialTransaction.objects.filter(Q(origin__in=all_locations)|Q(destination__in=all_locations)).count()
    else:
        pass
		
    return render_to_response(req, "bednets/bednets_dashboard.html", 
        {
        'no_of_stock_transfers': no_of_stock_transfers,
        'no_of_card_reports': no_of_card_reports,
        'no_of_distributed_cards': no_of_distributed_cards,
        'no_of_distributed_cards_target': no_of_distributed_cards_target,
        'no_of_distributed_cards_coverage': no_of_distributed_cards_coverage,
        'no_of_net_reports': no_of_net_reports,
        'no_of_distributed_nets': no_of_distributed_nets,
        'no_of_distributed_nets_target': no_of_distributed_nets_target,
        'no_of_distributed_nets_coverage': no_of_distributed_nets_coverage,
        'no_of_reporters': no_of_reporters,
        'active_locations': active_locations,
        'campaign_id': campaign_id,
        'state_id': state_id,
        })
		
