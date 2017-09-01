""" Module to glue interfaces to implementations """

from api.providers.inventory.inventory_provider import MockInventoryProvider, InventoryProvider
from api.providers.metrics import MockMetricsProvider
from api.providers.ordering import MockOrderingProvider
from api.providers.ordering.ordering_provider import OrderingProvider
from api.providers.production.production_provider import ProductionProvider
from api.providers.reporting.reporting_provider import ReportingProvider
from api.providers.validation import MockValidationProvider
from api.providers.validation.validictory import ValidationProvider
from api.providers.configuration.configuration_provider import ConfigurationProvider
from api.providers.administration.administration_provider import AdministrationProvider
from api.providers.reporting.aggregation_provider import AggregationProvider
from api.providers.metrics.metrics_provider import MetricsProvider


class DefaultProviders(object):

    ordering = OrderingProvider()

    validation = ValidationProvider()

    metrics = MetricsProvider()

    inventory = InventoryProvider()

    production = ProductionProvider()

    configuration = ConfigurationProvider()

    reporting = ReportingProvider()

    administration = AdministrationProvider()

    aggregation = AggregationProvider()


class MockProviders(object):
    ordering = MockOrderingProvider()

    validation = MockValidationProvider()

    metrics = MockMetricsProvider()

    inventory = MockInventoryProvider()
