import os
import datetime
import dateutil.relativedelta

import yaml

from api import __location__
from api.system.logger import ilogger as logger
from api.providers.configuration.configuration_provider import ConfigurationProvider
from api.providers.reporting.aggregation_provider import AggregationProvider
from api.notification import emails

config = ConfigurationProvider()
METRICS_BOILERS = yaml.load(open(os.path.join(__location__, 'providers/metrics/report_boilerplates.yaml')))


class MetricsProvider(object):
    def __init__(self):
        self.aggregations = AggregationProvider()

    def send_metrics_report(self, period, activity):
        email_list = config.get('email.metrics.{}.{}'.format(activity, period)).split(',')
        period_rng = self.convert_relative_period(period)
        body = '# Report range: {start_date} - {end_date}\n'.format(**period_rng) + '=' * 50 + '\n\n'
        boilers = METRICS_BOILERS[activity]

        if activity == 'users':
            info_dict = self.gather_interfaces_info(sensor_type=['landsat', 'modis'], **period_rng)
            body += boilers['interfaces'].format(**info_dict) + '\n\n'
            info_dict = self.gather_top_info(sensor_type=['landsat', 'modis'], **period_rng)
            body += boilers['top'].format(**info_dict) + '\n\n'

        subject = 'ESPA STAFF | {} {} report'.format(period, activity)
        emails.Emails().send_email(email_list, subject=subject, body=body)
        return True

    @staticmethod
    def convert_relative_period(period, fmt='%Y-%m-%d %H:%M:%S'):
        starters = {'daily': dateutil.relativedelta.relativedelta(days=-1),
                    'weekly': dateutil.relativedelta.relativedelta(weeks=-1),
                    'monthly': dateutil.relativedelta.relativedelta(months=-1),
                    'yearly': dateutil.relativedelta.relativedelta(years=-1)
                    }
        period_rng = {'start_date': datetime.datetime.utcnow() + starters[period],
                      'end_date': datetime.datetime.utcnow()}
        return {k: v.strftime(fmt) for k, v in period_rng.items()}

    def gather_interfaces_info(self, **kwargs):
        retval = dict(who='ALL', tot_unique='',
                      scenes_month='', scenes_usgs='', scenes_non='',
                      orders_month='', orders_usgs='', orders_non='')

        info = self.aggregations.count('orders', kwargs)
        logger.debug(info)
        retval['orders_month'] = sum(info.values())
        retval['orders_usgs'] = sum(v for k, v in info.items() if k.endswith('@usgs.gov'))
        retval['orders_non'] = sum(v for k, v in info.items() if not k.endswith('@usgs.gov'))
        retval['tot_unique'] = len(info.keys())

        info = self.aggregations.count('scenes', kwargs)
        retval['scenes_month'] = sum(info.values())
        retval['scenes_usgs'] = sum(v for k, v in info.items() if k.endswith('@usgs.gov'))
        retval['scenes_non'] = sum(v for k, v in info.items() if not k.endswith('@usgs.gov'))

        return retval

    def gather_top_info(self, **kwargs):
        retval = dict(itertext='\n')
        info = self.aggregations.count('scenes', kwargs)
        info = sorted(info.items(), key=lambda x: x[1])
        retval['itertext'] += '\n'.join(': '.join(map(str, i)) for i in info[:10])
        return retval
