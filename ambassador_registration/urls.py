from django.urls import path

from . import views

app_name = 'ambassador_registration'

urlpatterns = [
    path('', views.ambassador_apply, name='ambassador_apply'),
    path('thanks/', views.thanks, name='thanks'),
]
