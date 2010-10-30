from django_extensions.management.jobs import BaseJob
from locations.models import *
import sys
import os

class Job(BaseJob):
    help = "Creates the vaccine stores (one per lga)"

    def execute(self):
        types = {}
        types = dict(map(lambda loc: [loc.name.upper(), loc], LocationType.objects.all()))
        # create lga stores and state stores
        all_locations = Location.objects.filter(type__in=[types['LGA'], types['STATE'])
        for location in all_locations:
            Facility(name=location.name, code=location.code, location=location).save()

        # create the national and regional stores
        other_stores = [
            {'name': 'National Store', 'code': 'ns',
                'location': Location.objects.get(code='15') }, # FCT
            {'name': 'North Central Store', 'code': 'nc',
                'location': Location.objects.get(code='27') }, # Niger
            {'name': 'North East Store', 'code': 'ne',
                'location': Location.objects.get(code='05') }, # Bauchi
            {'name': 'North West Store', 'code': 'nw',
                'location': Location.objects.get(code='20') }, # Kano
            {'name': 'South East Store', 'code': 'se',
                'location': Location.objects.get(code='14') }, # Enugu
            {'name': 'South West Store', 'code': 'sw',
                'location': Location.objects.get(code='25') }, # Lagos
            {'name': 'South South Store', 'code': 'ss',
                'location': Location.objects.get(code='12') }, # Edo
        ]
        for store in other_stores:
             Facility(name=store['name'], code=store['code'], location=store['location']).save()

