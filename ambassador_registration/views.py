import json
from io import BytesIO
from threading import Thread

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import BooleanField, Case, Count, Q, Value, When
from django.db.models.functions import Trim
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from access_ctrl.decorators import permission_required
from access_ctrl.utils import Site_Permissions
from ambassador_email.models import MailJob
from ambassador_email.sender import process_job_in_thread
from hackathon.utils import get_phase01_tab_counts
from system_administration.utils import log_exception

from .forms import DUPLICATE_EMAIL_MSG, AmbassadorForm
from .models import Ambassador, AmbassadorFormStatus
from .ratelimit import is_rate_limited

RATE_LIMIT_MSG = 'Too many submissions from this IP address. Please wait before trying again.'
CLOSED_MSG = 'Ambassador registration is currently closed.'


def _get_publish_status() -> bool:
    status = AmbassadorFormStatus.objects.order_by('-updated_at').first()
    return bool(status and status.is_published)


def _is_ajax(request):
    """form.js marks its fetch() calls with X-Requested-With: XMLHttpRequest."""
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _errors_for_json(form):
    """Shape the errors for form.js renderErrors(): {field: ['msg', ...]}."""
    return {
        field: [err['message'] for err in messages]
        for field, messages in form.errors.get_json_data().items()
    }


def _staff_permissions(user) -> dict:
    return {
        'reg_form_control': Site_Permissions.user_has_permission(user, 'reg_form_control'),
        'view_reg_responses_list': Site_Permissions.user_has_permission(user, 'view_reg_responses_list'),
        'view_finance_info': Site_Permissions.user_has_permission(user, 'view_finance_info'),
        'view_qr_dashboard': Site_Permissions.user_has_permission(user, 'view_qr_dashboard'),
    }


def ambassador_apply(request):
    """Show and process the SPARC Ambassador application form.

    GET  -> redirect staff/permitted admins to admin_ambassador (unless ?preview=1),
            otherwise render the form or closed state depending on publish status.
    POST -> validate publish status + rate limit + AmbassadorForm; on success save
            the application FIRST and answer immediately. The background mail job
            is created and dispatched via transaction.on_commit. AJAX callers get
            JSON; plain browser posts get the /thanks/ page or the form
            re-rendered with field errors.
    """
    is_privileged = request.user.is_authenticated and (
        request.user.is_staff
        or Site_Permissions.user_has_permission(request.user, 'reg_form_control')
    )
    is_published = _get_publish_status()

    if request.method == 'POST':
        if not is_privileged and not is_published:
            if _is_ajax(request):
                return JsonResponse({
                    'success': False,
                    'message': CLOSED_MSG,
                    'errors': {'__all__': [CLOSED_MSG]},
                }, status=403)
            return render(
                request,
                'ambassador_registration/apply.html',
                {
                    'form': AmbassadorForm(),
                    'is_staff_view': False,
                    'is_published': False,
                    'registration_closed': False,
                },
                status=403,
            )

        if is_rate_limited(request, action='ambassador_apply'):
            if _is_ajax(request):
                return JsonResponse({
                    'success': False,
                    'message': RATE_LIMIT_MSG,
                    'errors': {'__all__': [RATE_LIMIT_MSG]},
                }, status=429)
            form = AmbassadorForm(request.POST, request.FILES)
            form.add_error(None, RATE_LIMIT_MSG)
            return render(
                request,
                'ambassador_registration/apply.html',
                {
                    'form': form,
                    'is_staff_view': is_privileged,
                    'is_published': is_published,
                    'registration_closed': False,
                },
                status=429,
            )

        form = AmbassadorForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                with transaction.atomic():
                    ambassador = form.save()

                    job, _ = MailJob.objects.get_or_create(
                        campaign='ambassador_received',
                        ambassador=ambassador,
                        defaults={'to_email': ambassador.email})
                    transaction.on_commit(lambda: Thread(
                        target=process_job_in_thread, args=(job.id,),
                        daemon=True).start())
            except IntegrityError:
                form.add_error('email', DUPLICATE_EMAIL_MSG)
                if _is_ajax(request):
                    return JsonResponse({'success': False,
                                         'errors': _errors_for_json(form)},
                                        status=400)
                return render(
                    request,
                    'ambassador_registration/apply.html',
                    {
                        'form': form,
                        'is_staff_view': is_privileged,
                        'is_published': is_published,
                        'registration_closed': False,
                    },
                )

            if _is_ajax(request):
                return JsonResponse({
                    'success': True,
                    'message': 'Application received. Thank you!',
                })
            return redirect('ambassador_registration:thanks')

        if _is_ajax(request):
            return JsonResponse({'success': False,
                                 'errors': _errors_for_json(form)}, status=400)

        # Non-JavaScript path: re-render with the submitted values and the
        # server-rendered error lists (the template shows {{ form.x.errors }}).
        return render(
            request,
            'ambassador_registration/apply.html',
            {
                'form': form,
                'is_staff_view': is_privileged,
                'is_published': is_published,
                'registration_closed': False,
            },
        )

    # GET: Redirect staff/permitted users to admin view unless previewing live form
    preview_mode = request.GET.get('preview') == '1'
    if not preview_mode:
        if request.user.is_authenticated and request.user.is_staff:
            return redirect('ambassador_registration:admin_ambassador')

        if request.user.is_authenticated:
            if not Site_Permissions.user_has_permission(request.user, 'reg_form_control'):
                return redirect('core:dashboard')
            elif not Site_Permissions.user_has_permission(request.user, 'view_qr_dashboard'):
                return redirect('ambassador_registration:admin_ambassador')
            else:
                return redirect('core:dashboard')

    ambassador_count = Ambassador.objects.count()
    registration_closed = ambassador_count >= 10000

    return render(
        request,
        'ambassador_registration/apply.html',
        {
            'form': AmbassadorForm(),
            'is_staff_view': False,
            'is_published': is_published,
            'registration_closed': registration_closed,
        },
    )


def thanks(request):
    """Confirmation page for non-JavaScript submissions."""
    return render(request, 'ambassador_registration/thanks.html')


@login_required
@permission_required('reg_form_control')
def admin_ambassador(request):
    """Staff-only preview and control view for the Ambassador Application form."""
    registration_count = Ambassador.objects.count()
    context = {
        'form': AmbassadorForm(),
        'is_staff_view': True,
        'is_published': _get_publish_status(),
        'registration_count': registration_count,
        'has_perm': _staff_permissions(request.user),
    }
    return render(request, 'ambassador_registration/apply.html', context)


@login_required
@permission_required('reg_form_control')
@require_POST
def toggle_publish(request):
    """Independently toggles Ambassador form public availability."""
    status = AmbassadorFormStatus.objects.order_by('-updated_at').first()
    if not status:
        status = AmbassadorFormStatus.objects.create(is_published=True)
    else:
        status.is_published = not status.is_published
        status.save(update_fields=['is_published', 'updated_at'])

    return JsonResponse({'success': True, 'is_published': status.is_published})


@login_required
@permission_required('view_reg_responses_list')
def response_table(request):
    """Admin response table for Ambassador applications with folder tabs and statistics."""
    permissions = {
        'view_finance_info': Site_Permissions.user_has_permission(request.user, 'view_finance_info'),
        'reg_form_control': Site_Permissions.user_has_permission(request.user, 'reg_form_control'),
    }

    ambassadors = Ambassador.objects.all().order_by('created_at')

    reg_stats = Ambassador.objects.aggregate(
        total_ambassadors=Count('id'),
        total_selected=Count('id', filter=Q(is_selected=True)),
        ieee_members=Count('id', filter=Q(is_ieee_member=True)),
        non_ieee_members=Count('id', filter=Q(is_ieee_member=False)),
        male_count=Count('id', filter=Q(gender=Ambassador.GENDER_MALE)),
        female_count=Count('id', filter=Q(gender=Ambassador.GENDER_FEMALE)),
    )

    university_data = (
        Ambassador.objects
        .exclude(university__isnull=True)
        .exclude(university='')
        .annotate(university_sanitized=Trim('university'))
        .values('university_sanitized')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    year_labels = dict(Ambassador.YEAR_CHOICES)
    raw_year_data = (
        Ambassador.objects
        .values('year_of_study')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    year_data = [
        {
            'label': year_labels.get(row['year_of_study'], row['year_of_study']),
            'total': row['total'],
        }
        for row in raw_year_data
    ]

    context = {
        'ambassadors': ambassadors,
        'reg_stats': reg_stats,
        'university_data': university_data,
        'year_data': year_data,
        'tab_counts': get_phase01_tab_counts(),
        'has_perm': permissions,
    }
    return render(request, 'ambassador_registration/ambassador_response_table.html', context)


@login_required
def view_response(request, id):
    """Detailed view for a single Ambassador application."""
    if not (
        request.user.is_superuser
        or Site_Permissions.user_has_permission(request.user, 'view_reg_response')
        or Site_Permissions.user_has_permission(request.user, 'view_reg_responses_list')
        or Site_Permissions.user_has_permission(request.user, 'reg_form_control')
    ):
        return render(request, 'AccessDenied.html')

    ambassador = get_object_or_404(Ambassador, id=id)
    activity_labels = dict(Ambassador.ACTIVITY_CHOICES)
    readable_activities = [
        activity_labels.get(key, key) for key in (ambassador.activities or [])
    ]

    context = {
        'ambassador': ambassador,
        'readable_activities': readable_activities,
    }
    return render(request, 'ambassador_registration/ambassador_response_detail.html', context)


@login_required
@permission_required('reg_form_control')
@require_POST
def save_selected(request):
    """Bulk updates is_selected status for Ambassador applications."""
    try:
        data = json.loads(request.body)
        raw_ids = data.get('selected_ids', [])
        if not isinstance(raw_ids, list):
            return JsonResponse(
                {'message': 'selected_ids must be a list.', 'status': 'error'},
                status=400,
            )

        selected_ids = [int(x) for x in raw_ids if str(x).isdigit()]

        Ambassador.objects.update(
            is_selected=Case(
                When(id__in=selected_ids, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
        return JsonResponse(
            {'message': 'Ambassador selections updated successfully!', 'status': 'success'}
        )
    except Exception as exc:
        log_exception(exc, request)
        return JsonResponse(
            {'message': 'Error saving ambassador selections.', 'status': 'error'},
            status=500,
        )


@login_required
@permission_required('reg_form_control')
@require_GET
def download_excel(request):
    """Exports Ambassador applications as a 3-sheet Excel workbook:
    1. Ambassador Name (basic info)
    2. University Name (university & academic info)
    3. IEEE Members (filtered IEEE members)
    """
    ambassadors = Ambassador.objects.all().order_by('created_at')
    activity_labels = dict(Ambassador.ACTIVITY_CHOICES)

    ambassador_basic_data = []
    university_info_data = []
    ieee_data = []

    for amb in ambassadors:
        activities_str = ', '.join(
            activity_labels.get(k, k) for k in (amb.activities or [])
        )
        ambassador_basic_data.append({
            'ID': amb.id,
            'Full Name': amb.name,
            'Email': amb.email,
            'WhatsApp': amb.whatsapp,
            'Date of Birth': amb.date_of_birth.strftime('%Y-%m-%d') if amb.date_of_birth else '',
            'Gender': amb.get_gender_display(),
            'Bio': amb.bio,
            'Why Ambassador': amb.why_ambassador,
            'Activities': activities_str,
            'Heard From': amb.get_heard_from_display(),
            'Selected': 'Yes' if amb.is_selected else 'No',
            'Submitted At': amb.created_at.astimezone().strftime('%Y-%m-%d %H:%M:%S'),
        })

        university_info_data.append({
            'ID': amb.id,
            'Full Name': amb.name,
            'Email': amb.email,
            'University': amb.university,
            'Department': amb.department,
            'Year of Study': amb.get_year_of_study_display(),
            'Student ID': amb.student_id,
        })

        if amb.is_ieee_member:
            ieee_data.append({
                'ID': amb.id,
                'Full Name': amb.name,
                'Email': amb.email,
                'University': amb.university,
                'IEEE Membership No': amb.ieee_number,
                'Membership Grade': amb.get_ieee_grade_display() if amb.ieee_grade else '',
                'IEEE Student Branch': amb.ieee_branch,
                'Branch Position': amb.ieee_position,
            })

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if ambassador_basic_data:
            pd.DataFrame(ambassador_basic_data).to_excel(
                writer, index=False, sheet_name='Ambassador Name'
            )
        else:
            pd.DataFrame({'Message': ['No ambassadors registered yet']}).to_excel(
                writer, index=False, sheet_name='Ambassador Name'
            )

        if university_info_data:
            pd.DataFrame(university_info_data).to_excel(
                writer, index=False, sheet_name='University Name'
            )
        else:
            pd.DataFrame({'Message': ['No university data recorded yet']}).to_excel(
                writer, index=False, sheet_name='University Name'
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
    response['Content-Disposition'] = 'attachment; filename="ambassador_data.xlsx"'
    return response
