from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden

import json

# Create your views here.
def view_main(request):
    if _is_logged_in(request):
        u = User.objects.get(username=request.user)
        ctx = {'profile': json.dumps(_get_user_profile(u))}
        return render(request, 'swa_app/home.html', ctx)
    else:
        return HttpResponseRedirect(reverse('login'))

def view_admin(request):
    if _is_logged_in(request):
        u = User.objects.get(username=request.user)
        if _is_admin(u):
            ctx = {'all_users': json.dumps(_get_all_users())}
            return render(request, 'swa_app/admin.html', ctx)
        else:
            return HttpResponseForbidden()
    else:
        return HttpResponseRedirect(reverse('login'))

@csrf_exempt
def view_login(request):
    if request.method == 'POST':
        user = authenticate(username=request.POST['inputEmail'], password=request.POST['inputPassword'])
        print(user)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse('main'))
        else:
            return render(request, 'swa_app/login.html', None)
    else:
        return render(request, 'swa_app/login.html', None)

@csrf_exempt
def view_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('login'))

def _is_logged_in(request):
    return request.user.is_authenticated

def _is_admin(usr):
    for grp in usr.groups.all():
        if grp.name == "Catalog Admin":
            return True
    return False

def _get_user_profile(usr):
    user_dict = {}
    user_dict['user_name'] = usr.username
    user_dict['first_name'] = usr.first_name
    user_dict['last_name'] = usr.last_name
    user_dict['department'] = usr.profile.department
    user_dict['opt_in'] = usr.profile.opt_in
    user_dict['phone_number'] = usr.profile.phone_number
    user_dict['country'] = usr.profile.country
    user_dict['company_name'] = usr.profile.company_name

    dicts = []
    for grp in usr.groups.all():
        d = {
            'name': grp.name,
        }
        dicts.append(d)

    user_dict['groups'] = dicts
    return user_dict

def _get_all_users():
    retVal = []
    for usr in User.objects.all():
        retVal.append(_get_user_profile(usr))
    return retVal
