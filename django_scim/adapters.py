"""
Adapters are used to convert the data model described by the SCIM 2.0
specification to a data model that fits the data provided by the application
implementing a SCIM api.

For example, in a Django app, there are User and Group models that do
not have the same attributes/fields that are defined by the SCIM 2.0
specification. The Django User model has both ``first_name`` and ``last_name``
attributes but the SCIM speicifcation requires this same data be sent under
the names ``givenName`` and ``familyName`` respectively.

An adapter is instantiated with a model instance. Eg::

    user = get_user_model().objects.get(id=1)
    scim_user = SCIMUser(user)
    ...

"""
import logging
from urllib.parse import urljoin

from django.contrib.auth import get_user_model
from django.urls import reverse
from django import core

from . import constants
from .exceptions import PatchError
from .constants import BASE_PATH
import json

logger = logging.getLogger(__name__)

class SCIMMixin(object):
    def __init__(self, obj, request=None):
        self.obj = obj
        self._request = request

    @property
    def request(self):
        if self._request:
            return self._request

        raise RuntimeError('Adapter is not associated with a request object. '
                           'Set object.request to avoid this error.')

    @request.setter
    def request(self, value):
        self._request = value

    @property
    def id(self):
        return str(self.obj.id)

    @property
    def path(self):
        return reverse(self.url_name, kwargs={'uuid': self.obj.id})

    @property
    def location(self):
        return urljoin(BASE_PATH, self.path)

    def save(self):
        self.obj.save()

    def delete(self):
        self.obj.__class__.objects.filter(id=self.obj.id).delete()

    def handle_operations(self, operations):
        """
        The SCIM specification allows for making changes to specific attributes
        of a model. These changes are sent in PUT requests and are batched into
        operations to be performed on a object.Operations could be 'add',
        'remove', 'replace', etc. This method iterates through all of the
        operations in ``operations`` and calls the appropriate handler (defined
        on the appropriate adapter) for each.
        """
        for operation in operations:
            op_code = operation.get('op')
            op_code = 'handle_' + op_code
            handler = getattr(self, op_code)
            handler(operation)


class SCIMUser(SCIMMixin):
    """
    Adapter for adding SCIM functionality to a Django User object.

    This adapter can be overriden; see the ``USER_ADAPTER`` setting
    for details.
    """
    # not great, could be more decoupled. But \__( )__/ whatevs.
    url_name = 'scim:users'
    resource_type = 'User'

    @property
    def user_name(self):
        return self.obj.username

    @property
    def is_active(self):
        return self.obj.is_active

    @property
    def display_name(self):
        """
        Return the displayName of the user per the SCIM spec.
        """
        if self.obj.first_name and self.obj.last_name:
            return u'{0.first_name} {0.last_name}'.format(self.obj)
        return self.obj.username

    @property
    def emails(self):
        """
        Return the email of the user per the SCIM spec.
        """
        return [{'value': self.obj.email, 'primary': True}]

    @property
    def groups(self):
        """
        Return the groups of the user per the SCIM spec.
        """
        group_qs = self.obj.groups.all()
        scim_groups = [SCIMGroup(g, self.request) for g in group_qs]

        dicts = []
        for group in scim_groups:
            d = {
                'value': group.id,
                #'$ref': group.location,
                'display': group.display_name,
            }
            dicts.append(d)

        return dicts

    @property
    def meta(self):
        """
        Return the meta object of the user per the SCIM spec.
        """
        d = {
            'resourceType': self.resource_type,
            'created': self.obj.date_joined.isoformat(timespec='milliseconds'),
            'lastModified': self.obj.date_joined.isoformat(timespec='milliseconds'),
            'location': self.location,
        }

        return d

    def to_dict(self):
        """
        Return a ``dict`` conforming to the SCIM User Schema,
        ready for conversion to a JSON object.
        """
        d = {
            'schemas': [constants.SchemaURI.USER, constants.SchemaURI.OKTA_USER],
            'id': self.id,
            'userName': self.obj.username,
            'name': {
                'givenName': self.obj.first_name,
                'familyName': self.obj.last_name,
            },
            'displayName': self.display_name,
            'emails': self.emails,
            'active': self.obj.is_active,
            'groups': self.groups,
            constants.SchemaURI.OKTA_USER: {
                "phone_number":self.obj.profile.phone_number,
                "department": self.obj.profile.department,
                "company_name": self.obj.profile.company_name,
                "country": self.obj.profile.country,
                "opt_in": self.obj.profile.opt_in,
            },
        #    'meta': self.meta,
        }

        return d

    def from_dict(self, d):
        """
        Consume a ``dict`` conforming to the SCIM User Schema, updating the
        internal user object with data from the ``dict``.

        Please note, the user object is not saved within this method. To
        persist the changes made by this method, please call ``.save()`` on the
        adapter. Eg::

            scim_user.from_dict(d)
            scim_user.save()
        """
        username = d.get('userName')
        self.obj.username = username or ''

        first_name = d.get('name', {}).get('givenName')
        self.obj.first_name = first_name or ''

        last_name = d.get('name', {}).get('familyName')
        self.obj.last_name = last_name or ''

        emails = d.get('emails', [])
        primary_emails = [e['value'] for e in emails if e.get('primary')]
        emails = primary_emails + emails
        email = emails[0] if emails else None
        self.obj.email = email

        cleartext_password = d.get('password')
        if cleartext_password:
            self.obj.set_password(cleartext_password)

        active = d.get('active')
        if active is not None:
            self.obj.is_active = active

        if self.obj.id is None:
            self.obj.save()

        if d.get("{}".format(constants.SchemaURI.OKTA_USER)) is not None:
            self.obj.profile.phone_number = d.get("{}".format(constants.SchemaURI.OKTA_USER)).get("phone_number")
            self.obj.profile.department = d.get("{}".format(constants.SchemaURI.OKTA_USER)).get("department")
            self.obj.profile.company_name = d.get("{}".format(constants.SchemaURI.OKTA_USER)).get("company_name")
            self.obj.profile.country = d.get("{}".format(constants.SchemaURI.OKTA_USER)).get("country")
            self.obj.profile.opt_in = d.get("{}".format(constants.SchemaURI.OKTA_USER)).get("opt_in")

    @classmethod
    def resource_type_dict(cls, request=None):
        """
        Return a ``dict`` containing ResourceType metadata for the user object.
        """
        id_ = cls.resource_type
        path = reverse('scim:resource-types', kwargs={'uuid': id_})
        location = urljoin(BASE_PATH, path)
        return {
            'schemas': [constants.SchemaURI.RESOURCE_TYPE],
            'id': id_,
            'name': 'User',
            'endpoint': reverse('scim:users'),
            'description': 'User Account',
            'schema': constants.SchemaURI.USER,
            'meta': {
                'location': location,
                'resourceType': 'ResourceType'
            }
        }

class SCIMGroup(SCIMMixin):
    """
    Adapter for adding SCIM functionality to a Django Group object.

    This adapter can be overriden; see the ``GROUP_ADAPTER``
    setting for details.
    """
    # not great, could be more decoupled. But \__( )__/ whatevs.
    url_name = 'scim:groups'
    resource_type = 'Group'

    @property
    def display_name(self):
        """
        Return the displayName of the user per the SCIM spec.
        """
        return self.obj.name

    @property
    def members(self):
        """
        Return a list of user dicts (ready for serialization) for the members
        of the group.

        :rtype: list
        """
        dicts = []
        users = self.obj.user_set.all()
        if users is not None:
            scim_users = [SCIMUser(user, self.request) for user in users]

            for user in scim_users:
                d = {
                    'value': user.id,
                    'display': user.user_name,
                    #'$ref': user.location,
                    #'display': user.display_name,
                }
                dicts.append(d)

        return dicts

    @property
    def meta(self):
        """
        Return the meta object of the user per the SCIM spec.
        """
        d = {
            'resourceType': self.resource_type,
            'location': self.location,
        }

        return d

    def to_dict(self):
        """
        Return a ``dict`` conforming to the SCIM User Schema,
        ready for conversion to a JSON object.
        """
        return {
            'schemas': [constants.SchemaURI.GROUP, constants.SchemaURI.OKTA_GROUP],
            'id': self.id,
            'displayName': self.display_name,
            'members': self.members,
            "urn:okta:custom:group:1.0":{
                "description":"This is the first group"
            },
        #    'meta': self.meta,
        }

    def from_dict(self, d):
        """
        Consume a ``dict`` conforming to the SCIM Group Schema, updating the
        internal group object with data from the ``dict``.

        Please note, the group object is not saved within this method. To
        persist the changes made by this method, please call ``.save()`` on the
        adapter. Eg::

            scim_group.from_dict(d)
            scim_group.save()
        """
        name = d.get('displayName')
        self.obj.name = name or ''

        if self.obj.id is None:
            self.obj.save()

        members = d.get('members')
        self.obj.user_set.clear()
        if members is not None:
            ids = [int(member.get('value')) for member in members]
            users = get_user_model().objects.filter(id__in=ids)
            if len(ids) != users.count():
                raise PatchError('Can not add a non-existent user to group')

            for user in users:
                self.obj.user_set.add(user)


    @classmethod
    def resource_type_dict(cls, request=None):
        """
        Return a ``dict`` containing ResourceType metadata for the group object.
        """
        id_ = cls.resource_type
        path = reverse('scim:resource-types', kwargs={'uuid': id_})
        location = urljoin(BASE_PATH, path)
        return {
            'schemas': [constants.SchemaURI.RESOURCE_TYPE],
            'id': id_,
            'name': 'Group',
            'endpoint': reverse('scim:groups'),
            'description': 'Group',
            'schema': constants.SchemaURI.GROUP,
            'meta': {
                'location': location,
                'resourceType': 'ResourceType'
            }
        }

    def handle_add(self, operation):
        """
        Handle add operations.
        """
        if operation.get('path') == 'members':
            members = operation.get('value', [])
            ids = [int(member.get('value')) for member in members]
            users = get_user_model().objects.filter(id__in=ids)

            if len(ids) != users.count():
                raise PatchError('Can not add a non-existent user to group')

            for user in users:
                self.obj.user_set.add(user)

        else:
            raise NotImplemented

    def handle_remove(self, operation):
        """
        Handle remove operations.
        """
        if operation.get('path') == 'members':
            members = operation.get('value', [])
            ids = [int(member.get('value')) for member in members]
            users = get_user_model().objects.filter(id__in=ids)

            if len(ids) != users.count():
                raise PatchError('Can not remove a non-existent user from group')

            for user in users:
                self.obj.user_set.remove(user)

        else:
            raise NotImplemented
