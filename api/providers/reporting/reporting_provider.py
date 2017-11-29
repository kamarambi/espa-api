"""
    Frequent reporting of period-grouped Metrics
"""
import os
import copy
import datetime
from collections import namedtuple

import yaml
from dateutil.relativedelta import relativedelta

from api import __location__
from api.providers.metrics import MetricsProvider
from api.util.dbconnect import DBConnectException, db_instance
from api.system.logger import ilogger as logger


TimePeriod = namedtuple('TimePeriod', ['start_date', 'stop_date'])
MetricsReport = namedtuple('MetricsReport',
                           ['frequency', 'values', 'description',
                            'optionals',  'template'])


class Aggregation(object):
    now = datetime.datetime.now()
    groups = {
        'hour':  (relativedelta(hours=-1),
                  now.replace(minute=0, second=0, microsecond=0)),
        'day':   (relativedelta(days=-1),
                  now.replace(hour=0, minute=0, second=0, microsecond=0)),
        'month': (relativedelta(months=-1),
                  now.replace(day=1, hour=0, minute=0, second=0, microsecond=0))
    }

    @staticmethod
    def step(group):
        return TimePeriod([self.groups[group][1] + self.groups[group][0],
                           self.groups[group][1]])


class ReportingProviderException(Exception):
    pass


class Reporting(object):
    metrics = MetricsProvider()
    agg = Aggregation()
    reports_fname = os.path.join(__location__,
                                 'providers/reporting/reports.yaml')

    def __init__(self, fname=None):
        self.reports_fname = fname or self.reports_fname
        self.reports = {k: MetricsReport(**v) for k, v
                        in yaml.load(open(self.reports_fname, 'r')).items()}

    @staticmethod
    def list_reports(reports, frequency=None, name=None):
        if frequency is None:
            return list(set([x for v in reports.values()
                             for x in v.frequency]))
        elif name is None:
            return {k: v.description
                    for k, v in reports.items() if frequency in v.frequency}
        else:
            return reports[name]
