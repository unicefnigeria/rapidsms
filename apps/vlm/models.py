# vim: ai sts=4 ts=4 et sw=4
from django.db import models
from reporters.models import Reporter, PersistantConnection
from locations.models import Location, Facility

class PartialTransaction(models.Model):
    COMMODITIES = (
        ('01', 'AL'),
        ('02', 'BCG'),
        ('03', 'bOPV'),
        ('04', 'CSM'),
        ('05', 'DPT'),
        ('06', 'HepB'),
        ('07', 'Mama Kits'),
        ('08', 'mOPV1'),
        ('09', 'mOPV3'),
        ('10', 'MV'),
        ('11', 'Deworm'),
        ('12', 'Penta Vac'),
        ('13', 'SB'),
        ('14', 'SY500ml'),
        ('15', 'SY50ml'),
        ('16', 'SY2ml'),
        ('17', 'SY5ml'),
        ('18', 'tOPV'),
        ('19', 'TT'),
        ('20', 'VITA1'),
        ('21', 'VITA2'),
        ('22', 'YF'),
    )
    TRANSACTION_TYPES = (
        ('I', 'Issue'),
        ('R', 'Receipt'),
    )
    STATUS_TYPES = (
        ('P', 'Pending'),
        ('C', 'Confirmed'),
        ('A', 'Amended'),
    )
    FLAG_TYPES = (
        ('S', 'Reported stock does not match expected stock balance.'),
        ('U', 'Unregistered reporter.'),
    )

    reporter = models.ForeignKey(Reporter, blank=True, null=True, related_name='vlm_partialtransactions')
    connection = models.ForeignKey(PersistantConnection, blank=True, null=True, related_name="vlm_partialtransactions")
    origin = models.ForeignKey(Facility, related_name='origins')
    destination = models.ForeignKey(Facility, related_name='destinations')
    commodity = models.CharField(blank=True, null=True, max_length=10, choices=COMMODITIES)
    expiry = models.DateField(db_index=True)
    batch = models.CharField(max_length=15, blank=True, null=True, help_text="Waybill number")
    amount = models.PositiveIntegerField(blank=True, null=True, help_text="Amount of supply shipped")
    stock = models.PositiveIntegerField(blank=True, null=True, help_text="Amount of stock present at location.")
    time = models.DateTimeField()
    # this could be a boolean, but is more readable this way
    type = models.CharField(max_length=1, choices=TRANSACTION_TYPES)
    status = models.CharField(max_length=1, choices=STATUS_TYPES)
    flag = models.CharField(blank=True, null=True, max_length=1, choices=FLAG_TYPES)
    
    def _get_transaction(self):
        if self.status == 'C':
            if self.type == 'I':
                return Transaction.objects.filter(issue__pk=self.pk)
            elif self.type == 'R':
                return Transaction.objects.filter(receipt__pk=self.pk)

    # there should only ever be one transaction for a partial transaction,
    # but since this returns a queryset, the property name is plural
    transactions = property(_get_transaction)

    class Meta:
        ordering = ['-status']


class Shipment(models.Model):
    '''Stores vaccine shipments'''
    origin = models.ForeignKey(Facility, related_name='vlm_shipments_origin')
    destination = models.ForeignKey(Facility, related_name='vlm_shipments_destination')
    commodity = models.CharField(blank=True, null=True, max_length=10, choices=PartialTransaction.COMMODITIES)
    expiry = models.DateField(db_index=True)
    sent = models.DateTimeField()
    received = models.DateTimeField()
    batch = models.CharField(max_length=15, blank=True, null=True, help_text="Batch number")

    def __unicode__(self):
        return "%s (%s) ==> %s (%s)" % (self.origin.name, self.sent.date(), self.destination.name, self.received.date())

class Stock(models.Model):
    facility = models.ForeignKey(Facility, related_name="stock")
    commodity = models.CharField(blank=True, null=True, max_length=10, choices=PartialTransaction.COMMODITIES)
    balance = models.PositiveIntegerField(blank=True, null=True, help_text="Amount of supply at warehouse")
    time = models.DateTimeField()

    def __unicode__(self):
        return "%s (%s doses)" % (self.facility, self.balance)


class Transaction(models.Model):
    FLAG_TYPES = (
        ('A', 'Mis-matched amounts'),
        ('W', 'Mis-matched waybill'),
        ('I', 'Incorrect. Has been replaced.'),
    )

    amount_sent  = models.PositiveIntegerField(blank=True, null=True, help_text="Amount of supply shipped from origin")
    amount_received = models.PositiveIntegerField(blank=True, null=True, help_text="Amount of supply received by destination")
    shipment = models.ForeignKey(Shipment)
    issue = models.ForeignKey(PartialTransaction, related_name='issues')
    receipt = models.ForeignKey(PartialTransaction, related_name='receipts')
    flag = models.CharField(blank=True, null=True, max_length=1, choices=FLAG_TYPES)
    time = models.DateTimeField()

    def __unicode__(self):
        return "%s (%s) ==> %s (%s)" % (self.shipment.origin.name, self.amount_sent, self.shipment.destination.name, self.amount_received)

