import json
import logging
from urllib.parse import urljoin
import os

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django import db
from django.db import transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.utils import six
from django.utils.decorators import method_decorator
from django.urls import reverse

from . import constants
from .simple_filter import SCIMSimpleUserFilterTransformer
from .exceptions import SCIMException
from .exceptions import NotFoundError
from .exceptions import BadRequestError
from .exceptions import IntegrityError
from .constants import BASE_PATH
from .utils import get_loggable_body

from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

from .adapters import SCIMUser
from .adapters import SCIMGroup
from .models import SCIMServiceProviderConfig

logger = logging.getLogger(__name__)

class SCIMView(View):
    lookup_field = 'id'
    lookup_url_kwarg = 'uuid'

    implemented = True

    def get_object(self):
        """Get object by configurable ID."""
        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        uuid = self.kwargs[lookup_url_kwarg]

        try:
            return self.model_cls.objects.get(id=uuid)
        except ObjectDoesNotExist as _e:
            raise NotFoundError(uuid)

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        if not self.implemented:
            return self.status_501(request, *args, **kwargs)

        if not self.correct_auth_header(request):
            return self.status_401(request)

        try:
            try:
                body = get_loggable_body(request.body.decode(constants.ENCODING))
                logger.debug(
                    u'REQUEST '
                    u'PATH >>>>>{}<<<<< '
                    u'METHOD >>>>>{}<<<<< '
                    u'BODY >>>>>{}<<<<<'.format(
                        request.path,
                        request.method,
                        body,
                    )
                )
            except:
                logger.debug(
                    u'REQUEST '
                    u'PATH >>>>>{}<<<<< '
                    u'METHOD >>>>>{}<<<<< '
                    u'ERROR >>>>>Could not get loggable body<<<<<'.format(
                        request.path,
                        request.method,
                    ),
                    exc_info=1,
                )
            return super(SCIMView, self).dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.debug('Unable to complete SCIM call.', exc_info=1)
            if not isinstance(e, SCIMException):
                e = SCIMException(six.text_type(e))

            content = json.dumps(e.to_dict())
            return HttpResponse(content=content,
                                content_type=constants.SCIM_CONTENT_TYPE,
                                status=e.status)

    def status_501(self, request, *args, **kwargs):
        """
        A service provider that does NOT support a feature SHOULD
        respond with HTTP status code 501 (Not Implemented).
        """
        return HttpResponse(content_type=constants.SCIM_CONTENT_TYPE, status=501)

    def status_401(self, request):
        return HttpResponse(content_type=constants.SCIM_CONTENT_TYPE, status=401)

    def correct_auth_header(self, request):
        if 'HTTP_AUTHORIZATION' not in request.META or 'API_KEY' not in os.environ:
            return False

        key = os.environ.get('API_KEY')
        bearer = request.META.get('HTTP_AUTHORIZATION')

        return key == bearer



class FilterMixin(object):

    parser = None
    scim_adapter = None

    def _page(self, request):
        try:
            start = request.GET.get('startIndex', 1)
            if start is not None:
                start = int(start)
                if start < 1:
                    raise BadRequestError('Invalid startIndex (must be >= 1)')

            count = request.GET.get('count', 50)
            if count is not None:
                count = int(count)

            return start, count

        except ValueError as e:
            raise BadRequestError('Invalid pagination values: ' + str(e))

    def _search(self, request, query, start, count):
        try:
            qs = self.parser.search(query)
        except ValueError as e:
            raise BadRequestError('Invalid filter/search query: ' + str(e))

        return self._build_response(request, qs, start, count)

    def _build_response(self, request, qs, start, count):
        try:
            total_count = sum(1 for _ in qs)
            qs = qs[start-1:(start-1) + count]
            resources = [self.scim_adapter(o, request=request).to_dict() for o in qs]
            doc = {
                'schemas': [constants.SchemaURI.LIST_RESPONSE],
                'totalResults': total_count,
                'itemsPerPage': count,
                'startIndex': start,
                'Resources': resources,
            }
        except ValueError as e:
            raise BadRequestError(six.text_type(e))
        else:
            content = json.dumps(doc)
            print(content)
            return HttpResponse(content=content,
                                content_type=constants.SCIM_CONTENT_TYPE)

class SearchView(FilterMixin, SCIMView):
    http_method_names = ['post']

    scim_adapter = None

    def post(self, request):
        body = json.loads(request.body.decode(constants.ENCODING) or '{}')
        if body.get('schemas') != [constants.SchemaURI.SEARCH_REQUEST]:
            raise BadRequestError('Invalid schema uri. Must be SearchRequest.')

        query = body.get('filter', request.GET.get('filter'))

        if not query:
            raise BadRequestError('No filter query specified')
        else:
            response = self._search(request, query, *self._page(request))
            path = reverse(self.scim_adapter.url_name)
            url = urljoin("https://localhost", path).rstrip('/')
            response['Location'] = url + '/.search'
            return response


class GetView(object):
    def get(self, request, *args, **kwargs):
        if kwargs.get(self.lookup_url_kwarg):
            return self.get_single(request)

        return self.get_many(request)

    def get_single(self, request):
        obj = self.get_object()
        scim_obj = self.scim_adapter(obj, request=request)
        content = json.dumps(scim_obj.to_dict())
        response = HttpResponse(content=content,
                                content_type=constants.SCIM_CONTENT_TYPE)
        response['Location'] = scim_obj.location
        return response

    def get_many(self, request):
        query = request.GET.get('filter')
        if query:
            return self._search(request, query, *self._page(request))

        qs = self.model_cls.objects.all().order_by(self.lookup_field)
        return self._build_response(request, qs, *self._page(request))


class DeleteView(object):
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()

        scim_obj = self.scim_adapter(obj, request=request)

        scim_obj.delete()

        return HttpResponse(status=204)


class PostView(object):
    def post(self, request, **kwargs):
        print("Post Request Body:{}".format(request.body.decode(constants.ENCODING)))
        obj = self.model_cls()
        scim_obj = self.scim_adapter(obj, request=request)

        body = json.loads(request.body.decode(constants.ENCODING))

        scim_obj.from_dict(body)

        try:
            scim_obj.save()
        except db.utils.IntegrityError as e:
            # Cast error to a SCIM IntegrityError to use the status
            # attribute on the SCIM IntegrityError.
            raise IntegrityError(str(e))

        content = json.dumps(scim_obj.to_dict())
        response = HttpResponse(content=content,
                                content_type=constants.SCIM_CONTENT_TYPE,
                                status=201)
        response['Location'] = scim_obj.location
        return response


class PutView(object):
    def put(self, request, *args, **kwargs):
        print("Put Request Body:{}".format(request.body.decode(constants.ENCODING)))
        obj = self.get_object()

        scim_obj = self.scim_adapter(obj, request=request)
        print(request.body.decode(constants.ENCODING))
        body = json.loads(request.body.decode(constants.ENCODING))

        scim_obj.from_dict(body)
        print(scim_obj)
        if hasattr(scim_obj, 'is_active') and getattr(scim_obj, 'is_active') == False:
            scim_obj.delete()
        else:
            scim_obj.save()

        content = json.dumps(scim_obj.to_dict())
        response = HttpResponse(content=content,
                                content_type=constants.SCIM_CONTENT_TYPE)
        response['Location'] = scim_obj.location
        return response

class UsersView(FilterMixin, GetView, PostView, PutView, DeleteView, SCIMView):

    http_method_names = ['get', 'post', 'put']

    scim_adapter = SCIMUser
    model_cls = get_user_model()
    parser = SCIMSimpleUserFilterTransformer


class GroupsView(FilterMixin, GetView, PostView, PutView, DeleteView, SCIMView):
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    scim_adapter = SCIMGroup
    model_cls = Group
    parser = None


class ServiceProviderConfigView(SCIMView):
    http_method_names = ['get']

    def get(self, request):
        config = SCIMServiceProviderConfig(request=request)
        content = json.dumps(config.to_dict())
        return HttpResponse(content=content,
                            content_type=constants.SCIM_CONTENT_TYPE)
