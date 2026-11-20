
from django.urls import path
from .views import *

app_name='emails'

urlpatterns = [
    # path('init/send_emails/', send_emails),
    path('api/send_email/', send_email, name='send_email'),
    path('init/authorise/', authorize, name='authorise'),
    # Support both without and with trailing slash to prevent any redirect URI mismatch
    path('init/oauth2callback', oauth2callback, name='oauth2callback_bare'),
    path('init/oauth2callback/', oauth2callback, name='oauth2callback'),
]
