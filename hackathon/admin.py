from django.contrib import admin
from .models import (
    HackathonFormStatus_Phase01,
    HackathonMember_Phase01,
    HackathonTeam_Phase01,
)

# Register your models here

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


@admin.register(HackathonFormStatus_Phase01)
class HackathonFormStatusPhase01Admin(admin.ModelAdmin):
    list_display = ('is_published', 'updated_at')
    readonly_fields = ('updated_at',)