#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import re
from datetime import date, datetime
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

import rapidsms
from rapidsms.parsers.keyworder import * 

from models import *
from reporters.models import PersistantConnection, Reporter, Role
from formslogic import *
import form.app as form_app

from form.models import Domain

class App(rapidsms.app.App):

    # lets use the Keyworder parser!
    kw = Keyworder()
    kw.prefix = ["mnchw"]
    
    def start(self):
        # initialize the forms app for Nigeria IPDC
        self._form_app = form_app.App(self.router)
        # this tells the form app to add itself as a message handler 
        # which registers the regex and function that this will dispatch to 
        self._form_app.add_message_handler_to(self)
        # this tells the form app that this is also a form handler 
        self._form_app.add_form_handler("ipd", IPDFormsLogic())

    def parse(self, message):
        self.handled = False

    def handle(self, message):
        self.handled = False
        try:
            if hasattr(self, "kw"):
                self.debug("HANDLE")
                
                # attempt to match tokens in this message
                # using the keyworder parser
                results = self.kw.match(self, message.text)
                if results:
                    func, captures = results
                    # if a function was returned, then a this message
                    # matches the handler _func_. call it, and short-
                    # circuit further handler calls
                    func(self, message, *captures)
                    return self.handled
                else:
                    self.debug("NO MATCH FOR %s" % message.text)
            else:
                self.debug("App does not instantiate Keyworder as 'kw'")
        except Exception, e:
            self.log_last_exception()


    def cleanup(self, message):
        # this will add a generic response based 
        # on the available forms
        if not message.responses:
            message.respond("Sorry we didn't understand that. %s" % self.form_app.get_helper_message())
        

    def __get(self, model, **kwargs):
        try:
            # attempt to fetch the object
            return model.objects.get(**kwargs)
            
        # no objects or multiple objects found (in the latter case,
        # something is probably broken, so perhaps we should warn)
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            return None

    # HELP ----------------------------------------------------------
    @kw("report help")
    def help(self, message):
        message.respond('Format: MNCHW REPORT [LOCATION] [COMMODITY] [IMMUNIZED]. Replace values in brackets with their actual values.')
        self.handled = True
        
    @kw("report (numbers) (whatever)")
    def report(self, message, location, report):
        con = PersistantConnection.from_message(message)
        rep = con.reporter
        report_date = datetime(message.date.year, message.date.month, message.date.day)
        
        try:
            loc = Location.objects.get(code=location)
        except Location.DoesNotExist:
            message.respond('Unknown location with code: %s' % location)
            self.handled = True
            return self.handled
        
        if not (con and rep):
            message.respond('Please register your phone with RapidSMS before sending your report.')
            self.handled = True
            return self.handled
        
        commodities = self._parse_commodity_data(report)
        if commodities:
            # store commodity data
            for (commodity,immunized) in commodities.items():
                (report, created) = Report.objects.get_or_create(
                    reporter=rep, connection=con, location=loc,
                    time=report_date, commodity=commodity)
                report.immunized = immunized
                report.save()
            
            # generate the response
            response = 'Thank you %s. Received MNCHW REPORT for %s %s: ' % \
                (rep.first_name, loc.name, loc.type.name)
            response += ", ".join(['%s=%s' % (c.upper(),i) for (c,i) in commodities.items()])
            message.respond(response)
        else:
            message.respond("Sorry I couldn't understand your message. Please send MNCHW REPORT HELP for instructions.")
        
        self.handled = True
        
    def _parse_commodity_data(self, s):
        ''' parser for the gender data submitted
        by the birth registrars
        no_immunized        ::= number
        commodity           ::= dpt|opv|vita|measles|...
        commodity_report    ::= (commodity) no_immunized
        submitted_data      ::= commodity_report*'''

        commodity_re = re.compile(r'^(vita|opv|tt|mv|bcg|dpt|yf|hepb|plus|deworm|fe|fp|hp|llin|muac)$', re.I)

        in_data = ''
        commodity_data = {}
        gen = s.split()
        for token in gen:
            if commodity_re.match(token):
                in_data = token.lower()
                continue
            if token.isdigit() and in_data:
                commodity_data[in_data] = int(token)

        return commodity_data
        
    def add_message_handler(self, regex, function):
        '''Registers a message handler with this app.  Incoming messages that match this 
           will call the function'''
        self.info("Registering regex: %s for function %s, %s" %(regex, function.im_class, function.im_func.func_name))
        self.kw.regexen.append((re.compile(regex, re.IGNORECASE), function))
        
    @property
    def form_app(self):
        if hasattr(self, "_form_app"):
            return self._form_app

