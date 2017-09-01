import os
import json
import hashlib

import yaml

from api import __location__
from api.util.dbconnect import DBConnectException, db_instance
from api.system.logger import ilogger as logger
from api.providers.caching.caching_provider import CachingProvider


AGGREGATE_SQL_QUERIES = yaml.load(open(os.path.join(__location__, 'providers/reporting/aggregations.yaml')))
cache = CachingProvider()


class AggregationProvider(object):
    def __init__(self):
        pass

    @staticmethod
    def __query(query, args):
        hashquery = query + json.dumps(args, sort_keys=True)
        cache_key = hashlib.sha256(hashquery).hexdigest()
        logger.debug(cache_key)
        data = cache.get(cache_key)
        if not data:
            with db_instance() as db:
                log_sql = db.cursor.mogrify(query, args)
                logger.debug(log_sql)
                db.select(query, args)
                data = db.dictfetchall
            cache.set(cache_key, data)
        return data

    @staticmethod
    def format_response(dictfetchall, aggkey='email', aggname='count'):
        stat = dict()
        for row in dictfetchall:
            stat[row[aggkey]] = row[aggname]
        return stat

    def count(self, groupname, args, aggname='count'):
        sql_obj = AGGREGATE_SQL_QUERIES[aggname][groupname]
        if sql_obj is None:
            return False
        logger.debug(sql_obj)
        query, groupby = (sql_obj['query'], sql_obj['groupby'])

        args_formatted = {k.upper(): v for k, v in args.items()}
        args_formatted = {k: v if not isinstance(v, list) else tuple(v) for k, v in args_formatted.items()}
        return self.format_response(self.__query(query, args_formatted))