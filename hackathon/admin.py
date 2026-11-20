from django.contrib import admin, messages
from .models import (
    HackathonFormStatus_Phase01,
    HackathonFormStatus_Phase02,
    HackathonMember_Phase01,
    HackathonMember_Phase02,
    HackathonTeam_Phase01,
    HackathonTeam_Phase02,
    HackathonTeam_Unique_Code_Phase_2,
)

# Register your models here

# PHASE 1 ADMIN

class HackathonMemberPhase01Inline(admin.TabularInline):
    model = HackathonMember_Phase01
    extra = 0
    max_num = 3
    fields = (
        'member_order',
        'is_leader',
        'full_name',
        'email',
        'phone_number',
        'university',
        'department',
        'academic_year',
        'student_id',
        'gender',
        'is_ieee_member',
        'ieee_membership_no',
        'ieee_membership_grade',
        'ieee_student_branch',
        'ieee_volunteer_position',
    )


@admin.register(HackathonTeam_Phase01)
class HackathonTeamPhase01Admin(admin.ModelAdmin):
    list_display = (
        'id',
        'team_name',
        'team_size',
        'university_distribution',
        'leader_email',
        'leader_phone',
        'is_selected',
        'is_phase_2_email_sent',
        'created_at',
    )
    list_filter = (
        'team_size',
        'university_distribution',
        'is_selected',
        'is_phase_2_email_sent',
    )
    search_fields = (
        'team_name',
        'leader_email',
        'leader_phone',
        'leader_signature',
        'members__full_name',
        'members__email',
        'members__student_id',
        'members__ieee_membership_no',
    )
    readonly_fields = ('created_at',)
    inlines = [HackathonMemberPhase01Inline]
    actions = ('send_phase_2_email_selected',)

    @admin.action(description='Send/Resend Phase-2 email to leader of selected teams (Selected only)')
    def send_phase_2_email_selected(self, request, queryset):
        teams = queryset.filter(is_selected=True)
        if not teams.exists():
            self.message_user(request, 'No selected teams in current selection.', level=messages.WARNING)
            return
        from emails.views import send_hackathon_phase02_email
        send_hackathon_phase02_email(request, teams)
        self.message_user(request, f'Phase 2 invitation email processing finished for {teams.count()} team(s).', level=messages.SUCCESS)


@admin.register(HackathonFormStatus_Phase01)
class HackathonFormStatusPhase01Admin(admin.ModelAdmin):
    list_display = ('is_published', 'updated_at')
    readonly_fields = ('updated_at',)


# PHASE 2 ADMIN

class HackathonMemberPhase02Inline(admin.TabularInline):
    model = HackathonMember_Phase02
    extra = 0
    max_num = 3
    fields = (
        'member_order',
        'is_leader',
        'full_name',
        'email',
        'phone_number',
        'university',
        'department',
        'academic_year',
        'student_id',
        'gender',
        'is_ieee_member',
        'ieee_membership_no',
        'tshirt_size',
    )


@admin.register(HackathonTeam_Phase02)
class HackathonTeamPhase02Admin(admin.ModelAdmin):
    list_display = (
        'id',
        'team_name',
        'team_size',
        'leader_email',
        'leader_phone',
        'payment_method',
        'sender_number',
        'transaction_id',
        'is_payment_confirmed',
        'created_at',
    )
    list_filter = (
        'team_size',
        'payment_method',
        'is_payment_confirmed',
        'created_at',
    )
    search_fields = (
        'team_name',
        'leader_email',
        'leader_phone',
        'sender_number',
        'transaction_id',
        'members__full_name',
        'members__email',
        'members__student_id',
    )
    readonly_fields = ('created_at', 'updated_at')
    inlines = [HackathonMemberPhase02Inline]


@admin.register(HackathonMember_Phase02)
class HackathonMemberPhase02Admin(admin.ModelAdmin):
    list_display = (
        'id',
        'full_name',
        'team',
        'member_order',
        'is_leader',
        'university',
        'tshirt_size',
        'is_ieee_member',
    )
    list_filter = (
        'tshirt_size',
        'academic_year',
        'is_ieee_member',
        'gender',
    )
    search_fields = (
        'full_name',
        'email',
        'phone_number',
        'student_id',
        'team__team_name',
    )


@admin.register(HackathonTeam_Unique_Code_Phase_2)
class HackathonTeamUniqueCodePhase2Admin(admin.ModelAdmin):
    list_display = (
        'id',
        'team',
        'unique_code',
        'is_active',
        'created_at',
    )
    list_filter = (
        'is_active',
        'created_at',
    )
    search_fields = (
        'team__team_name',
        'unique_code',
    )
    readonly_fields = ('created_at',)


@admin.register(HackathonFormStatus_Phase02)
class HackathonFormStatusPhase02Admin(admin.ModelAdmin):
    list_display = ('is_published', 'updated_at')
    readonly_fields = ('updated_at',)
