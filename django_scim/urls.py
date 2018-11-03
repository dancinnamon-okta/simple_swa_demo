try:
    from django.urls import re_path
except ImportError:
    from django.conf.urls import url as re_path

from .simple_filter import SCIMSimpleUserFilterTransformer
from .adapters import SCIMUser
from . import views


app_name = 'scim'

urlpatterns = [
    # This endpoint is used soley for middleware url purposes.
    re_path(r'^$',
        views.SCIMView.as_view(implemented=False),
        name='root'),

    re_path(r'^.search$',
        views.SearchView.as_view(implemented=False),
        name='search'),

    re_path(r'^Users/.search$',
        views.SearchView.as_view(scim_adapter=SCIMUser(None), parser=SCIMSimpleUserFilterTransformer),
        name='users-search'),

    re_path(r'^Users(?:/(?P<uuid>[^/]+))?$',
        views.UsersView.as_view(),
        name='users'),

    re_path(r'^Groups/.search$',
        views.SearchView.as_view(implemented=False),
        name='groups-search'),

    re_path(r'^Groups(?:/(?P<uuid>[^/]+))?$',
        views.GroupsView.as_view(),
        name='groups'),

    re_path(r'^Me$',
        views.SCIMView.as_view(implemented=False),
        name='me'),

    re_path(r'^ServiceProviderConfig$',
        views.ServiceProviderConfigView.as_view(),
        name='service-provider-config'),
]
