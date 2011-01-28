from django.db import models
from locations.models import Location
from reporters.models import Reporter, PersistantConnection

class BirthRegistration(models.Model):
    """Stores birth registration records for the different health facilities"""
    reporter = models.ForeignKey(Reporter, blank=True, null=True, related_name="br_birthregistration")
    connection = models.ForeignKey(PersistantConnection, blank=True, null=True, related_name="br_birthregistration")
    location = models.ForeignKey(Location, related_name='birthregistration_records')
    girls_below1 = models.IntegerField()
    girls_1to4 = models.IntegerField()
    girls_5to9 = models.IntegerField()
    girls_10to18 = models.IntegerField()
    boys_below1 = models.IntegerField()
    boys_1to4 = models.IntegerField()
    boys_5to9 = models.IntegerField()
    boys_10to18 = models.IntegerField()

    time = models.DateTimeField()

    def __unicode__(self):
        return "%s" % (self.pk)
