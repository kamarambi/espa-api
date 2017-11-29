"""
    Core monthly/daily/etc. report generation
"""
import os
from collections import namedtuple

import yaml

from api import __location__



MetricsQuery = namedtuple('MetricsQuery', ['description', 'display_name',
                                           'query', 'where', 'optionals',
                                           'required','returns'])


class Reports(object):
    @staticmethod
    def _read_templates():
        pass


class MetricsException(Exception):
    pass


class Metrics(object):
    def __init__(self):
        self.queries_fname = os.path.join(__location__,
                                          'providers/metrics/queries.yaml')
        self.queries = self.read_sqls(self.queries_fname)
        self.info_keys = ['returns', 'display_name',
                          'description', 'optionals', 'required']

    @staticmethod
    def read_sqls(fname):
        return {k: MetricsQuery(**v)
                for k, v in yaml.load(open(fname, 'r')).items()}

    @staticmethod
    def list_metrics(queries):
        return {k: v.description for k, v in queries.items()}

    @staticmethod
    def metric_info(query, keys):
        return {k: v if isinstance(v, basestring) else v.keys()
                for k, v in query._asdict().items() if k in keys}

    @staticmethod
    def build_sql(query, data):
        delta = set(query.required.keys()) - set(data.keys())
        if delta:
            msg = 'Missing required arguments: {}'.format(list(delta))
            raise MetricsException(msg)

        present = list(set(query.optionals.keys()) & set(data.keys()))
        where = ' AND '.join([query.where] +
                            [query.required[k] for k in query.required.keys()] +
                            [query.optionals[k] for k in present])

        sql_query = query.query.replace('{{WHERE}}', where)
        return sql_query
