#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django import template
register = template.Library()

def key_value(value, args):
    '''Retrieves a value from a list given the key'''
    return value.get(args) if value.has_key(args) else None

register.filter('key_value', key_value)
