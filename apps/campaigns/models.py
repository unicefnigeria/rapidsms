# vim: ai sts=4 ts=4 et sw=4
from django.db import models
from location.models import Location

# Create your Django models here, if you need them.
class Application(models.Model):
    name = models.CharField()
    description = models.CharField()

    def __unicode__(self):
        return self.name

class Campaign(models.Model):
    name = models.CharField()
    locations = models.ManyToManyField(Location)
    start_date = models.DateField()
    end_date = models.DateField()
    app = models.ManyToManyField(Application)

    def __unicode__(self):
        return self.name
