#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import rapidsms
from rapidsms.parsers.keyworder import *
from models import *
from reporters.models import PersistantConnection, Reporter, Role
from datetime import datetime, timedelta
from locations.models import Location
from rapidsms.message import StatusCodes
import tokenize
from StringIO import StringIO

class FormValidationError(Exception):
    error_msgs = {
        'invalid_facility': "Sorry, I don't have the facility with the code: %s in my database. Please confirm and try again.",
        'invalid_location': "Sorry, I don't know any location with the code: %s",
        'invalid_role': "Unknown role code: %s",
        'invalid_commodity': "Hmm... I don't have any recollection of a commodity with the code: %s. I only know the following commodities: %s",
        'unauthorized_reporter': 'Please register your number with RapidSMS before sending this report',
        'unauthorized_role': 'Your role does not have permissions to send this report.',
        }

    def __init__(self, error_key, error_values=[]):
        self.msg = self.error_msgs[error_key] % tuple(error_values)

class App(rapidsms.app.App):

    kw = Keyworder()
    error_msgs = {
        'invalid_facility': "Sorry, I don't have the facility with the code: %s in my database. Please confirm and try again.",
        'invalid_location': "Sorry, I don't know any location with the code: %s",
        'invalid_role': "Unknown role code: %s",
        'invalid_commodity': "Hmm... I don't have any recollection of a commodity with the code: %s. I only know the following commodities: %s"
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

    kw.prefix = ['vlm']

    @kw("help")
    def help(self, message):
        message.respond("['receive', 'issue', 'stock', 'register']", StatusCodes.OK)
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

    @kw('stock (slug) (whatever)')
    def stock(self, message, store_code, commodity_stock):
        commodity_list = []
        try:
            if not hasattr(message, 'reporter'):
                raise FormValidationError('unauthorized_reporter')
            if not message.reporter.role.code.lower() in ['sm', 'nsm', 'rsm']:
                raise FormValidationError('unauthorized_role')

            reporter = message.reporter
            store = Facility.objects.get(code__iexact=store_code)
            store_stock = self._parse_commodity_stock(commodity_stock)

            # validate commodities
            commodities = store_stock.keys()
            for c in commodities:
                if not c in dict(PartialTransaction.COMMODITIES):
                    raise FormValidationError('invalid_commodity', [c, ", ".join(dict(PartialTransaction.COMMODITIES).keys())])
                    
            for commodity in store_stock:
                try:
                    stock = Stock.objects.get(facility=store,commodity=commodity,time__year=message.date.year,time__month=message.date.month,time__day=message.date.day)
                    stock.balance = store_stock[commodity]
                    stock.save()
                except Stock.DoesNotExist:
                    data = {'facility': store, 'commodity': commodity,\
                        'balance': store_stock[commodity],
                        'time': message.date}
                    stock = Stock(**data)
                    stock.save()

                # TODO: It'll be nice to have the actual commodity names
                # instead of the codes
                commodity_list.append([commodity, store_stock[commodity]])

            # respond adequately
            message.respond('Thank you %s. Stock report received for %s Date=%s %s' % (reporter.first_name, store.name, message.date.strftime('%d/%m/%Y'), " ".join(["=".join(entry) for entry in commodity_list])))
        except Facility.DoesNotExist:
            message.respond(self.error_msgs['invalid_facility'] % origin)
        except FormValidationError, f:
            message.respond(f.msg)
        except Exception, e:
            self.debug(e)

        self.handled = True
        return

    def _parse_commodity_stock(self, s):
        ''' parses stock lists in the format 
            stock_commodity ::= string
            stock_quantity  ::= number
            stock_item      ::= stock_commodity stock_quantity
            stock_list      ::= stock_item* '''
        next_stock = ""
        stock = {}
        gen = tokenize.generate_tokens(StringIO(s).readline)
        for toknum, tokval, _, _, _ in gen:
            if not next_stock:
                next_stock = tokval
            else:
                if toknum == tokenize.NUMBER:
                    stock[next_stock] = tokval
                # reset the next_stock to parse the next stock
                next_stock = ""
        return stock

    @kw("(i|issue) from (slug) to (slug) (slug) (slug) (whatever) (numbers) (numbers) (whatever)")
    def issue(self, message, command, origin, destination, commodity, batch, expiry, qty, bal, vvmstatus):
        try:
            origin_facility = Facility.objects.get(code=origin)
        except Facility.DoesNotExist:
            message.respond(self.error_msgs['invalid_facility'] % origin, StatusCodes.OK)
            self.handled = True
            return True

        try:
            destination_facility = Facility.objects.get(code=destination)
        except Facility.DoesNotExist:
            message.respond(self.error_msgs['invalid_facility'] % destination, StatusCodes.OK)
            self.handled = True
            return True

        if not commodity in dict(PartialTransaction.COMMODITIES):
            message.respond(self.error_msgs['invalid_commodity'] % (
                commodity, ", ".join(dict(PartialTransaction.COMMODITIES).keys())), StatusCodes.OK)
            self.handled = True
            return True

        # partial transaction
        try:
            ten_hrs_ago = datetime.now() - timedelta(0, 36000, 0)
            pt = PartialTransaction.objects.get(origin__code=origin, destination__code=destination, commodity=commodity, batch=batch, type='I', time__gte=ten_hrs_ago, connection=PersistantConnection.from_message(message))
            pt.time = datetime.now()
            pt.expiry = self.convert_date(expiry)
            pt.amount = qty
            pt.stock = bal
            pt.save()
        except PartialTransaction.DoesNotExist:
            pt = PartialTransaction()
            pt.connection = PersistantConnection.from_message(message)
            pt.reporter = pt.connection.reporter
            pt.origin = Facility.objects.get(code=origin)
            pt.destination = Facility.objects.get(code=destination)
            pt.commodity = commodity
            pt.expiry = self.convert_date(expiry)
            pt.batch = batch
            pt.amount = qty
            pt.stock = bal
            pt.time = datetime.now()
            pt.type = 'I'
            pt.save()

        # stock for facility
        try:
            stock = Stock.objects.get(facility__code=origin, commodity__iexact=commodity)
            stock.balance = bal
            stock.save()
        except Stock.DoesNotExist:
            stock = Stock()
            stock.facility = Facility.objects.get(code=origin)
            stock.commodity = commodity
            stock.balance = bal
            stock.save()

        message.respond('Report received for VLM ISSUE: from %s to %s COMMODITY: %s, EXPIRY: %s, DOSES: %s, STOCK: %s, VVMSTATUS: %s' % (
            origin_facility, destination_facility, commodity, expiry, qty,
            bal, vvmstatus
        ), StatusCodes.OK)
        self.handled = True

    def convert_date(self, date):
        return datetime.strptime(date, '%d/%m/%Y').date()

    @kw("(r|receive) from (slug) to (slug) (slug) (slug) (whatever) (numbers) (numbers) (whatever)")
    def receive(self, message, command, origin, destination, commodity, batch, expiry, qty, bal, vvmstatus):
        try:
            origin_facility = Facility.objects.get(code=origin)
        except Facility.DoesNotExist:
            message.respond(self.error_msgs['invalid_facility'] % origin, StatusCodes.OK)
            self.handled = True
            return True

        try:
            destination_facility = Facility.objects.get(code=destination)
        except Facility.DoesNotExist:
            message.respond(self.error_msgs['invalid_facility'] % destination, StatusCodes.OK)
            self.handled = True
            return True

        if not commodity in dict(PartialTransaction.COMMODITIES):
            message.respond(self.error_msgs['invalid_commodity'] % (
                commodity, ", ".join(dict(PartialTransaction.COMMODITIES).keys())), StatusCodes.OK)
            self.handled = True
            return True

        # partial transaction
        try:
            ten_hrs_ago = datetime.now() - timedelta(0, 36000, 0)
            pt_receive = PartialTransaction.objects.get(origin__code=origin, destination__code=destination, commodity=commodity, batch=batch, type='R', time__gte=ten_hrs_ago, connection=PersistantConnection.from_message(message))
            pt_receive.time = datetime.now()
            pt_receive.expiry = self.convert_date(expiry)
            pt_receive.amount = qty
            pt_receive.stock = bal
            pt_receive.save()
        except PartialTransaction.DoesNotExist:
            pt_receive = PartialTransaction()
            pt_receive.connection = PersistantConnection.from_message(message)
            pt_receive.reporter = pt_receive.connection.reporter
            pt_receive.origin = Facility.objects.get(code=origin)
            pt_receive.destination = Facility.objects.get(code=destination)
            pt_receive.commodity = commodity
            pt_receive.expiry = self.convert_date(expiry)
            pt_receive.batch = batch
            pt_receive.amount = qty
            pt_receive.stock = bal
            pt_receive.time = datetime.now()
            pt_receive.type = 'R'
            pt_receive.save()

        # stock for facility
        try:
            stock = Stock.objects.get(facility__code=destination, commodity__iexact=commodity)
            stock.balance = bal
            stock.save()
        except Stock.DoesNotExist:
            stock = Stock()
            stock.facility = Facility.objects.get(code=destination)
            stock.commodity = commodity
            stock.balance = bal
            stock.save()

        # find matching previous partial transaction
        try:
            pt_issue = PartialTransaction.objects.get(origin=origin_facility, destination=destination_facility, commodity=commodity, batch=batch, type='I')

            # shipment
            try:
                shipment = Shipment.objects.get(origin=origin_facility, destination=destination_facility, commodity=commodity, batch=batch)
                shipment.expiry = self.convert_date(expiry)
                shipment.sent = pt_issue.time
                shipment.received = pt_receive.time
            except Shipment.DoesNotExist:
                shipment = Shipment()
                shipment.origin = origin_facility
                shipment.destination = destination_facility
                shipment.commodity = commodity
                shipment.expiry = self.convert_date(expiry)
                shipment.sent = pt_issue.time
                shipment.received = pt_receive.time
                shipment.batch = batch
                shipment.save()

            # transaction
            try:
                trans = Transaction.objects.get(shipment=shipment,receipt=pt_receive)
                trans.amount_received = qty
                trans.receipt = pt_receive
                trans.save()
            except Transaction.DoesNotExist:
                trans = Transaction()
                trans.amount_sent = pt_issue.amount
                trans.amount_received = pt_receive.amount
                trans.shipment = shipment
                trans.issue = pt_issue
                trans.receipt = pt_receive
                trans.save()

        except PartialTransaction.DoesNotExist:
            # no matching issue partial transaction found
            # could we possibly be trying to receive without an issue?
            pass

        message.respond('Report received for VLM RECEIVE: from %s to %s COMMODITY: %s, EXPIRY: %s, DOSES: %s, STOCK: %s, VVMSTATUS: %s' % (
            origin_facility, destination_facility, commodity, expiry, qty,
            bal, vvmstatus
        ), StatusCodes.OK)
        self.handled = True

    @kw('(whatever)')
    def default(self, message, text):
        message.respond("We didn't understand your message.", StatusCodes.OK)
        self.handled = True
