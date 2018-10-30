from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.contrib.auth.models import User

import json

# Create your views here.
def view_main(request):
    if _is_logged_in(request):
        u = User.objects.get(username=request.user)
        ctx = {'profile': json.dumps(_get_user_profile(u))}
        return render(request, 'swa_app/home.html', ctx)
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

def _get_user_profile(usr):
    user_dict = {}
    user_dict['user_name'] = usr.username
    user_dict['first_name'] = usr.first_name
    user_dict['last_name'] = usr.last_name

    dicts = []
    for grp in usr.groups.all():
        d = {
            'name': grp.name,
        }
        dicts.append(d)

    user_dict['groups'] = dicts
    return user_dict
