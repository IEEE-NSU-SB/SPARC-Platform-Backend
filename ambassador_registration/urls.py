from django.urls import path

from . import views

app_name = 'ambassador_registration'

urlpatterns = [
    path('', views.ambassador_apply, name='ambassador_apply'),
    path('thanks/', views.thanks, name='thanks'),
    path('admin/', views.admin_ambassador, name='admin_ambassador'),
    path('toggle-publish/', views.toggle_publish, name='toggle_publish'),
    path('responses/', views.response_table, name='response_table'),
    path('responses/<int:id>/', views.view_response, name='view_response'),
    path('save-selected/', views.save_selected, name='save_selected'),
    path('download-excel/', views.download_excel, name='download_excel'),
]
