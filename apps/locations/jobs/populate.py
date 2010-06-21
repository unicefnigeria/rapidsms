from django_extensions.management.jobs import BaseJob
from locations.models import *
import sys
import os
from os.path import join, dirname

class Job(BaseJob):
    help = "Update locations with population data (uses .popn files)"

    def populate(self, filename):
        if os.access(join(os.getcwd(), filename), os.F_OK):
            filename = join(os.getcwd(), filename)
        elif os.access(join(dirname(__file__), filename), os.F_OK):
            filename = join(dirname(__file__), filename)
        else:
            raise IOError, "File does not exist or read access denied"

        f = open(filename)
        for line in f.readlines():
            code, popn = line.split(",")
            code = code.strip('"')
            popn = popn.strip("\n")
            try:
                loc = Location.objects.get(code=code)
                loc.population = popn
                loc.save()
                print "%s, %s" % (loc.name, popn)
            except Location.DoesNotExist:
                print "Location with code %d not found." % code

    def execute(self):
        print sys.argv
        files = os.listdir(".")
        newfiles = []
        for file in files:
            if file.endswith(".popn"):
                self.populate(file)
