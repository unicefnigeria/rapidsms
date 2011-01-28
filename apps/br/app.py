#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import rapidsms
from rapidsms.parsers.keyworder import *
from models import BirthRegistration
from reporters.models import PersistantConnection, Reporter, Role
from locations.models import Location
from rapidsms.message import StatusCodes
import re

class FormValidationError(Exception):
    error_msgs = {
        'invalid_location': "Sorry, I don't know any location with the code: %s",
        'invalid_role': "Unknown role code: %s",
        'unauthorized_reporter': 'Please register your number with RapidSMS before sending this report',
        'unauthorized_role': 'Your role does not have permissions to send this report.',
        }

    def __init__(self, error_key, error_values=[]):
        self.msg = self.error_msgs[error_key] % tuple(error_values)

class App(rapidsms.app.App):

    kw = Keyworder()
    error_msgs = {
        'invalid_location': "Sorry, I don't know any location with the code: %s",
        'invalid_role': "Unknown role code: %s",
        'unauthorized_reporter': 'Please register your number with RapidSMS before sending this report',
        'unauthorized_role': 'Your role does not have permissions to send this report.',
        }

    def start(self):
        pass

    def parse(self, message):
        self.handled = False
        pass

    def handle(self, message):
        try:
            if hasattr(self, "kw"):
                try:
                    func, captures = self.kw.match(self, message.text)
                    func(self, message, *captures)
                    return self.handled
                except Exception, e:
                    return self.handled
            else:
                self.debug('App has not instantiated keyworder as kw')
        except Exception, e:
            self.error(e)

    def cleanup(self, message):
        pass

    kw.prefix = ['br']

    @kw("help")
    def help(self, message):
        message.respond("['report', 'register']", StatusCodes.OK)
        self.handled = True

    @kw('register (numbers) (slug) (whatever)')
    def register(self, message, location_code, role, name=''):
        data = {}
        try:
            data['location'] = Location.objects.get(code__iexact=location_code)
            data['role'] = Role.objects.get(code__iexact=role)
            data['alias'], data['first_name'], data['last_name'] = Reporter.parse_name(name.strip())
            rep = Reporter(**data)
            conn = PersistantConnection.from_message(message)
            if Reporter.exists(rep, conn):
                message.respond("Hello again %s! You are already registered as a %s at %s %s." % (rep.first_name, rep.role, rep.location, rep.location.type), StatusCodes.OK)
                self.handled = True
                return True

            rep.save()
            conn.reporter = rep
            conn.save()

            message.respond("Hello %s! You are now registered as %s at %s %s."\
                            % (rep.first_name, rep.role, rep.location, rep.location.type), StatusCodes.OK)
        except Role.DoesNotExist:
            message.respond(self.error_msgs['invalid_role'] % role)
        except Location.DoesNotExist:
            message.respond(self.error_msgs['invalid_location'] % location_code)
        
        self.handled = True
        return True

    @kw('report (whatever)')
    def report(self, message, gender_data):
        report = self._parse_gender_data(gender_data)

        try:
            if not hasattr(message, 'reporter') or not message.reporter:
                raise FormValidationError('unauthorized_reporter')

            if not message.reporter.role.code.lower() in ['br']:
                raise FormValidationError('unauthorized_role')

            location = message.reporter.location

            # store the report
            # TODO: add ability to replace duplicate reports
            br = BirthRegistration()
            br.connection = PersistantConnection.from_message(message)
            br.reporter = br.connection.reporter
            br.location = location
            br.girls_below1 = report['female'][1] if report['female'].has_key(1) else 0
            br.girls_1to4 = report['female'][2] if report['female'].has_key(2) else 0
            br.girls_5to9 = report['female'][3] if report['female'].has_key(3) else 0
            br.girls_10to18 = report['female'][4] if report['female'].has_key(4) else 0
            br.boys_below1 = report['male'][1] if report['male'].has_key(1) else 0
            br.boys_1to4 = report['male'][2] if report['male'].has_key(2) else 0
            br.boys_5to9 = report['male'][3] if report['male'].has_key(3) else 0
            br.boys_10to18 = report['male'][4] if report['male'].has_key(4) else 0
            br.time = message.date
            br.save()

            # respond adequately
            message.respond('Thank you %s. BR report received for %s %s Date=%s Girls <1: %d, Girls 1-4: %d, Girls 5-9: %d, Girls 10-18: %d, Boys <1: %d, Boys 1-4: %d, Boys 5-9: %d, Boys 10-18: %d' % (br.reporter.first_name, location.name, location.type.name, message.date.strftime('%d/%m/%Y'), br.girls_below1, br.girls_1to4, br.girls_5to9, br.girls_10to18, br.boys_below1, br.boys_1to4, br.boys_5to9, br.boys_10to18))
        except FormValidationError, f:
            message.respond(f.msg)
        except Exception, e:
            self.debug(e)
        
        self.handled = True

    @kw('(whatever)')
    def default(self, message, text):
        message.respond("We didn't understand your message. Please text 'BR HELP' for available forms.", StatusCodes.OK)
        self.handled = True

    def _parse_gender_data(self, s):
        ''' parser for the gender data submitted
        by the birth registrars
        gender_data         ::= number
        gender_male         ::= M|m|B|b
        gender_female       ::= F|f|G|g
        gender_submission   ::= (gender_male|gender_female) gender_data*
        submitted_data      ::= gender_submission*'''

        male_re = re.compile(r'^(m|b).*', re.I)
        female_re = re.compile(r'^(f|g).*', re.I)

        in_data = ''
        gender_data = {'male': {}, 'female': {}}
        counter = 0
        gen = s.split()
        for token in gen:
            if male_re.match(token):
                in_data = 'male'
                counter = 1
                continue
            if female_re.match(token):
                in_data = 'female'
                counter = 1
                continue
            if token.isdigit() and in_data:
                gender_data[in_data][counter] = int(token)
                counter += 1

        return gender_data


