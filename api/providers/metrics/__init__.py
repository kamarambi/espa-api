import abc

from api.providers.metrics.metrics_provider import Metrics


class MetricsProviderInterface(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def list_metrics(self):
        pass

    @abc.abstractmethod
    def metric_info(self, name):
        pass

    @abc.abstractmethod
    def read_metric(self, name, args):
        pass


class MockMetricsProvider(MetricsProviderInterface):

    def list_metrics(self):
        pass

    def metric_info(self, name):
        pass

    def read_metric(self, name, args):
        pass


class MetricsProvider(MetricsProviderInterface):
    metrics = Metrics()

    def list_metrics(self):
        return self.metrics.list_metrics(self.metrics.queries)

    def metric_info(self, name):
        return self.metrics.metric_info(self.metrics.queries.get(name),
                                        self.metrics.info_keys)

    def read_metric(self, name, args):
        sql_statement = self.metrics.build_sql(self.metrics.queries.get(name),
                                               args)
        result = self.metrics.run_sql(sql_statement, args)
        return self.metrics.format_result(self.metrics.queries.get(name), result)
