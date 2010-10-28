from django_extensions.management.jobs import BaseJob
from locations.models import *
import sys
import os

class Job(BaseJob):
    help = "Creates the Health Facilities (one per state or lga and three per ward)"

    def execute(self):
        types = {}
        types = dict(map(lambda loc: [loc.name.upper(), loc], LocationType.objects.all()))
        all_locations = Location.objects.all()
        for location in all_locations:
            if location.type in [types['STATE'], types['LGA']]:
                Facility(name=location.name, location=location).save()
            if location.type == types['WARD']:
                # we save three facilities per ward
                Facility(name='Health Facility #1', location=location).save()
                Facility(name='Health Facility #2', location=location).save()
                Facility(name='Health Facility #3', location=location).save()

