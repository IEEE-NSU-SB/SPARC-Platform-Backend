import json
import re
from io import BytesIO

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import BooleanField, Case, Count, Q, Sum, Value, When
from django.db.models.functions import Trim
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from access_ctrl.decorators import permission_required
from access_ctrl.utils import Site_Permissions
from system_administration.utils import log_exception

from .models import (
    HackathonFormStatus_Phase01,
    HackathonMember_Phase01,
    HackathonTeam_Phase01,
)
from .utils import get_phase01_tab_counts

# Create your views here


def _get_publish_status_phase01() -> bool:
    status = HackathonFormStatus_Phase01.objects.order_by('-updated_at').first()
    return bool(status and status.is_published)


def _normalize_phone(raw_value: str) -> str:
    """Removes spaces or dashes from phone input before regex validation."""
    return re.sub(r'[\s\-]+', '', (raw_value or '').strip())


def form_phase01(request):
    """Public Hackathon Phase 1 registration form. Redirects staff/permitted admins to admin preview."""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('hackathon:admin_phase01')

    if request.user.is_authenticated:
        if not Site_Permissions.user_has_permission(request.user, 'reg_form_control'):
            return redirect('core:dashboard')
        elif not Site_Permissions.user_has_permission(request.user, 'view_qr_dashboard'):
            return redirect('hackathon:admin_phase01')
        else:
            return redirect('core:dashboard')

    team_count = HackathonTeam_Phase01.objects.count()
    registration_closed = team_count >= 10000

    context = {
        'is_staff_view': False,
        'is_published': _get_publish_status_phase01(),
        'registration_closed': registration_closed,
    }
    return render(request, 'hackathon_form_phase01.html', context)


@login_required
@permission_required('reg_form_control')
def admin_phase01(request):
    """Staff-only preview and control view for the Hackathon Phase 1 form."""
    registration_count = HackathonTeam_Phase01.objects.count()
    people_count = (
        HackathonTeam_Phase01.objects.aggregate(total=Sum('team_size'))['total'] or 0
    )

    permissions = {
        'reg_form_control': Site_Permissions.user_has_permission(request.user, 'reg_form_control'),
        'view_reg_responses_list': Site_Permissions.user_has_permission(request.user, 'view_reg_responses_list'),
        'view_finance_info': Site_Permissions.user_has_permission(request.user, 'view_finance_info'),
        'view_qr_dashboard': Site_Permissions.user_has_permission(request.user, 'view_qr_dashboard'),
    }

    context = {
        'is_staff_view': True,
        'is_published': _get_publish_status_phase01(),
        'registration_count': registration_count,
        'people_count': people_count,
        'has_perm': permissions,
    }
    return render(request, 'hackathon_form_phase01.html', context)


@login_required
@permission_required('reg_form_control')
@require_POST
def toggle_publish_phase01(request):
    """Independently toggles Hackathon Phase 1 public availability."""
    status = HackathonFormStatus_Phase01.objects.order_by('-updated_at').first()
    if not status:
        status = HackathonFormStatus_Phase01.objects.create(is_published=True)
    else:
        status.is_published = not status.is_published
        status.save(update_fields=['is_published', 'updated_at'])

    return JsonResponse({'success': True, 'is_published': status.is_published})


@require_POST
def submit_phase01(request):
    """Atomically validates and saves a Hackathon Phase 1 team and its 2 or 3 members."""
    try:
        is_privileged = request.user.is_authenticated and (
            request.user.is_staff
            or Site_Permissions.user_has_permission(request.user, 'reg_form_control')
        )
        if not is_privileged and not _get_publish_status_phase01():
            return JsonResponse(
                {'success': False, 'message': 'Hackathon registration form is currently closed.'},
                status=403,
            )

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {'success': False, 'message': 'Invalid request payload format.'},
                status=400,
            )

        try:
            team_size = int(payload.get('team_size', 0))
        except (TypeError, ValueError):
            team_size = 0

        if team_size not in (2, 3):
            return JsonResponse(
                {'success': False, 'message': 'Team size must be either 2 or 3 members.'},
                status=400,
            )

        members_data = payload.get('members', [])
        if not isinstance(members_data, list) or len(members_data) != team_size:
            return JsonResponse(
                {
                    'success': False,
                    'message': f'Expected {team_size} member entries, received {len(members_data) if isinstance(members_data, list) else 0}.',
                },
                status=400,
            )

        agreements = payload.get('agreements', {}) or {}
        leader_email = (payload.get('leader_email') or '').strip()
        leader_phone = _normalize_phone(payload.get('leader_phone', ''))

        with transaction.atomic():
            team = HackathonTeam_Phase01(
                team_name=(payload.get('team_name') or '').strip(),
                team_size=team_size,
                university_distribution=(payload.get('university_distribution') or '').strip(),
                leader_email=leader_email,
                leader_phone=leader_phone,
                agreed_enrolled_students=bool(agreements.get('enrolled_students')),
                agreed_member_consent=bool(agreements.get('member_consent')),
                agreed_composition_final=bool(agreements.get('composition_final')),
                agreed_rules_plagiarism=bool(agreements.get('rules_plagiarism')),
                agreed_originality=bool(agreements.get('originality')),
                agreed_announcements=bool(agreements.get('announcements')),
                agreed_media_permission=bool(agreements.get('media_permission')),
                leader_signature=(payload.get('leader_signature') or '').strip(),
            )
            team.full_clean()
            team.save()

            seen_emails = set()
            seen_student_ids = set()

            for index, m_data in enumerate(members_data, start=1):
                is_leader = (index == 1)
                role_label = "Team Leader" if is_leader else f"Member {index}"

                # Keep Member 1 contact info synchronized with Section 1 leader contact
                member_email = (
                    leader_email if is_leader else (m_data.get('email') or '').strip()
                )
                member_phone = (
                    leader_phone if is_leader else _normalize_phone(m_data.get('phone_number', ''))
                )
                student_id = (m_data.get('student_id') or '').strip()

                if member_email.lower() in seen_emails:
                    raise ValidationError(
                        {f'member_{index}_email': f'{role_label} cannot share the same email as another teammate.'}
                    )
                if student_id and student_id.lower() in seen_student_ids:
                    raise ValidationError(
                        {f'member_{index}_student_id': f'{role_label} cannot share the same Student ID as another teammate.'}
                    )

                seen_emails.add(member_email.lower())
                if student_id:
                    seen_student_ids.add(student_id.lower())

                raw_ieee = m_data.get('is_ieee_member', False)
                is_ieee = (
                    raw_ieee if isinstance(raw_ieee, bool)
                    else str(raw_ieee).strip().lower() in ('true', 'yes', '1')
                )

                raw_gender = (m_data.get('gender') or '').strip()

                member = HackathonMember_Phase01(
                    team=team,
                    member_order=index,
                    is_leader=is_leader,
                    full_name=(m_data.get('full_name') or '').strip(),
                    email=member_email,
                    phone_number=member_phone,
                    university=(m_data.get('university') or '').strip(),
                    department=(m_data.get('department') or '').strip(),
                    academic_year=(m_data.get('academic_year') or '').strip(),
                    student_id=student_id,
                    gender=raw_gender if raw_gender else None,
                    is_ieee_member=is_ieee,
                    ieee_membership_no=(m_data.get('ieee_membership_no') or '').strip() if is_ieee else '',
                    ieee_membership_grade=(m_data.get('ieee_membership_grade') or '').strip() if is_ieee else '',
                    ieee_student_branch=(m_data.get('ieee_student_branch') or '').strip() if is_ieee else '',
                    ieee_volunteer_position=(m_data.get('ieee_volunteer_position') or '').strip() if is_ieee else '',
                )
                try:
                    member.full_clean()
                except ValidationError as member_exc:
                    if hasattr(member_exc, 'message_dict'):
                        prefixed = {
                            f'member_{index}_{field}': msgs
                            for field, msgs in member_exc.message_dict.items()
                        }
                        raise ValidationError(prefixed)
                    raise ValidationError({f'member_{index}': member_exc.messages})

                member.save()

        # TODO (Step 8): Trigger hackathon Phase 1 confirmation email via emails.views
        # send_hackathon_registration_email_phase01(request, team)

        return JsonResponse(
            {
                'success': True,
                'message': f'Registration successful! Team "{team.team_name}" has been registered (Team ID: {team.id}).',
                'team_id': team.id,
                'team_name': team.team_name,
            },
            status=201,
        )

    except ValidationError as exc:
        errors = exc.message_dict if hasattr(exc, 'message_dict') else {'__all__': exc.messages}
        return JsonResponse(
            {
                'success': False,
                'message': 'Please fix the highlighted validation errors and try again.',
                'errors': errors,
            },
            status=400,
        )
    except Exception as exc:
        log_exception(exc, request)
        return JsonResponse(
            {'success': False, 'message': 'Registration failed due to an unexpected server error.'},
            status=500,
        )


@login_required
@permission_required('view_reg_responses_list')
def response_table_phase01(request):
    """Admin response table for Hackathon Phase 1 teams with shared folder-tab counts and statistics."""
    permissions = {
        'view_finance_info': Site_Permissions.user_has_permission(request.user, 'view_finance_info'),
        'reg_form_control': Site_Permissions.user_has_permission(request.user, 'reg_form_control'),
    }

    teams = (
        HackathonTeam_Phase01.objects
        .prefetch_related('members')
        .all()
        .order_by('created_at')
    )

    reg_stats = HackathonTeam_Phase01.objects.aggregate(
        total_teams=Count('id'),
        total_participants=Sum('team_size'),
        total_selected=Count('id', filter=Q(is_selected=True)),
        teams_of_2=Count('id', filter=Q(team_size=2)),
        teams_of_3=Count('id', filter=Q(team_size=3)),
        single_uni_teams=Count('id', filter=Q(university_distribution='single')),
        multi_uni_teams=Count('id', filter=Q(university_distribution='multiple')),
    )
    reg_stats['total_participants'] = reg_stats['total_participants'] or 0

    member_stats = HackathonMember_Phase01.objects.aggregate(
        ieee_members=Count('id', filter=Q(is_ieee_member=True)),
        non_ieee_members=Count('id', filter=Q(is_ieee_member=False)),
    )

    university_data = (
        HackathonMember_Phase01.objects
        .exclude(university__isnull=True)
        .exclude(university='')
        .annotate(university_sanitized=Trim('university'))
        .values('university_sanitized')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    context = {
        'teams': teams,
        'reg_stats': reg_stats,
        'member_stats': member_stats,
        'university_data': university_data,
        'tab_counts': get_phase01_tab_counts(),
        'has_perm': permissions,
    }
    return render(request, 'hackathon_response_table_phase01.html', context)


@login_required
def view_response_phase01(request, id):
    """Detailed view for a single Hackathon Phase 1 team and all its members."""
    if not (
        request.user.is_superuser
        or Site_Permissions.user_has_permission(request.user, 'view_reg_response')
        or Site_Permissions.user_has_permission(request.user, 'view_reg_responses_list')
        or Site_Permissions.user_has_permission(request.user, 'reg_form_control')
    ):
        return render(request, "AccessDenied.html")

    team = get_object_or_404(
        HackathonTeam_Phase01.objects.prefetch_related('members'),
        id=id,
    )
    context = {
        'team': team,
        'members': team.members.all(),
    }
    return render(request, 'hackathon_team_response_phase01.html', context)


@login_required
@permission_required('reg_form_control')
@require_POST
def save_selected_phase01(request):
    """Bulk updates is_selected status for Hackathon Phase 1 teams."""
    try:
        data = json.loads(request.body)
        raw_ids = data.get('selected_ids', [])
        if not isinstance(raw_ids, list):
            return JsonResponse(
                {'message': 'selected_ids must be a list.', 'status': 'error'},
                status=400,
            )

        selected_ids = [int(x) for x in raw_ids if str(x).isdigit()]

        HackathonTeam_Phase01.objects.update(
            is_selected=Case(
                When(id__in=selected_ids, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
        return JsonResponse(
            {'message': 'Team selections updated successfully!', 'status': 'success'}
        )
    except Exception as exc:
        log_exception(exc, request)
        return JsonResponse(
            {'message': 'Error saving team selections.', 'status': 'error'},
            status=500,
        )


@login_required
@permission_required('reg_form_control')
@require_GET
def download_excel_phase01(request):
    """Exports Hackathon Phase 1 registrations as a 3-sheet Excel workbook (no T-shirt fields)."""
    teams = (
        HackathonTeam_Phase01.objects
        .prefetch_related('members')
        .all()
        .order_by('created_at')
    )

    teams_data = []
    participants_data = []
    ieee_data = []

    for team in teams:
        teams_data.append({
            'Team ID': team.id,
            'Team Name': team.team_name,
            'Team Size': team.team_size,
            'University Distribution': team.get_university_distribution_display(),
            'Leader Email': team.leader_email,
            'Leader Phone': team.leader_phone,
            'Leader Signature': team.leader_signature,
            'Selected': 'Yes' if team.is_selected else 'No',
            'Phase 2 Email Sent': 'Yes' if team.is_phase_2_email_sent else 'No',
            'Created At': team.created_at.astimezone().strftime('%Y-%m-%d %H:%M:%S'),
        })

        for member in team.members.all():
            role = 'Team Leader' if member.is_leader else f'Member {member.member_order}'
            participants_data.append({
                'Team ID': team.id,
                'Team Name': team.team_name,
                'Role': role,
                'Full Name': member.full_name,
                'Email': member.email,
                'Phone / WhatsApp': member.phone_number,
                'University': member.university,
                'Department': member.department,
                'Academic Year': member.get_academic_year_display(),
                'Student ID': member.student_id,
                'Gender': member.get_gender_display() if member.gender else '',
                'IEEE Member': 'Yes' if member.is_ieee_member else 'No',
                'IEEE Membership No': member.ieee_membership_no,
                'Membership Grade': member.ieee_membership_grade,
                'IEEE Student Branch': member.ieee_student_branch,
                'Officer / Volunteer Position': member.ieee_volunteer_position,
            })

            if member.is_ieee_member:
                ieee_data.append({
                    'Team ID': team.id,
                    'Team Name': team.team_name,
                    'Role': role,
                    'Full Name': member.full_name,
                    'Email': member.email,
                    'IEEE Membership No': member.ieee_membership_no,
                    'Membership Grade': member.ieee_membership_grade,
                    'IEEE Student Branch': member.ieee_student_branch,
                    'Officer / Volunteer Position': member.ieee_volunteer_position,
                })

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if teams_data:
            pd.DataFrame(teams_data).to_excel(writer, index=False, sheet_name='Teams')
        else:
            pd.DataFrame({'Message': ['No hackathon teams registered']}).to_excel(
                writer, index=False, sheet_name='Teams'
            )

        if participants_data:
            pd.DataFrame(participants_data).to_excel(
                writer, index=False, sheet_name='Participants'
            )
        else:
            pd.DataFrame({'Message': ['No hackathon participants registered']}).to_excel(
                writer, index=False, sheet_name='Participants'
            )

        if ieee_data:
            pd.DataFrame(ieee_data).to_excel(
                writer, index=False, sheet_name='IEEE Members'
            )
        else:
            pd.DataFrame({'Message': ['No IEEE members registered yet']}).to_excel(
                writer, index=False, sheet_name='IEEE Members'
            )

    output.seek(0)
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename="hackathon_phase01_data.xlsx"'
    return response