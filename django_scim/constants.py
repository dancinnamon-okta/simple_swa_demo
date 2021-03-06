import os
ENCODING = 'utf-8'
SCIM_CONTENT_TYPE = 'application/scim+json'
BASE_PATH = 'https://localhost'

class SchemaURI(object):
    ERROR = 'urn:ietf:params:scim:api:messages:2.0:Error'
    LIST_RESPONSE = 'urn:scim:schemas:core:1.0'
    SEARCH_REQUEST = 'urn:ietf:params:scim:api:messages:2.0:SearchRequest'
    USER = 'urn:scim:schemas:core:1.0'
    OKTA_USER = 'urn:okta:{}:1.0:user:custom'.format(os.environ.get('OKTA_APP_NAME'))
    GROUP = 'urn:scim:schemas:core:1.0'
    RESOURCE_TYPE = 'urn:ietf:params:scim:schemas:core:2.0:ResourceType'
    SERVICE_PROVIDER_CONFIG = 'urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig'
    OKTA_PROVIDER_CONFIG = 'urn:okta:schemas:scim:providerconfig:1.0'
    OKTA_GROUP = 'urn:okta:custom:group:1.0'
