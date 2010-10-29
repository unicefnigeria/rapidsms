from rapidsms.tests.scripted import TestScript
import form.app as form_app
import bednets.app as  bednets_app
from reporters.models import *
import reporters.app as reporter_app
from app import App
from models import *

class TestApp (TestScript):
    apps = (reporter_app.App, App, form_app.App, bednets_app.App)
    # the test_backend script does the loading of the dummy backend that allows reporters
    # to work properly in tests
    fixtures = ['nigeria_llin', 'kano_locations', 'kano_test_facilities', 'test_backend']
    
    def setUp(self):
        TestScript.setUp(self)

    def testScript(self):
        reports = """
            8005552222 > llin register 20 sm mister sender 
            8005552222 < Hello mister! You are now registered as Stock manager at KANO State.
            8005551111 > llin register 2027 sm mister recipient
            8005551111 < Hello mister! You are now registered as Stock manager at KURA LGA.
            8005552222 > vlm issue from 20 to 2001 vita 0022 23/12/2010 800 1600 001
            8005552222 < Report received for VLM ISSUE: from KANO to AJINGI COMMODITY: vita, EXPIRY: 23/12/2010, DOSES: 800, STOCK: 1600, VVMSTATUS: 001
            8005551111 > vlm receive from 20 to 2001 vita 0022 23/12/2010 800 1000 001
            8005551111 < Report received for VLM RECEIVE: from KANO to AJINGI COMMODITY: vita, EXPIRY: 23/12/2010, DOSES: 800, STOCK: 1000, VVMSTATUS: 001
            """
        self.runScript(reports)

        sender = Reporter.objects.get(alias="msender")
        recipient = Reporter.objects.get(alias="mrecipient")

        issue = PartialTransaction.objects.get(origin__name__iexact="KANO",\
           destination__name__iexact="AJINGI", batch="0022",\
           type="I", reporter__pk=sender.pk)

        receipt = PartialTransaction.objects.get(origin__name__iexact="KANO",\
           destination__name__iexact="AJINGI", batch="0022",\
           type="R", reporter__pk=recipient.pk)
        
        origin_stock = Stock.objects.get(facility__name__iexact="KANO")
        dest_stock = Stock.objects.get(facility__name__iexact="AJINGI")

        shipment = Shipment.objects.get(origin__name__iexact="KANO",\
            destination__name__iexact="AJINGI", commodity__iexact="vita",\
            batch="0022")
        
        # stocks created with correct balance
        self.assertEqual(issue.stock, origin_stock.balance)
        self.assertEqual(receipt.stock, dest_stock.balance)
