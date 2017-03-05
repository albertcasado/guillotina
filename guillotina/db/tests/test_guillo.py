# -*- encoding: utf-8 -*-
import json

async def test_get_the_root(guillotina):
    requester = await guillotina
    response, status = await requester('GET', '/')
    assert response['static_file'] == ['favicon.ico']
    assert response['databases'] == ['guillotina']
    assert response['static_directory'] == []


async def test_get_db(guillotina):
    requester = await guillotina
    response, status = await requester('GET', '/guillotina')
    assert response['sites'] == []


async def test_get_site(site):
    async for requester in site:
        response, status = await requester('GET', '/guillotina/guillotina')
        assert response['@type'] == 'Site'


async def test_get_content(site):
    async for requester in site:
        response, status = await requester(
            'POST',
            '/guillotina/guillotina',
            data=json.dumps({
                '@type': 'Item',
                'id': 'hello',
                'title': 'Hola'
            }))
        assert status == 201
        response, status = await requester(
            'GET',
            '/guillotina/guillotina/hello')
        assert status == 200
