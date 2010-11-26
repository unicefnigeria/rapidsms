#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import rapidsms
from rapidsms.parsers.keyworder import *
from models import BirthRegistration
from reporters.models import PersistantConnection, Reporter, Role
from locations.models import Location
from rapidsms.message import StatusCodes

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

    @kw('report (slug) (numbers) (numbers) (numbers) (numbers)')
    def report(self, message, location_code, girls_l5, girls_g5, boys_l5, boys_g5):
        try:
            if not hasattr(message, 'reporter'):
                raise FormValidationError('unauthorized_reporter')
            if not message.reporter.role.code.lower() in ['br']:
                raise FormValidationError('unauthorized_role')

            location = Location.objects.get(code=location_code)

            # store the report
            # TODO: add ability to replace duplicate reports
            br = BirthRegistration()
            br.connection = PersistantConnection.from_message(message)
            br.reporter = br.connection.reporter
            br.location = location
            br.girls_under5 = int(girls_l5)
            br.girls_over5 = int(girls_g5)
            br.boys_under5 = int(boys_l5)
            br.boys_over5 = int(boys_g5)
            br.time = message.date
            br.save()

            # respond adequately
            message.respond('Thank you %s. Birth Registration report received for %s %s Date=%s Girls under 5: %d, Girls over 5: %d, Boys under 5: %d, Boys over 5: %d' % (br.reporter.first_name, location.name, location.type.name, message.date.strftime('%d/%m/%Y'), int(girls_l5), int(girls_g5), int(boys_l5), int(boys_g5)))
        except Location.DoesNotExist:
            message.respond(self.error_msgs['invalid_location'] % location_code)
        except FormValidationError, f:
            message.respond(f.msg)
        except Exception, e:
            self.debug(e)
        
        self.handled = True

    @kw('(whatever)')
    def default(self, message, text):
        message.respond("We didn't understand your message. Please text 'BR HELP' for available forms.", StatusCodes.OK)
        self.handled = True
