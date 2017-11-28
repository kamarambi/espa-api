# Tie together the urls for functionality

import os
import sys

from flask import Flask, request, make_response, jsonify
from flask.ext.restful import Api, Resource, reqparse, fields, marshal

from api.providers.configuration.configuration_provider import ConfigurationProvider
from api.util import api_cfg
from api.system.logger import ilogger as logger

from http_user import Index, VersionInfo, AvailableProducts, ValidationInfo,\
    ListOrders, Ordering, UserInfo, ItemStatus, BacklogStats, PublicSystemStatus

from http_production import ProductionVersion, ProductionConfiguration, ProductionOperations, ProductionManagement

from http_admin import Reports, SystemStatus, OrderResets, ProductionStats
from http_json import MessagesResponse, BadRequestResponse, SystemErrorResponse

config = ConfigurationProvider()

app = Flask(__name__)
app.secret_key = api_cfg('config').get('key')


@app.errorhandler(404)
def page_not_found(e):
    errors = MessagesResponse(errors=['{} not found on the server'
                                      .format(request.path)],
                              code=404)
    return errors()


@app.errorhandler(IndexError)
def no_results_found(e):
    return MessagesResponse(warnings=['No results found.'],
                            code=200)()

@app.errorhandler(Exception)
def internal_server_error(e):
    logger.critical('Internal Server Error: {}'.format(e))
    return SystemErrorResponse()

transport_api = Api(app)

resources = [
    # USER facing functionality
    {
        "operator": "Index",
        "paths": ["/"]
    }, {
        "operator": "VersionInfo",
        "paths": ['/api', '/api/', '/api/v<version>', '/api/v<version>/']
    }, {
        "operator": "UserInfo",
        "paths": ['/api/v<version>/user', '/api/v<version>/user/']
    }, {
        "operator": "AvailableProducts",
        "paths": [
            '/api/v<version>/available-products/<prod_id>',
            '/api/v<version>/available-products',
            '/api/v<version>/available-products/']
    }, {
        "operator": "ValidationInfo",
        "paths": [
            '/api/v<version>/projections',
            '/api/v<version>/formats',
            '/api/v<version>/resampling-methods',
            '/api/v<version>/order-schema',
            '/api/v<version>/product-groups']
    }, {
        "operator": "ListOrders",
        "paths": [
            '/api/v<version>/list-orders',
            '/api/v<version>/list-orders/',
            '/api/v<version>/list-orders/<email>',
            '/api/v<version>/list-orders-feed/<email>']
    }, {
        "operator": "Ordering",
        "paths": [
            '/api/v<version>/order',
            '/api/v<version>/order/',
            '/api/v<version>/order/<ordernum>',
            '/api/v<version>/order-status/<ordernum>']
    }, {
        "operator": "ItemStatus",
        "paths": [
            '/api/v<version>/item-status',
            '/api/v<version>/item-status/<orderid>',
            '/api/v<version>/item-status/<orderid>/<itemnum>']
    }, {
        "operator": "BacklogStats",
        "paths": [
            '/api/v<version>/info/backlog']
    }, {
        "operator": "PublicSystemStatus",
        "paths": [
            '/api/v<version>/info/status']
    }, {
        "operator": "Reports",
        "paths": [
            '/api/v<version>/reports/',
            '/api/v<version>/reports/<name>/',
            '/api/v<version>/statistics/',
            '/api/v<version>/statistics/<name>',
            '/api/v<version>/aux_report/<group>/',
            '/api/v<version>/aux_report/<group>/<year>']
    }, {
        "operator": "SystemStatus",
        "paths": [
            '/api/v<version>/system-status',
            '/api/v<version>/system-status-update',
            '/api/v<version>/system/config']

    }, {
        "operator": "OrderResets",
        "paths": [
            '/api/v<version>/error_to_submitted/<orderid>',
            '/api/v<version>/error_to_unavailable/<orderid>']
    # PRODUCTION facing functionality
    }, {
        "operator": "ProductionVersion",
        "paths": [
            '/production-api',
            '/production-api/v<version>']
    }, {
        "operator": "ProductionOperations",
        "paths": [
            '/production-api/v<version>/products',
            '/production-api/v<version>/<action>',
            '/production-api/v<version>/handle-orders',
            '/production-api/v<version>/queue-products']
    }, {
        "operator": "ProductionStats",
        "paths": [
            '/production-api/v<version>/statistics/<name>',
            '/production-api/v<version>/multistat/<name>']
    }, {
        "operator": "ProductionManagement",
        "paths": [
            '/production-api/v<version>/handle-orphans',
            '/production-api/v<version>/reset-status']
    }, {
        "operator": "ProductionConfiguration",
        "paths": [
            '/production-api/v<version>/configuration/<key>']
    }
]

def get_resource(name):
    return reduce(getattr, name.split("."), sys.modules[__name__])

for res in resources:
    transport_api.add_resource(get_resource(res['operator']), *res['paths'])


if __name__ == '__main__':

    debug = False
    if 'ESPA_DEBUG' in os.environ and os.environ['ESPA_DEBUG'] == 'True':
        debug = True
    app.run(debug=debug)
