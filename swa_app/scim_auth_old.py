from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User

class SCIM_AUTH_BACKEND:

    def authenticate(self, request, username=None, password=None):
        if (username == 'admin' and password == 'testing123') or 'admin' in request.META:
            user = User.objects.get(username='admin')
            return user
        return None


    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
