#!/usr/bin/env python
# vim: ai sts=4 sw=4 ts=4 et
from django.conf import settings

for a in settings.INSTALLED_APPS:
    try:
        __path__.extend(__import__(a + '.templatetags', {}, {}, ['']).__path__)
    except ImportError:
        pass
