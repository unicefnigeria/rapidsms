# vim: ai sts=4 sw=4 et ts=4
import rapidsms
from rapidsms.webui import settings
from models import Application

class App (rapidsms.app.App):
    def start (self):
        ''' This method was defined to automatically enumerate the list of apps and store them in the Application 
            model so they can be specified in the different campaigns.'''
        for app in settings.RAPIDSMS_APPS.keys():
            try:
                appObj = Application.objects.get(name=app)
            except Application.DoesNotExist:
                appObj = Application(name=app)
                if settings.RAPIDSMS_APPS[app].has_key('title'):
                    appObj.description = settings.RAPIDSMS_APPS[app]['title']
                appObj.save()

