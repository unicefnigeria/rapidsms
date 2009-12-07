# vim: ai sts=4 ts=4 et sw=4
from django.db import models
from reporters.models import Reporter, PersistantConnection
from locations.models import Location
import time as taim
from form.models import Domain
from datetime import datetime,timedelta

class Report(models.Model):
    '''The Report model is used in storing Ward Summary Reports necessary
    for tracking number of persons immunized'''

    IM_COMMODITIES = (
        ('opv', 'OPV'),
        ('vita', 'Vitamin A'),
        ('tt', 'Tetanus Toxoid'),
        ('mv', 'Measles Vaccine'),
        ('yf', 'Yellow Fever'),
        ('hepb', 'Hepatitis B'),
        ('folate', 'Ferrous Folate'),
        ('dpt', 'Diphtheria'),
        ('deworm', 'Deworming'),
        ('sp', 'Sulphadoxie Pyrimethanol for IPT'),
        ('plus', 'Plus'),
    )

    reporter = models.ForeignKey(Reporter, null=True, blank=True)
    connection = models.ForeignKey(PersistantConnection, null=True, blank=True)
    location = models.ForeignKey(Location)
    time = models.DateTimeField()
    immunized = models.PositiveIntegerField(blank=True, null=True, help_text="Total Persons Immunized")
    commodity = models.CharField(blank=True, null=True, max_length=10, choices=IM_COMMODITIES, help_text="This is the commodity of the immunization being reported")

    class Meta:
        # the permission required for this tab to display in the UI
        permissions = (
            ("can_view", "Can view"),
        )

    def __unicode__(self):
        return "%s (%s) => %s, %s" % (self.location, self.reporter, self.commodity, self.immunized)

class NonCompliance(models.Model):
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
     
    reporter = models.ForeignKey(Reporter, null=True, blank=True)
    connection = models.ForeignKey(PersistantConnection, null=True, blank=True)
    location = models.ForeignKey(Location)
    time = models.DateTimeField()
    reason = models.CharField(blank=True, null=True, max_length=1, choices=NC_REASONS, help_text="This is the reason for non-compliance")
    cases = models.PositiveIntegerField()

    def __unicode__(self):
        return "%s (%s) %s %s" % (self.location, self.reporter, self.reason, self.cases)

    @staticmethod
    def summed_data(location):
        pass

    @staticmethod
    def non_compliance_total(location):
        all = NonCompliance.objects.all().filter(location__pk=location.pk)

        return {"cases": sum(all.values_list("cases", flat=True))
        }

    def get_reason(reason):
        if int(reason) in range(1, 9):
            return NonCompliance.NC_REASONS[int(reason) - 1][1]
        else:
            return NonCompliance.NC_REASONS[8][1]

    @staticmethod
    def get_reason(reason):
        if int(reason) in range(1, 9):
            return NonCompliance.NC_REASONS[int(reason) - 1][1]
        else:
            return NonCompliance.NC_REASONS[8][1]
    def get_reason_total(reason, location):
        all = NonCompliance.objects.all().filter(location__code__startswith=location.code, reason=reason)

        reason_total = sum(all.values_list('cases', flat=True))
        return reason_total
        
class Shortage(models.Model):
    '''Model for storing shortage reports'''
    # I'm suspecting that this might be a better way to store
    # the commodities.
    SHORTAGE_COMMODITIES = (
        ('opv', 'OPV'),
        ('vita', 'Vitamin A'),
        ('tt', 'Tetanus Toxoid'),
        ('mv', 'Measles Vaccine'),
        ('yf', 'Yellow Fever'),
        ('hepb', 'Hepatitis B'),
        ('folate', 'Ferrous Folate'),
        ('dpt', 'Diphtheria'),
        ('deworm', 'Deworming'),
        ('sp', 'Sulphadoxie Pyrimethanol for IPT'),
        ('plus', 'Plus'),
    )

    reporter = models.ForeignKey(Reporter, null=True, blank=True)
    # What's the case for storing the connection since the report has one?
    # TODO: This has to go!
    connection = models.ForeignKey(PersistantConnection, null=True, blank=True)
    location = models.ForeignKey(Location)
    time = models.DateTimeField()
    commodity = models.CharField(blank=True, null=True, max_length=10, choices=SHORTAGE_COMMODITIES, help_text="This is the commodity of the immunization being reported")

    def __unicode__(self):
        return "%s (%s) => %s" % (self.reporter, self.location, self.commodity)
