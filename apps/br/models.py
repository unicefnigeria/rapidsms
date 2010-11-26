from django.db import models
from locations.models import Location
from reporters.models import Reporter, PersistantConnection

class BirthRegistration(models.Model):
    """Stores birth registration records for the different health facilities"""
    reporter = models.ForeignKey(Reporter, blank=True, null=True, related_name="br_birthregistration")
    connection = models.ForeignKey(PersistantConnection, blank=True, null=True, related_name="br_birthregistration")
    location = models.ForeignKey(Location, related_name='birthregistration_records')
    girls_under5 = models.IntegerField()
    girls_over5 = models.IntegerField()
    boys_under5 = models.IntegerField()
    boys_over5 = models.IntegerField()

    time = models.DateTimeField()

    def __unicode__(self):
        return "%s (GL5: %d GO5: %d BL5: %d BO5: %d)" % (self.location, \
            self.girls_under5, self.girls_over5, self.boys_under5, \
            self.boys_over5)
