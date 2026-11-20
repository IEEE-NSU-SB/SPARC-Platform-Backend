from django.contrib import admin, messages

from .models import *
# Register your models here.

@admin.register(EventFormStatus_Phase01)
class EventFormStatusAdmin_Phase01(admin.ModelAdmin):
    list_display = ['is_published', 'updated_at']

@admin.register(EventFormStatus_Phase02)
class EventFormStatusAdmin_Phase02(admin.ModelAdmin):
    list_display = ['is_published', 'updated_at']

@admin.register(Form_Participant_Phase_1)
class Form_Participant_Phase01_Admin(admin.ModelAdmin):
    list_display = ['id', 'name', 'university', 'email', 'membership_type', 'is_nsu_student', 'is_selected', 'is_phase_2_email_sent', 'created_at']
    list_filter = ['is_selected', 'is_phase_2_email_sent', 'membership_type', 'is_nsu_student', 'created_at']
    search_fields = ['name', 'email', 'university', 'department', 'university_id']
    actions = ['send_phase_2_email_selected']

    @admin.action(description='Send/Resend Phase-2 email to selected participants (Selected only)')
    def send_phase_2_email_selected(self, request, queryset):
        participants = queryset.filter(is_selected=True)
        if not participants.exists():
            self.message_user(request, 'No selected participants in current selection.', level=messages.WARNING)
            return
        from emails.views import send_participant_phase02_email
        send_participant_phase02_email(request, participants)
        self.message_user(request, f'Phase 2 invitation email processing finished for {participants.count()} participant(s).', level=messages.SUCCESS)

@admin.register(Form_Participant_Phase_2)
class Form_Participant_Phase02_Admin(admin.ModelAdmin):
    list_display = ['id', 'name', 'institution', 'email', 'membership_type', 'is_payment_confirmed', 'created_at']
    list_filter = ['membership_type', 'is_payment_confirmed', 'payment_method', 'created_at']
    search_fields = ['name', 'email', 'institution', 'transaction_id']

admin.site.register(Form_Participant_Unique_Code_Phase_2)

admin.site.register(University)
