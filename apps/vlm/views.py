#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from models import *
from rapidsms.webui.utils import render_to_response
from datetime import datetime

def _compare(x, y):
    if x['commodity_code'] == y['commodity_code']:
        return 0
    if x['commodity_code'] < y['commodity_code']:
        return -1
    else:
        return 1

''' the filter_stock method returns only the first of a particular
commodity in a list of commodity list data'''
def filter_stock(stock_list):
    old_list = stock_list
    new_list = []
    commodity_map = {}
    for item in old_list:
        key = 'commodity_code' if item.has_key('commodity_code') else 'commodity'
        if not commodity_map.has_key(item[key]):
            new_list.append(item)
            commodity_map[item[key]] = True

    return new_list

def dashboard(req):
    all_commodities = dict(PartialTransaction.COMMODITIES)
    month_year = datetime.now().year
    month_month = datetime.now().month

    location = 'ns'

    start_period = datetime(year=2010, month=1, day=1) # Start from January 1st, 2010
    if month_month == 12:
        end_period = datetime(year=month_year+1, month=1, day=1)
    else:
        end_period = datetime(year=month_year, month=month_month + 1, day=1)

    location_stock_balance = []
    location_stock = Stock.objects.filter(facility__code=location, time__gte=start_period, time__lt=end_period).order_by('-time')
    if location_stock:
        stock_date = location_stock[0].time
    else:
        stock_date = None
        
    for stock in location_stock:
        location_stock_balance.append({'commodity_code': stock.commodity, 'commodity': all_commodities[stock.commodity], 'balance': stock.balance})

    location_stock_balance = filter_stock(location_stock_balance)
    location_stock_balance.sort(_compare)

    stock_balances = []

    sub_locations = Facility.objects.get(code=location).location.children.all()
    commodities = Stock.objects.filter(facility__location__in=sub_locations).order_by('commodity').values_list('commodity', flat=True).distinct()
    commodities_dict = dict([[x, 0] for x in commodities])
    for sub_location in sub_locations:
        sub_location_commodities = commodities_dict.copy()
        sub_location_stock = Stock.objects.filter(facility__location=sub_location, time__gte=start_period, time__lt=end_period).order_by('-time')
        if sub_location_stock:
            sub_location_stock_date = sub_location_stock[0].time
        else:
            sub_location_stock_date = None

        sub_location_stock_balance = []
        '''The following fetches all the stock balances and updates the commodities list
        with the latest available stock balance for each commodity'''
        for stock in sub_location_stock:
            sub_location_stock_balance.append({'commodity': stock.commodity, 'balance': stock.balance})

        # filter the stock balance and return only the latest
        sub_location_stock_balance = filter_stock(sub_location_stock_balance)

        # do the update
        for stock_balance in sub_location_stock_balance:
            sub_location_commodities[stock_balance['commodity']] = stock_balance['balance']

        stock_balances.append({'name':sub_location.name, 'latest': sub_location_stock_date, 'commodities': sub_location_commodities})
        
    return render_to_response(req, "vlm/vlm_dashboard.html", {
        'stock': location_stock_balance, 'commodities': commodities, 
        'regions': stock_balances, 'commodity_names': all_commodities,
        'stock_date': stock_date,
    })

def location_summary(req, zone="", state="", year=0, month=0):
    all_commodities = dict(PartialTransaction.COMMODITIES)
    month_year = datetime.now().year if not year else int(year)
    month_month = datetime.now().month if not month else int(month)

    location = state if state else zone

    # TODO: Use the earliest report as the start period
    start_period = datetime(year=2010, month=1, day=1) # Start from January 1st, 2010
    end_period = datetime(year=month_year, month=month_month + 1 if month_month < 12 else 11 + 1, day=1)

    location_stock_balance = []
    if state:
        location_stock = Stock.objects.filter(facility__code=state, time__gte=start_period, time__lt=end_period).order_by('-time')
    else:
        location_stock = Stock.objects.filter(facility__code=zone, time__gte=start_period, time__lt=end_period).order_by('-time')
        
    for stock in location_stock:
        location_stock_balance.append({'commodity_code': stock.commodity, 'commodity': all_commodities[stock.commodity], 'balance': stock.balance})

    location_stock_balance = filter_stock(location_stock_balance)
    location_stock_balance.sort(_compare)

    stock_balances = []

    sub_locations = Facility.objects.get(code=location).location.children.all()
    commodities = Stock.objects.filter(facility__location__in=sub_locations).order_by('commodity').values_list('commodity', flat=True).distinct()
    commodities_dict = dict([[x, 0] for x in commodities])

    for sub_location in sub_locations:
        sub_location_commodities = commodities_dict.copy()
        sub_location_stock = Stock.objects.filter(facility__location=sub_location, time__gte=start_period, time__lt=end_period).order_by('-time')

        sub_location_stock_balance = []
        '''The following fetches all the stock balances and updates the commodities list
        with the latest available stock balance for each commodity'''
        for stock in sub_location_stock:
            sub_location_stock_balance.append({'commodity': stock.commodity, 'balance': stock.balance})

        # filter the stock balance and return only the latest
        sub_location_stock_balance = filter_stock(sub_location_stock_balance)

        # do the update
        for stock_balance in sub_location_stock_balance:
            sub_location_commodities[stock_balance['commodity']] = stock_balance['balance']

        stock_balances.append({'sub_location':sub_location.name, 'commodities': sub_location_commodities})
        
    return render_to_response(req, "vlm/vlm_location_summary.html", {
        'stock': location_stock_balance, 'zone_id': zone, 'state_id': state, 'month_year': month_year,
        'month_month': month_month, 'commodities': commodities, 
        'sub_locations_stock': stock_balances, 'commodity_names': all_commodities,
    })

