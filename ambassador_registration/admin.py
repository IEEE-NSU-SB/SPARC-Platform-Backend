from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.html import format_html

from .models import Ambassador
from ambassador_email.models import MailJob
from ambassador_email.sender import build_service, process_job


class MailJobInline(admin.TabularInline):
    model = MailJob
    extra = 0
    can_delete = False
    readonly_fields = (
        'campaign', 'to_email', 'status_badge', 'error_display',
        'gmail_message_id', 'created_at', 'sent_at', 'resend_button'
    )
    fields = (
        'campaign', 'to_email', 'status_badge', 'error_display',
        'gmail_message_id', 'created_at', 'sent_at', 'resend_button'
    )

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description='Status')
    def status_badge(self, obj):
        if not obj.pk:
            return '-'
        colors = {
            MailJob.SENT: '#1a7f37',
            MailJob.FAILED: '#cf222e',
            MailJob.PENDING: '#9a6700',
            MailJob.SENDING: '#0969da',
        }
        return format_html(
            '<b style="color:{}">{}</b>', colors.get(obj.status, '#57606a'), obj.status.upper())

    @admin.display(description='Error')
    def error_display(self, obj):
        if obj.error:
            return format_html(
                '<span style="color:#cf222e; max-width:350px; display:inline-block; word-break:break-word;">{}</span>',
                obj.error
            )
        return '-'

    @admin.display(description='Action')
    def resend_button(self, obj):
        if not obj.pk:
            return '-'
        url = reverse('admin:ambassador_email_mailjob_resend', args=[obj.pk])
        label = "Resend" if obj.status == MailJob.SENT else "Send / Retry"
        force_param = "?force=1" if obj.status == MailJob.SENT else ""
        return format_html(
            '<a class="button" style="padding:2px 8px;font-size:11px;" href="{}{}">{}</a>',
            url, force_param, label
        )


class EmailStatusFilter(admin.SimpleListFilter):
    title = 'Email Status'
    parameter_name = 'email_status'

    def lookups(self, request, model_admin):
        return (
            ('sent', 'Sent'),
            ('failed', 'Failed'),
            ('pending', 'Pending'),
            ('sending', 'Sending'),
            ('no_job', 'Not Queued'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'sent':
            return queryset.filter(mailjob__campaign='ambassador_received', mailjob__status=MailJob.SENT)
        if self.value() == 'failed':
            return queryset.filter(mailjob__campaign='ambassador_received', mailjob__status=MailJob.FAILED)
        if self.value() == 'pending':
            return queryset.filter(mailjob__campaign='ambassador_received', mailjob__status=MailJob.PENDING)
        if self.value() == 'sending':
            return queryset.filter(mailjob__campaign='ambassador_received', mailjob__status=MailJob.SENDING)
        if self.value() == 'no_job':
            return queryset.exclude(mailjob__campaign='ambassador_received')
        return queryset


@admin.register(Ambassador)
class AmbassadorAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'photo_thumbnail', 'name', 'email', 'university',
        'year_of_study', 'is_ieee_member', 'email_status', 'email_action', 'created_at')
    list_filter = (
        EmailStatusFilter, 'year_of_study', 'gender', 'is_ieee_member',
        'heard_from', 'created_at'
    )
    search_fields = ('name', 'email', 'university', 'department', 'student_id')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'photo_thumbnail')
    inlines = [MailJobInline]
    actions = ('resend_failed_emails', 'force_resend_emails')

    fieldsets = (
        ('Section 1 - Personal information', {
            'fields': ('name', 'email', 'whatsapp', 'date_of_birth', 'gender'),
        }),
        ('Section 2 - University information', {
            'fields': ('university', 'department', 'year_of_study', 'student_id'),
        }),
        ('Section 3 - IEEE information', {
            'fields': ('is_ieee_member', 'ieee_number', 'ieee_grade',
                       'ieee_branch', 'ieee_position'),
        }),
        ('Section 4 - Photo for website, social media and ID', {
            'fields': ('photo', 'photo_thumbnail', 'bio'),
        }),
        ('Section 6 - About you', {
            'fields': ('why_ambassador', 'activities', 'heard_from'),
        }),
        ('Section 7 - Agreement (all four required)', {
            'fields': ('agree_info_accurate', 'agree_media_usage',
                       'agree_points_ranking', 'agree_contact_consent'),
        }),
        ('Timestamps', {'fields': ('created_at',)}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('mailjob_set')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:ambassador_id>/resend-email/',
                self.admin_site.admin_view(self.resend_single_email_view),
                name='ambassador_registration_ambassador_resend_email'
            ),
        ]
        return custom_urls + urls

    def resend_single_email_view(self, request, ambassador_id):
        if not self.has_change_permission(request):
            self.message_user(request, "Permission denied.", level=messages.ERROR)
            return redirect('..')

        amb = self.get_object(request, ambassador_id)
        if not amb:
            self.message_user(request, "Ambassador not found.", level=messages.ERROR)
            return redirect('..')

        try:
            service = build_service()
        except RuntimeError as exc:
            self.message_user(request, f'Cannot send now: {exc}', level=messages.ERROR)
            return redirect(request.META.get('HTTP_REFERER', '..'))

        force = request.GET.get('force') == '1'
        job, _ = MailJob.objects.get_or_create(
            campaign='ambassador_received',
            ambassador=amb,
            defaults={'to_email': amb.email}
        )
        result = process_job(job.id, service, force=force)
        if result and result.status == MailJob.SENT:
            self.message_user(
                request,
                f'Successfully sent confirmation email to {amb.name} ({amb.email}). MsgId: {result.gmail_message_id}',
                level=messages.SUCCESS
            )
        else:
            err = result.error if result else "Job vanished"
            self.message_user(
                request,
                f'Failed to send email to {amb.name} ({amb.email}): {err}',
                level=messages.ERROR
            )
        return redirect(request.META.get('HTTP_REFERER', '..'))

    @admin.display(description='Photo')
    def photo_thumbnail(self, obj):
        if obj and obj.photo:
            return format_html(
                '<img src="{}" style="max-height:120px;border-radius:6px">',
                obj.photo.url)
        return '-'

    @admin.display(description='Email Status')
    def email_status(self, obj):
        job = obj.mailjob_set.filter(campaign='ambassador_received').first()
        if not job:
            return format_html('<span style="color:#57606a;">Not Queued</span>')
        colors = {
            MailJob.SENT: '#1a7f37',
            MailJob.FAILED: '#cf222e',
            MailJob.PENDING: '#9a6700',
            MailJob.SENDING: '#0969da',
        }
        status_text = job.status.upper()
        if job.status == MailJob.FAILED and job.error:
            err_snip = (job.error[:50] + '...') if len(job.error) > 50 else job.error
            return format_html(
                '<b style="color:{}" title="{}">{}</b><br><small style="color:#cf222e;">{}</small>',
                colors.get(job.status, '#57606a'), job.error, status_text, err_snip
            )
        return format_html(
            '<b style="color:{}">{}</b>', colors.get(job.status, '#57606a'), status_text
        )

    @admin.display(description='Email Action')
    def email_action(self, obj):
        job = obj.mailjob_set.filter(campaign='ambassador_received').first()
        url = reverse('admin:ambassador_registration_ambassador_resend_email', args=[obj.pk])
        if not job:
            return format_html(
                '<a class="button" style="padding:2px 8px;font-size:11px;" href="{}">Send Mail</a>',
                url
            )
        if job.status == MailJob.SENT:
            return format_html(
                '<a class="button" style="padding:2px 8px;font-size:11px;opacity:0.85;" href="{}?force=1">Resend</a>',
                url
            )
        return format_html(
            '<a class="button" style="padding:2px 8px;font-size:11px;background:#cf222e;color:#fff;" href="{}">Send / Retry</a>',
            url
        )

    @admin.action(description='Send now: process Pending/Failed emails for selected ambassadors')
    def resend_failed_emails(self, request, queryset):
        """Processes pending or failed jobs for selected ambassadors."""
        self._send_for_ambassadors(request, queryset, force=False)

    @admin.action(description='Force resend confirmation email to selected ambassadors (including Sent)')
    def force_resend_emails(self, request, queryset):
        """Forces sending email even if already marked sent."""
        self._send_for_ambassadors(request, queryset, force=True)

    def _send_for_ambassadors(self, request, queryset, force=False):
        try:
            service = build_service()
        except RuntimeError as exc:
            self.message_user(
                request, f'Cannot send now: {exc}', level=messages.ERROR)
            return

        sent = failed = skipped = 0
        for amb in queryset.order_by('pk'):
            job, _ = MailJob.objects.get_or_create(
                campaign='ambassador_received',
                ambassador=amb,
                defaults={'to_email': amb.email}
            )
            if not force and job.status == MailJob.SENT:
                skipped += 1
                continue
            result = process_job(job.id, service, force=force)
            if result is None:
                continue
            if result.status == MailJob.SENT:
                sent += 1
            else:
                failed += 1

        if sent or failed:
            msg = f'Send now finished: {sent} sent, {failed} failed.'
            if skipped:
                msg += f' ({skipped} already-sent skipped)'
            level = messages.SUCCESS if failed == 0 else messages.WARNING
            self.message_user(request, msg, level=level)
        else:
            self.message_user(
                request, 'Nothing to send - selection contains only already-sent emails (use Force resend if needed).',
                level=messages.INFO
            )
