# vim: ai sts=4 ts=4 et sw=4
from django.db import models
from locations.models import Location, LocationType

class Application(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

class Campaign(models.Model):
    name = models.CharField(max_length=255)
    locations = models.ManyToManyField(Location, limit_choices_to={'type__in': [LocationType.objects.get(name="State"), LocationType.objects.get(name="LGA")]})
    start_date = models.DateField()
    end_date = models.DateField()
    apps = models.ManyToManyField(Application)

    def __unicode__(self):
        return self.name

    def campaign_states(self):
        states = []
        for location in self.locations.all():
            if location.type == LocationType.objects.get(name="State"):
                states.append(location)
        return states

    def campaign_lgas(self, state):
        try:
            if self.locations.get(id=state.id) and state.type == LocationType.objects.get(name="State"):
                return self.locations.filter(parent=state,type__name="LGA") or state.get_children()
        except (Location.DoesNotExist):
            pass

    def cro(self, klass, state, locations=None):
        ''' Fetches all Campaign Related Objects when supplied the class '''
        try:
            if not locations:
                campaign_lgas = self.campaign_lgas(state)
                if len(campaign_lgas) == len(Location.objects.filter(parent=state)):
                    return klass.objects.filter(location__code__startswith=state.code,time__range=(self.start_date,self.end_date))
                else:
                    locations = []
                    locations.append(state)
                    for lga in self.campaign_lgas(state):
                        locations.append(lga)
                        for desc in lga.get_descendants():
                            locations.append(desc)

            return klass.objects.filter(location__in=locations,time__range=(self.start_date,self.end_date))
        except:
            pass

