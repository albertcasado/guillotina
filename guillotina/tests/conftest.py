# -*- coding: utf-8 -*-
from guillotina.component import getUtility
from guillotina.content import load_cached_schema
from guillotina.factory import make_app
from guillotina.interfaces import IApplication
from guillotina.testing import ADMIN_TOKEN
from guillotina.testing import TESTING_SETTINGS
from guillotina.tests.utils import get_mocked_request
from time import sleep

import aiohttp
import asyncio
import copy
import docker
import json
import os
import psycopg2
import pytest


IS_TRAVIS = 'TRAVIS' in os.environ

IMAGE = 'postgres:9.6'
CONTAINERS_FOR_TESTING_LABEL = 'testingaiopg'
PG_SETTINGS = copy.deepcopy(TESTING_SETTINGS)
PG_SETTINGS['applications'] = []
PG_SETTINGS['databases'][0]['db']['storage'] = 'postgresql'

PG_SETTINGS['databases'][0]['db']['partition'] = \
    'guillotina.interfaces.IResource'
PG_SETTINGS['databases'][0]['db']['dsn'] = {
    'scheme': 'postgres',
    'dbname': 'guillotina',
    'user': 'postgres',
    'host': 'localhost',
    'password': '',
    'port': 5432
}

DUMMY_SETTINGS = copy.deepcopy(TESTING_SETTINGS)
DUMMY_SETTINGS['applications'] = []
DUMMY_SETTINGS['databases'][0]['db']['storage'] = 'DUMMY'

DUMMY_SETTINGS['databases'][0]['db']['partition'] = \
    'guillotina.interfaces.IResource'
DUMMY_SETTINGS['databases'][0]['db']['dsn'] = {}


def run_docker_postgresql():
    docker_client = docker.from_env(version='1.23')

    # Clean up possible other docker containers
    test_containers = docker_client.containers.list(
        all=True,
        filters={'label': CONTAINERS_FOR_TESTING_LABEL})
    for test_container in test_containers:
        test_container.stop()
        test_container.remove(v=True, force=True)

    # Create a new one
    container = docker_client.containers.run(
        image=IMAGE,
        labels=[CONTAINERS_FOR_TESTING_LABEL],
        detach=True,
        ports={
            '5432/tcp': 5432
        },
        cap_add=['IPC_LOCK'],
        mem_limit='1g',
        environment={
            'POSTGRES_PASSWORD': '',
            'POSTGRES_DB': 'guillotina',
            'POSTGRES_USER': 'postgres'
        },
        privileged=True
    )
    ident = container.id
    count = 1

    container_obj = docker_client.containers.get(ident)

    opened = False
    host = ''

    while count < 30 and not opened:
        count += 1
        container_obj = docker_client.containers.get(ident)
        print(container_obj.status)
        sleep(2)
        if container_obj.attrs['NetworkSettings']['IPAddress'] != '':
            if os.environ.get('TESTING', '') == 'jenkins':
                host = container_obj.attrs['NetworkSettings']['IPAddress']
            else:
                host = 'localhost'

        if host != '':
            try:
                conn = psycopg2.connect("dbname=guillotina user=postgres host=%s port=5432" % host)  # noqa
                cur = conn.cursor()
                cur.execute("SELECT 1;")
                cur.fetchone()
                cur.close()
                conn.close()
                opened = True
            except: # noqa
                conn = None
                cur = None
    return host


@pytest.fixture(scope='session')
def postgres():
    """
    detect travis, use travis's postgres; otherwise, use docker
    """
    if not IS_TRAVIS:
        host = run_docker_postgresql()
    else:
        host = 'localhost'

    PG_SETTINGS['databases'][0]['db']['dsn']['host'] = host

    yield host  # provide the fixture value

    if not IS_TRAVIS:
        docker_client = docker.from_env(version='1.23')
        # Clean up possible other docker containers
        test_containers = docker_client.containers.list(
            all=True,
            filters={'label': CONTAINERS_FOR_TESTING_LABEL})
        for test_container in test_containers:
            test_container.kill()
            test_container.remove(v=True, force=True)


class GuillotinaDBRequester(object):

    def __init__(self, server, loop):
        self.server = server
        self.loop = loop
        self.root = getUtility(IApplication, name='root')
        self.db = self.root['db']

    async def __call__(self, method, path, params=None, data=None, authenticated=True,
                       auth_type='Basic', headers={}, token=ADMIN_TOKEN, accept='application/json'):
        value, status, headers = await self.make_request(
            method, path, params, data, authenticated,
            auth_type, headers, token, accept)
        return value, status

    async def make_request(self, method, path, params=None, data=None,
                           authenticated=True, auth_type='Basic', headers={},
                           token=ADMIN_TOKEN, accept='application/json'):
        settings = {}
        headers = headers.copy()
        settings['headers'] = headers
        if accept is not None:
            settings['headers']['ACCEPT'] = accept
        if authenticated and token is not None:
            settings['headers']['AUTHORIZATION'] = '{} {}'.format(
                auth_type, token)

        settings['params'] = params
        settings['data'] = data

        async with aiohttp.ClientSession(loop=self.loop) as session:
            operation = getattr(session, method.lower(), None)
            async with operation(self.server.make_url(path), **settings) as resp:
                try:
                    value = await resp.json()
                    status = resp.status
                except:  # noqa
                    value = await resp.read()
                    status = resp.status
                return value, status, resp.headers


# MEMORY DB TESTING FIXTURES


@pytest.fixture(scope='function')
def dummy_guillotina(loop):
    from guillotina import test_package  # noqa
    aioapp = make_app(settings=DUMMY_SETTINGS, loop=loop)
    aioapp.config.execute_actions()
    load_cached_schema()
    return aioapp


class DummyRequestAsyncContextManager(object):
    def __init__(self, dummy_request, loop):
        self.request = dummy_request
        self.loop = loop

    async def __aenter__(self):
        task = asyncio.Task.current_task(loop=self.loop)
        if task is not None:
            task.request = self.request
        return self.request

    async def __aexit__(self, exc_type, exc, tb):
        task = asyncio.Task.current_task(loop=self.loop)
        del task.request


@pytest.fixture(scope='function')
def dummy_request(dummy_guillotina, monkeypatch):
    from guillotina.interfaces import IApplication
    from guillotina.component import getUtility
    root = getUtility(IApplication, name='root')
    db = root['db']

    request = get_mocked_request(db)
    return request


class RootAsyncContextManager(object):
    def __init__(self, request):
        self.request = request
        self.root = None
        self.txn = None

    async def __aenter__(self):
        self.txn = await self.request._tm.begin(request=dummy_request)
        self.root = await self.request._tm.root()
        return self.root

    async def __aexit__(self, exc_type, exc, tb):
        await self.txn.abort()


@pytest.fixture(scope='function')
async def dummy_txn_root(dummy_request):
    return RootAsyncContextManager(dummy_request)

# POSTGRES WITH DOCKER TESTING FIXTURES


@pytest.fixture(scope='function')
def guillotina_main(loop):
    from guillotina import test_package  # noqa
    aioapp = make_app(settings=PG_SETTINGS, loop=loop)
    aioapp.config.execute_actions()
    load_cached_schema()
    yield aioapp


@pytest.fixture(scope='function')
async def guillotina(test_server, postgres, guillotina_main, loop):
    server = await test_server(guillotina_main)
    requester = GuillotinaDBRequester(server=server, loop=loop)
    return requester


class SiteRequesterAsyncContextManager(object):
    def __init__(self, guillotina):
        self.guillotina = guillotina
        self.requester = None

    async def get_requester(self):
        return await self.guillotina

    async def __aenter__(self):
        requester = await self.get_requester()
        resp, status = await requester('POST', '/db', data=json.dumps({
            "@type": "Site",
            "title": "Guillotina Site",
            "id": "guillotina",
            "description": "Description Guillotina Site"
        }))
        assert status == 200
        self.requester = requester
        return requester

    async def __aexit__(self, exc_type, exc, tb):
        resp, status = await self.requester('DELETE', '/db/guillotina')
        assert status == 200


@pytest.fixture(scope='function')
async def site_requester(guillotina):
    return SiteRequesterAsyncContextManager(guillotina)
