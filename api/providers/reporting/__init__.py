import abc

from api.providers.reporting.reporting_provider import Reporting

class ReportingProviderInterfaceV0(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def listing(self, frequency, name):
        pass

    @abc.abstractmethod
    def run(self, frequency, name, data):
        pass


class ReportingProvider(ReportingProviderInterfaceV0):

    reporting = Reporting()

    def listing(self, frequency, name):
        return self.reporting.list_reports(self.reporting.reports,
                                           frequency, name)

    def run(self, frequency, name, data):
        pass
