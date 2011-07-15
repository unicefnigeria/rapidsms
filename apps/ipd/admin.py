#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.contrib import admin
from ipd.models import *

class ReportAdmin(admin.ModelAdmin):
    list_display = ['location', 'immunized', 'commodity', 'reporter', 'time']
    date_hierarchy = 'time'
    search_fields = ['location__name', 'location__code', 'reporter__first_name', 'reporter__last_name']

class ShortageAdmin(admin.ModelAdmin):
    list_display = ['location', 'commodity', 'reporter', 'time']
    date_hierarchy = 'time'
    search_fields = ['location__name', 'location__code', 'reporter__first_name', 'reporter__last_name']

class NonComplianceAdmin(admin.ModelAdmin):
    list_display = ['location', 'reason', 'cases', 'reporter','time']
    date_hierarchy = 'time'
    search_fields = ['location__name', 'location__code', 'reporter__first_name', 'reporter__last_name']

admin.site.register(Report, ReportAdmin)
admin.site.register(Shortage, ShortageAdmin)
admin.site.register(NonCompliance, NonComplianceAdmin)
