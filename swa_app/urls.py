"""swa_opp_demo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from .views import view_main
from .views import view_login, view_logout, view_admin

urlpatterns = [
    url(r'^$', view_main, name='main'),
    url(r'^login$', view_login, name='login'),
    url(r'^logout$', view_logout, name='logout'),
    url(r'^admin$', view_admin, name='admin'),

]
