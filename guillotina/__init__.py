# -*- encoding: utf-8 -*-

# load the patch before anything else.
from guillotina import patch  # noqa
from guillotina.i18n import MessageFactory

import logging


# create logging
logger = logging.getLogger('guillotina')

_ = MessageFactory('guillotina')


app_settings = {
    "databases": [],
    "host": "127.0.0.1",
    "port": 8080,
    "static": [],
    "utilities": [],
    "root_user": {
        "password": ""
    },
    "auth_extractors": [
        "guillotina.auth.extractors.BearerAuthPolicy",
        "guillotina.auth.extractors.BasicAuthPolicy",
        "guillotina.auth.extractors.WSTokenAuthPolicy",
    ],
    "auth_user_identifiers": [],
    "auth_token_validators": [
        "guillotina.auth.validators.SaltedHashPasswordValidator",
        "guillotina.auth.validators.JWTValidator"
    ],
    "default_permission": 'zope.Public',
    "available_addons": {},
    "api_definition": {},
    "cors": {
        "allow_origin": ["http://localhost:8080"],
        "allow_methods": ["GET", "POST", "DELETE", "HEAD", "PATCH", "OPTIONS"],
        "allow_headers": ["*"],
        "expose_headers": ["*"],
        "allow_credentials": True,
        "max_age": 3660
    },
    "jwt": {
        "secret": "foobar",
        "algorithm": "HS256"
    }
}

SCHEMA_CACHE = {}
PERMISSIONS_CACHE = {}
FACTORY_CACHE = {}
BEHAVIOR_CACHE = {}
