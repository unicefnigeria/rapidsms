#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.contrib import admin
from campaigns.models import *

class CampaignAdmin (admin.ModelAdmin):
    filter_horizontal = ('locations','apps',)

admin.site.register(Application)
admin.site.register(Campaign, CampaignAdmin)
