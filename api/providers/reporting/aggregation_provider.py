import os

import yaml

from api import __location__
from api.util.dbconnect import DBConnectException, db_instance
from api.system.logger import ilogger as logger


AGGREGATE_SQL_QUERIES = yaml.load(open(os.path.join(__location__, 'providers/reporting/aggregations.yaml')))


class AggregationProvider(object):
    def __init__(self):
        pass

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
        with db_instance() as db:
            log_sql = db.cursor.mogrify(query, args_formatted)
            logger.debug(log_sql)
            db.select(query, args_formatted)
            return self.format_response(db.dictfetchall, aggkey=groupby, aggname=aggname)
