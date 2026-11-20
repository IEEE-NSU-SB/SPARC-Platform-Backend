from django.urls import path
from . import views

app_name = 'hackathon'

urlpatterns = [
    path('phase-1/', views.form_phase01, name='form_phase01'),
    path('admin/phase-1/', views.admin_phase01, name='admin_phase01'),
    path('toggle-publish/phase-1/', views.toggle_publish_phase01, name='toggle_publish_phase01'),
    path('submit/phase-1/', views.submit_phase01, name='submit_phase01'),
    path('responses/phase-1/', views.response_table_phase01, name='response_table_phase01'),
    path('responses/phase-1/<int:id>/', views.view_response_phase01, name='view_response_phase01'),
    path('save-selected/phase-1/', views.save_selected_phase01, name='save_selected_phase01'),
    path('send-phase02-email/', views.send_phase02_email, name='send_phase02_email'),
    path('download-excel/phase-1/', views.download_excel_phase01, name='download_excel_phase01'),

    # Phase 2 Routes
    path('phase-2/', views.form_phase02, name='form_phase02'),
    path('admin/phase-2/', views.admin_phase02, name='admin_phase02'),
    path('toggle-publish/phase-2/', views.toggle_publish_phase02, name='toggle_publish_phase02'),
    path('submit/phase-2/', views.submit_phase02, name='submit_phase02'),
    path('responses/phase-2/', views.response_table_phase02, name='response_table_phase02'),
    path('responses/phase-2/<int:id>/', views.view_response_phase02, name='view_response_phase02'),
    path('save-selected/phase-2/', views.save_selected_phase02, name='save_selected_phase02'),
    path('download-excel/phase-2/', views.download_excel_phase02, name='download_excel_phase02'),
]