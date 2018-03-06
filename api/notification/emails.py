'''
Purpose: holds all the emails + email logic for espa-api
Author: David V. Hill
'''

import datetime
import re

from api.notification import contact_footer

from cStringIO import StringIO

from email.mime.text import MIMEText
from smtplib import SMTP, SMTPServerDisconnected

from validate_email import validate_email

from api.domain.order import Order
from api.domain.scene import Scene
from api.providers.configuration.configuration_provider import ConfigurationProvider

from api.system.logger import ilogger as logger

config = ConfigurationProvider()


class Emails(object):

    def __init__(self):
        self.status_base_url = config.url_for('status_url')

    def __send(self, recipient, subject, body):
        return self.send_email(recipient=recipient, subject=subject, body=body)

    def __order_status_url(self, orderid):
        _base_url = self.status_base_url
        _base_url = _base_url.replace("status", "order-status")
        return ''.join([_base_url, '/', orderid])

    def send_email(self, recipient, subject, body):
        '''Sends an email to a receipient on the behalf of espa'''

        def _validate(email):
            if not validate_email(email):
                raise TypeError("Invalid email address provided:%s" % email)

        to_header = recipient
        if isinstance(recipient, (list, tuple)):
            for r in recipient:
                _validate(r)
            to_header = ','.join(recipient)
        elif isinstance(recipient, basestring):
            _validate(recipient)
            recipient = [recipient]
        else:
            raise ValueError("Unsupported datatype for recipient:%s"
                             % type(recipient))

        logger.debug('Sending email: {} {}'.format(recipient, subject))
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['To'] = to_header
        msg['From'] = config.get('email.espa_address')
        s = SMTP(host=config.get('email.espa_server'), timeout=3)
        s.sendmail(msg['From'], recipient, msg.as_string())
        s.quit()

        return True

    def send_gzip_error_email(self, product_id):
        '''Sends an email to our people telling them to reprocess
           a bad gzip on the online cache'''

        address_block = config.get('email.corrupt_gzip_notification_list')
        addresses = address_block.split(',')

        subject = "Corrupt gzip detected: %s" % product_id

        m = list()
        m.append("This is an automated email, please do not reply.\n\n ")
        m.append("A corrupt gzip has been detected on the online cache. ")
        m.append("Please reprocess this at your earliest convienience.\n\n")
        m.append("Thanks!\n\n")
        m.append("The LSRD Team")

        email_msg = ''.join(m)

        return self.__send(recipient=addresses,
                           subject=subject,
                           body=email_msg)

    def send_all_initial(self, orders):
        '''Finds all the orders that have not had their initial emails sent and
        sends them'''
        for o in orders:
            if not o.initial_email_sent:
                try:
                    self.send_initial(o.orderid)
                    o.update('initial_email_sent', datetime.datetime.now())
                except SMTPServerDisconnected:
                    logger.error('Unable to send initial email: {}'
                                 .format(o.orderid))
        return True

    def send_initial(self, order_id):
        if isinstance(order_id, Order):
            order = order_id
        else:
            order = Order.find(order_id)

        if not isinstance(order, Order):
            msg = 'order must be str of orderid, int of pk or instance of Order'
            raise TypeError(msg)

        email = order.user_email()
        url = self.__order_status_url(order.orderid)


        m = list()
        m.append("Thank you for your order.\n\n")
        m.append("%s has been received and is currently " % order.orderid)
        m.append("being processed.  ")
        m.append("Another email will be sent when this order is complete.\n\n")
        m.append("You may view the status of your order and download ")
        m.append("completed products directly from %s\n\n" % url)
        m.append("Requested products\n")
        m.append("-------------------------------------------\n")

        scenes = order.scenes()

        for product in scenes:
            name = product.name

            if name == 'plot':
                name = "Plotting & Statistics"
            m.append("%s\n" % name)

        m.append(contact_footer)
        email_msg = ''.join(m)
        subject = 'USGS ESPA Processing order %s received' % order.orderid

        return self.__send(recipient=email, subject=subject, body=email_msg)

    def send_completion(self, order):
        if not isinstance(order, Order):
            order = Order.find(order)

        messages = {'complete': ['{orderid} is now complete and can be downloaded from {url}', '', '',
                                 'For large orders, the ESPA Bulk Downloader is available {bdurl}', '', '',
                                 'This order will remain available for 10 days. Any data not downloaded '
                                 'will need to be reordered after this time.', '', '',
                                 'Please contact Customer Services at 1-800-252-4547 or '
                                 'email custserv@usgs.gov with any questions.', '', '',
                                 'Requested products', '-------------------------------------------'
                                 ],
                    'unsuccessful': ['{orderid} was unsuccessful, and the reason can be found at {url}', '', '',
                                     'This order will remain available for 10 days.', '', '',
                                     'Please contact Customer Services at 1-800-252-4547 or '
                                     'email custserv@usgs.gov with any questions.', '', '',
                                     'Requested products', '-------------------------------------------'
                                     ]
                    }

        scenes = order.scenes({'status': 'complete'})
        status = 'complete' if len(scenes) > 0 else 'unsuccessful'
        outmessage = messages[status]

        email = order.user_email()
        url = self.__order_status_url(order.orderid)
        bdl_url = "https://github.com/USGS-EROS/espa-bulk-downloader"

        scenes = order.scenes()
        pbs = order.products_by_sensor()

        for product in scenes:
            if product.sensor_type == 'plot':
                line = "plotting & statistics"
            else:
                if product.status == 'complete':
                    line = "{}: {}".format(product.name, ", ".join(pbs[product.name]))
                else:
                    line = "{}: {}".format(product.name, product.note.strip())
            outmessage.append(line)

        outmessage.append(contact_footer)
        body = '\n'.join(outmessage).format(url=url, bdurl=bdl_url, orderid=order.orderid)
        subject = 'USGS ESPA Processing for {} {}'.format(order.orderid, status)

        return self.__send(recipient=email, subject=subject, body=body)

    def send_order_cancelled_email(self, order_id):
        if isinstance(order_id, Order):
            order = order_id
        else:
            order = Order.find(order_id)

        if not isinstance(order, Order):
            msg = 'order must be str of orderid, int of pk or instance of Order'
            raise TypeError(msg)

        email = order.user_email()
        orderid = str(order.orderid).strip()
        n_scenes_cancelled = len(order.scenes({'status': 'cancelled'}))
        n_scenes_running = len(order.scenes()) - n_scenes_cancelled

        email_template = (
            "Your order {orderid} has been cancelled.\n"
            "A total of {n_scenes} scenes have been stopped.\n"
            "{running_message}\n\n\n\n"
            "Please contact Customer Services at 1-800-252-4547 or "
            "email custserv@usgs.gov with any questions.\n\n"
            "This is an automated email.\n\n"
            "-------------------------------------------\n\n"
            "{contact_footer}"
        )
        running_message = ('({n} scenes could not be immediately halted, but '
                           'will finish in a cancelled state)'
                           .format(n=n_scenes_running)
                           if n_scenes_running else '')
        information = dict(n_scenes=n_scenes_cancelled,
                           running_message=running_message,
                           contact_footer=contact_footer,
                           orderid=orderid)
        email_msg = email_template.format(**information)
        subject = ('USGS ESPA Processing order {orderid} cancelled'
                   .format(orderid=orderid))

        return self.__send(recipient=email, subject=subject, body=email_msg)

    def send_purge_report(self, start_capacity, end_capacity, orders):
        buffer = StringIO()
        for order in orders:
            buffer.write('{0}\n'.format(order))
        order_str = buffer.getvalue()
        buffer.close()

        body = '''===================================
        Disk usage before purge
        Capacity:{start_capacity} Used:{start_used} Available:{start_available} Percent Used:{start_percent_free}

        ===================================
        Disk usage after purge
        Capacity:{end_capacity} Used:{end_used} Available:{end_available} Percent Used:{end_percent_free}

        ===================================
        Purged orders
          {purged_orders}
        ========== End of report ==========
        '''.format(start_capacity=start_capacity['capacity'],
                   start_used=start_capacity['used'],
                   start_available=start_capacity['available'],
                   start_percent_free=start_capacity['percent_used'],
                   end_capacity=end_capacity['capacity'],
                   end_used=end_capacity['used'],
                   end_available=end_capacity['available'],
                   end_percent_free=end_capacity['percent_used'],
                   purged_orders=order_str)

        now = datetime.datetime.now()
        subject = 'Purged orders for {month}-{day}-{year}'.format(day=now.day,
                                                                  month=now.month,
                                                                  year=now.year)
        recipients = config.get('email.purge_report_list').split(',')
        return self.__send(recipient=recipients, subject=subject, body=body)

def send_purge_report(start_capacity, end_capacity, orders):
    return Emails().send_purge_report(start_capacity, end_capacity, orders)

