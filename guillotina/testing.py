# -*- coding: utf-8 -*-
from aiohttp.test_utils import make_mocked_request
from guillotina.auth.users import ROOT_USER_ID
from guillotina.browser import View
from guillotina.content import Resource
from guillotina.directives import index
from guillotina.directives import metadata
from guillotina.interfaces import IResource
from guillotina.schema import JSONField
from guillotina.schema import List
from zope.interface import implementer

import base64
import guillotina.patch  # noqa
import json
import requests


TESTING_PORT = 55001

TESTING_SETTINGS = {
    "databases": [
        {
            "db": {
                "storage": "DUMMY",
                "name": "guillotina"
            }
        },
    ],
    "port": TESTING_PORT,
    "static": [
        {"favicon.ico": "static/favicon.ico"}
    ],
    "creator": {
        "admin": "admin",
        "password": "admin"
    },
    "cors": {
        "allow_origin": ["*"],
        "allow_methods": ["GET", "POST", "DELETE", "HEAD", "PATCH"],
        "allow_headers": ["*"],
        "expose_headers": ["*"],
        "allow_credentials": True,
        "max_age": 3660
    },
    "root_user": {
        "password": "admin"
    },
    "utilities": []
}

QUEUE_UTILITY_CONFIG = {
    "provides": "guillotina.async.IQueueUtility",
    "factory": "guillotina.async.QueueUtility",
    "settings": {}
}


ADMIN_TOKEN = base64.b64encode(
    '{}:{}'.format(ROOT_USER_ID, TESTING_SETTINGS['root_user']['password']).encode(
        'utf-8')).decode('utf-8')
DEBUG = False

TERM_SCHEMA = json.dumps({
    'type': 'object',
    'properties': {
        'label': {'type': 'string'},
        'number': {'type': 'number'}
    },
})


class IExample(IResource):

    metadata('categories')

    index('categories', type='nested')
    categories = List(
        title='categories',
        default=[],
        value_type=JSONField(
            title='term',
            schema=TERM_SCHEMA)
    )


@implementer(IExample)
class Example(Resource):
    pass


class MockView(View):

    def __init__(self, context, conn, func):
        self.context = context
        self.request = make_mocked_request('POST', '/')
        self.request.conn = conn
        self.request._db_write_enabled = True
        self.func = func

    def __call__(self, *args, **kw):
        self.func(*args, **kw)


class AsyncMockView(View):

    def __init__(self, context, request, func):
        self.context = context
        self.request = request
        self.func = func

    async def __call__(self, *args, **kw):
        await self.func(*args, **kw)


class GuillotinaRequester(object):

    def __init__(self, uri=None, server=None):
        self.uri = uri
        self.server = server

    def __call__(
            self,
            method,
            path,
            params=None,
            data=None,
            authenticated=True,
            auth_type='Basic',
            headers={},
            token=ADMIN_TOKEN,
            accept='application/json'):

        settings = {}
        settings['headers'] = headers
        if accept is not None:
            settings['headers']['ACCEPT'] = accept
        if authenticated and token is not None:
            settings['headers']['AUTHORIZATION'] = '{} {}'.format(
                auth_type, token)

        settings['params'] = params
        settings['data'] = data
        operation = getattr(requests, method.lower(), None)
        if operation:
            if self.server is not None:
                resp = operation(self.server.make_url(path), **settings)
            else:
                resp = operation(self.uri + path, **settings)
            return resp
        return None
