#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright © 2016-2017, Okta, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import os
import re
import json

from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest


class ListResponse():
    def __init__(self, list, start_index=1, count=None, total_results=0):
        self.list = list
        self.start_index = start_index
        self.count = count
        self.total_results = total_results

    def to_scim_resource(self):
        rv = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": self.total_results,
            "startIndex": self.start_index,
            "Resources": []
        }
        resources = []
        for item in self.list:
            resources.append(SCIMUser(item).to_scim_resource())
        if self.count:
            rv['itemsPerPage'] = self.count
        rv['Resources'] = resources
        return rv


class SCIMUser():

    def __init__(self, djangoUser):
        self.usr = djangoUser

    def to_scim_resource(self):
        rv = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": self.usr.id,
            "userName": self.usr.get_username(),
            "name": {
                "familyName": self.usr.last_name,
                "givenName": self.usr.first_name,
            },
            "emails": [
                {
                  "value": self.usr.email,
                  "type": "work",
                  "primary": "true"
                },
            ],
            "active": self.usr.is_active,

        }
        return rv

    def create(username, email, password):
        self.usr = User.objects.create_user(username, email, password)


def scim_error(message, status_code=500):
    rv = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
        "detail": message,
        "status": str(status_code)
    }
    return flask.jsonify(rv), status_code


def user_single(request, user_id):
    if request.method == 'GET':
        return _user_get(user_id)

    elif request.method == 'PUT':
        body_unicode = request.body.decode('utf-8')
        updatedUser = json.loads(body_unicode)
        return _user_put(user_id, updatedUser)

    elif request.method == 'PATCH':
        body_unicode = request.body.decode('utf-8')
        patch_resource = json.loads(body_unicode)
        for attribute in ['schemas', 'Operations']:
            if attribute not in patch_resource:
                message = "Payload must contain '{}' attribute.".format(attribute)
                return message, 400
        schema_patchop = 'urn:ietf:params:scim:api:messages:2.0:PatchOp'
        if schema_patchop not in patch_resource['schemas']:
            return "The 'schemas' type in this request is not supported.", 501

        user = SCIMUser(User.objects.get(id=user_id))
        return _user_patch(user_id, patch_resource['Operations'])

    else:
        return HttpResponseBadRequest("Request type not supported.")

def user_multiple(request):
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        newUser = json.loads(body_unicode)
        resp =  _user_post(newUser)
        resp.status_code = 201
        return resp

    elif request.method == 'GET':
        return _users_fetch(request)
    else:
        return HttpResponseBadRequest("Request type not supported.")


def groups_get():
    rv = ListResponse([])
    return HttpResponse(json.dumps(rv.to_scim_resource()))

def _user_get(user_id):
    try:
        print("Looking for user_id: " + user_id)
        user = SCIMUser(User.objects.get(id=user_id))
        print (user.to_scim_resource())
        return HttpResponse(json.dumps(user.to_scim_resource()))
    except Exception as e:
        print(e)
        return HttpResponseNotFound()

def _user_put(user_id, updatedUser):
    try:
        user = SCIMUser(User.objects.get(id=user_id))
    except:
        return HttpResponseNotFound()

    try:
        user.usr.username = updatedUser.userName
        user.usr.last_name = updatedUser.familyName
        user.usr.first_name = updatedUser.givenName
        user.usr.email = updatedUser.emails[0].value
        user.usr.is_active = updatedUser.active
        user.usr.save()
        return HttpResponse(json.dumps(user.to_scim_resource()))
    except:
        return HttpResponseBadRequest("There was an error updating user: " + json.dumps(updatedUser))


def _user_patch(user_id, operations):
    try:
        user = SCIMUser(User.objects.get(id=user_id))
        for operation in patch_resource['Operations']:
            if 'op' not in operation and operation['op'] != 'replace':
                continue
            value = operation['value']
            for key in value.keys():
                if key == "userName":
                    user.usr.username = value
                elif key == "familyName":
                    user.usr.last_name = value
                elif key == "givenName":
                    user.usr.first_name = value
                elif key == "emails":
                    user.usr.email = value[0].value
                elif key == "active":
                    user.usr.is_active = value
        user.usr.save()
        return HttpResponse(json.dumps(user.to_scim_resource()))
    except:
        return HttpResponseBadRequest("There was an error updating user: " + json.dumps(operations))

def _user_post(newUser):
    try:
        user = SCIMUser(None)
        user.create(newUser.userName, newUser.emails[0].value, newUser.password)

        user.usr.last_name = newUser.familyName
        user.usr.first_name = newUser.givenName
        user.usr.is_active = newUser.active
        user.usr.save()
        return HttpResponse(json.dumps(user.to_scim_resource()))
    except:
        return HttpResponseBadRequest("There was an error creating user: " + json.dumps(updatedUser))

def _users_fetch(request):
    request_filter = request.GET.get('filter')
    match = None
    print(request_filter)
    if request_filter:
        match = re.match('(\w+) eq "([^"]*)"', request_filter)
    if match:
        (search_key_name, search_value) = match.groups()
        search_key = getattr(User, search_key_name)

    print("Search key:" + search_key_name)
    count = int(request.GET.get('count', 100))
    start_index = int(request.GET.get('startIndex', 1))
    if start_index < 1:
        start_index = 1
    start_index -= 1

    users = User.objects.filter(**{search_key_name: search_value})

    if users.count() - start_index < 100:
        count = users.count() - start_index

    users = users[start_index:count]

    rv = ListResponse(users,
                      start_index=start_index,
                      count=count,
                      total_results=users.count())
    return HttpResponse(json.dumps(rv.to_scim_resource()))
