#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import mptt
from django.db import models
from rapidsms.webui.managers import *


class LocationType(models.Model):
    name = models.CharField(max_length=100)
    
    
    class Meta:
        verbose_name = "Type"
    
    def __unicode__(self):
        return self.name


class Location(models.Model):
    """A Location is technically a geopgraphical point (lat+long), but is often
       used to represent a large area such as a city or state. It is recursive
       via the _parent_ field, which can be used to create a hierachy (Country
       -> State -> County -> City) in combination with the _type_ field."""
    
    type = models.ForeignKey(LocationType, related_name="locations", blank=True, null=True)
    name = models.CharField(max_length=100, help_text="Name of location", db_index=True)
    code = models.CharField(max_length=30, unique=True)
    population = models.PositiveIntegerField(default=0, null=False, blank=False)
    
    parent = models.ForeignKey("Location", related_name="children", null=True, blank=True,
        help_text="The parent of this Location. Although it is not enforced, it" +\
                  "is expected that the parent will be of a different LocationType")
    
    latitude  = models.DecimalField(max_digits=8, decimal_places=6, blank=True, null=True, help_text="The physical latitude of this location")
    longitude = models.DecimalField(max_digits=8, decimal_places=6, blank=True, null=True, help_text="The physical longitude of this location")
    
    lft = models.PositiveIntegerField(blank=True, default=0, db_index=True)
    rgt = models.PositiveIntegerField(blank=True, default=0, db_index=True)
    tree_id = models.PositiveIntegerField(blank=True, default=0, db_index=True)
    level = models.PositiveIntegerField(blank=True, default=0, db_index=True)

    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

    
    # TODO: how can we port the Location.contacts and Location.one_contact
    #       methods, now that the locations app has been split from reporters?
    #       even if they can import one another, they can't know if they're
    #       both running at parse time, and can't monkey-patch later.
    def one_contact(self, role, display=False):
        return ""

    def contacts(self, role=None):
        return Location.objects.get(pk=2)
    
    def ancestors(self, include_self=False):
        """Returns all of the parent locations of this location,
           optionally including itself in the output. This is
           very inefficient, so consider caching the output.
           
           Tim: This has been better implemented using the Django MPTT
           library."""
        locs = [self] if include_self else []
        loc = self
        
        locs = self.get_ancestors()
        if include_self:
            locs.append(self)

        return locs
    
    def descendants(self, include_self=False):
        """Returns all of the locations which are descended from this location,
           optionally including itself in the output. This is very inefficient
           (it recurses once for EACH), so consider caching the output.
           
           New improvements, please see doc for ancestors method."""
        locs = [self] if include_self else []
        
        locs.extend(self.get_descendants())
        
        return locs

    def get_stock(self):
        from supply.models import Stock
        try:
            stock = Stock.objects.get(location=self)
        except Stock.DoesNotExist:
            stock = None

        return stock

class Facility(models.Model):
    '''A facility can be anything from a cold store to a health facility'''
    name = models.CharField(max_length=100, help_text='The common name given to the facility')
    code = models.CharField(max_length=15, help_text='code used to represent this facility')
    location = models.ForeignKey(Location, blank=True, null=True, related_name="facilities")

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

mptt.register(Location, left_attr='lft', right_attr='rgt', tree_id_attr='tree_id', level_attr='level', order_insertion_by=['code'])
