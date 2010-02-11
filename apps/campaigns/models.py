# vim: ai sts=4 ts=4 et sw=4
from django.db import models
from locations.models import Location

# Create your Django models here, if you need them.
class Application(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

class Campaign(models.Model):
    name = models.CharField(max_length=255)
    locations = models.ManyToManyField(Location)
    start_date = models.DateField()
    end_date = models.DateField()
    apps = models.ManyToManyField(Application)

    def __unicode__(self):
        return self.name
