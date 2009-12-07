# vim: et ai sts=4 sw=4 ts=4
import rapidsms
import re
# requires python-dateutil to work
try:
    from dateutil.parser import *
except ImportError:
    raise ImportError('python-dateutil is required for this app to work.')

class App (rapidsms.app.App):
    def start (self):
        """Configure your app in the start phase."""
        self.pattern = re.compile(r"(?P<date>(\d+[,./-;:]\d+|\d+[,./-;:]\d+[,./-;:]\d+))$")

    def parse (self, message):
        '''The purpose of this method is to look for any strings resembling
        a date string eg. 7/12/2009, 7/12, 7-12-2009, 7-12, etc and use that
        to configure the date of the message. This is essentially to cater for
        reports that may come in late.'''
        last_token = re.split("\s+", message.text.strip())[-1]
        # Match if similar to a date
        if (self.pattern.match(last_token)):
            # Extract the date and parse
            msg_date_string = self.pattern.match(last_token).group(1)
            msg_date = parse(msg_date_string, dayfirst=True)

            # If we parsed it successfully, then let's set the message date
            if (msg_date):
                self.info("setting message date to %s" % msg_date)
                message.date = msg_date

                # Remove the date from the message
                self.info("previous message: %s" % message.text.strip())
                msgtxt = " ".join(re.split("\s+", message.text.strip())[0:-1])
                message.text = msgtxt
                self.info("new message: %s" % message.text)

