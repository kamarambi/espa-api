import abc

from api.providers.metrics.metrics_provider import Metrics

class MetricsProviderInterface(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def list_metrics(self):
        pass

    @abc.abstractmethod
    def read_metric(self, name, **kwargs):
        pass

    @abc.abstractproperty
    def metrics():
        pass


class MockMetricsProvider(MetricsProviderInterface):

    def list_metrics(self):
        pass

    def read_metric(self, name, **kwargs):
        pass


class MetricsProvider(MetricsProviderInterface):
    metrics = Metrics()

    def list_metrics(self):
        return self.metrics.list_metrics(self.metrics.queries)

    def metric_info(self, name):
        return self.metrics.metric_info(self.metrics.queries.get(name),
                                        self.metrics.info_keys)

    def read_metric(self, name, **kwargs):
        pass