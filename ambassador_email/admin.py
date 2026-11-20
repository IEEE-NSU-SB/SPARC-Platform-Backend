from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.html import format_html

from .models import MailJob
from .sender import build_service, process_job


@admin.register(MailJob)
class MailJobAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'campaign', 'ambassador_name', 'to_email', 'status_badge',
        'gmail_message_id', 'created_at', 'sent_at', 'resend_action')
    list_filter = ('status', 'campaign', 'created_at')
    search_fields = ('to_email', 'ambassador__name', 'ambassador__email', 'gmail_message_id')
    readonly_fields = ('error', 'gmail_message_id', 'created_at', 'sent_at', 'resend_link')
    actions = ('retry_selected', 'force_resend_selected', 'reset_to_pending')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:job_id>/resend/',
                self.admin_site.admin_view(self.resend_job_view),
                name='ambassador_email_mailjob_resend'
            ),
        ]
        return custom_urls + urls

    def resend_job_view(self, request, job_id):
        if not self.has_change_permission(request):
            self.message_user(request, "Permission denied.", level=messages.ERROR)
            return redirect('..')

        job = self.get_object(request, job_id)
        if not job:
            self.message_user(request, "MailJob not found.", level=messages.ERROR)
            return redirect('..')

        try:
            service = build_service()
        except RuntimeError as exc:
            self.message_user(request, f'Cannot send now: {exc}', level=messages.ERROR)
            return redirect(request.META.get('HTTP_REFERER', '..'))

        force = request.GET.get('force') == '1'
        result = process_job(job.id, service, force=force)
        if result and result.status == MailJob.SENT:
            self.message_user(
                request,
                f'Successfully sent email to {result.to_email} (MsgId: {result.gmail_message_id}).',
                level=messages.SUCCESS
            )
        else:
            err = result.error if result else "Job vanished"
            self.message_user(
                request,
                f'Failed to send email to {job.to_email}: {err}',
                level=messages.ERROR
            )
        return redirect(request.META.get('HTTP_REFERER', '..'))

    @admin.display(description='Ambassador', ordering='ambassador__name')
    def ambassador_name(self, obj):
        return obj.ambassador.name

    @admin.display(description='Status', ordering='status')
    def status_badge(self, obj):
        colors = {
            MailJob.SENT: '#1a7f37',
            MailJob.FAILED: '#cf222e',
            MailJob.PENDING: '#9a6700',
            MailJob.SENDING: '#0969da',
        }
        status_text = obj.status.upper()
        if obj.status == MailJob.FAILED and obj.error:
            err_snip = (obj.error[:45] + '...') if len(obj.error) > 45 else obj.error
            return format_html(
                '<b style="color:{}" title="{}">{}</b><br><small style="color:#cf222e;">{}</small>',
                colors.get(obj.status, '#57606a'), obj.error, status_text, err_snip
            )
        return format_html(
            '<b style="color:{}">{}</b>', colors.get(obj.status, '#57606a'), status_text)

    @admin.display(description='Action')
    def resend_action(self, obj):
        url = reverse('admin:ambassador_email_mailjob_resend', args=[obj.pk])
        if obj.status == MailJob.SENT:
            return format_html(
                '<a class="button" style="padding:2px 8px;font-size:11px;opacity:0.85;" href="{}?force=1">Resend</a>',
                url
            )
        return format_html(
            '<a class="button" style="padding:2px 8px;font-size:11px;background:#cf222e;color:#fff;" href="{}">Send / Retry</a>',
            url
        )

    @admin.display(description='Resend Email')
    def resend_link(self, obj):
        if not obj or not obj.pk:
            return '-'
        url = reverse('admin:ambassador_email_mailjob_resend', args=[obj.pk])
        force_param = "?force=1" if obj.status == MailJob.SENT else ""
        label = "Resend Email Now (Force)" if obj.status == MailJob.SENT else "Send / Retry Email Now"
        return format_html(
            '<a class="button" style="background:#1b5c4a;color:#fff;padding:6px 12px;font-weight:600;" href="{}{}">{}</a>',
            url, force_param, label
        )

    @admin.action(
        description='Send now: process Pending/Failed jobs via the Gmail API')
    def retry_selected(self, request, queryset):
        """Manual retry from the admin: build one service, then run each
        selected job through process_job (which skips already-sent jobs)."""
        try:
            service = build_service()
        except RuntimeError as exc:
            self.message_user(
                request, f'Cannot send now: {exc}', level=messages.ERROR)
            return

        sent = failed = 0
        for job in queryset.exclude(status=MailJob.SENT).order_by('pk'):
            result = process_job(job.id, service)
            if result is None:
                continue
            if result.status == MailJob.SENT:
                sent += 1
            else:
                failed += 1
        if sent or failed:
            self.message_user(
                request, f'Send now finished: {sent} sent, {failed} failed.')
        else:
            self.message_user(
                request, 'Nothing to send - selection contains only '
                         'already-sent jobs.')

    @admin.action(description='Force resend selected jobs via Gmail API (including Sent)')
    def force_resend_selected(self, request, queryset):
        """Forces sending email even if already marked SENT."""
        try:
            service = build_service()
        except RuntimeError as exc:
            self.message_user(
                request, f'Cannot send now: {exc}', level=messages.ERROR)
            return

        sent = failed = 0
        for job in queryset.order_by('pk'):
            result = process_job(job.id, service, force=True)
            if result is None:
                continue
            if result.status == MailJob.SENT:
                sent += 1
            else:
                failed += 1
        self.message_user(
            request, f'Force send finished: {sent} sent, {failed} failed.')

    @admin.action(description='Reset Failed jobs to Pending (for send_pending command)')
    def reset_to_pending(self, request, queryset):
        updated = queryset.filter(status=MailJob.FAILED).update(status=MailJob.PENDING, error='')
        if updated:
            self.message_user(request, f'{updated} failed job(s) reset to Pending.')
        else:
            self.message_user(request, 'No failed jobs in selection.')
