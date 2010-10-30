#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import rapidsms
from rapidsms.parsers.keyworder import *
from models import *
from reporters.models import PersistantConnection, Reporter
from datetime import datetime, timedelta
from rapidsms.message import StatusCodes

class App(rapidsms.app.App):

    kw = Keyworder()
    error_msgs = {
        'invalid_location': "Sorry, I don't have the facility with the code: %s in my database. Please confirm and try again.",
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
        message.respond(['receive', 'issue'], StatusCodes.OK)
        self.handled = True

    @kw("(i|issue) from (slug) to (slug) (slug) (slug) (whatever) (numbers) (numbers) (whatever)")
    def issue(self, message, command, origin, destination, commodity, batch, expiry, qty, bal, vvmstatus):
        try:
            origin_facility = Facility.objects.get(code=origin)
        except Facility.DoesNotExist:
            message.respond(self.error_msgs['invalid_location'] % origin, StatusCodes.OK)
            self.handled = True
            return True

        try:
            destination_facility = Facility.objects.get(code=destination)
        except Facility.DoesNotExist:
            message.respond(self.error_msgs['invalid_location'] % destination, StatusCodes.OK)
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
            pt = PartialTransaction.objects.get(origin__code=origin, destination__code=destination, commodity=commodity, batch=batch, type='I', date__gte=ten_hrs_ago, connection=PersistantConnection.from_message(message))
            pt.date = datetime.now()
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
            pt.date = datetime.now()
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
            message.respond(self.error_msgs['invalid_location'] % origin, StatusCodes.OK)
            self.handled = True
            return True

        try:
            destination_facility = Facility.objects.get(code=destination)
        except Facility.DoesNotExist:
            message.respond(self.error_msgs['invalid_location'] % destination, StatusCodes.OK)
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
            pt_receive = PartialTransaction.objects.get(origin__code=origin, destination__code=destination, commodity=commodity, batch=batch, type='R', date__gte=ten_hrs_ago, connection=PersistantConnection.from_message(message))
            pt_receive.date = datetime.now()
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
            pt_receive.date = datetime.now()
            pt_receive.type = 'R'
            pt_receive.save()

        # stock for facility
        try:
            stock = Stock.objects.get(facility__code=destination)
            stock.balance = bal
            stock.save()
        except Stock.DoesNotExist:
            stock = Stock()
            stock.facility = Facility.objects.get(code=destination)
            stock.balance = bal
            stock.save()

        # find matching previous partial transaction
        try:
            pt_issue = PartialTransaction.objects.get(origin=origin_facility, destination=destination_facility, commodity=commodity, batch=batch, type='I')

            # shipment
            try:
                shipment = Shipment.objects.get(origin=origin_facility, destination=destination_facility, commodity=commodity, batch=batch)
                shipment.expiry = self.convert_date(expiry)
                shipment.sent = pt_issue.date
                shipment.received = pt_receive.date
            except Shipment.DoesNotExist:
                shipment = Shipment()
                shipment.origin = origin_facility
                shipment.destination = destination_facility
                shipment.commodity = commodity
                shipment.expiry = self.convert_date(expiry)
                shipment.sent = pt_issue.date
                shipment.received = pt_receive.date
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
