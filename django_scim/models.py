from urllib.parse import urljoin

from django.urls import reverse

from . import constants
from .constants import BASE_PATH


class SCIMServiceProviderConfig(object):
    """
    A reference ServiceProviderConfig. This should be overridden to
    describe those authentication_schemes and features that are implemented by
    your app.
    """
    def __init__(self, request=None):
        self.request = request

    @property
    def meta(self):
        return {
            'location': self.location,
            'resourceType': 'ServiceProviderConfig',
        }

    @property
    def location(self):
        path = reverse('scim:service-provider-config')
        return urljoin(BASE_PATH, path)

    def to_dict(self):
        return {
            'schemas': [constants.SchemaURI.SERVICE_PROVIDER_CONFIG, constants.SchemaURI.OKTA_PROVIDER_CONFIG],
            'documentationUri': 'https://developer.okta.com',
            'patch': {
                'supported': True,
            },
            'bulk': {
                'supported': False,
                'maxOperations': 1000,
                'maxPayloadSize': 1048576,
            },
            'filter': {
                'supported': True,
                'maxResults': 50,
            },
            'changePassword': {
                'supported': True,
            },
            'sort': {
                'supported': False,
            },
            'etag': {
                'supported': False,
            },
            'authenticationSchemes': {},
            'meta': self.meta,
            'urn:okta:schemas:scim:providerconfig:1.0':{
                'userManagementCapabilities':[
                    'GROUP_PUSH',
                    'IMPORT_NEW_USERS',
                    'IMPORT_PROFILE_UPDATES',
                    'PUSH_NEW_USERS',
                    'PUSH_PASSWORD_UPDATES',
                    'PUSH_PENDING_USERS',
                    'PUSH_PROFILE_UPDATES',
                    'PUSH_USER_DEACTIVATION',
                    'REACTIVATE_USERS'
                ]
            }
        }
