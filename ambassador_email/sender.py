import base64
import logging
from email.message import EmailMessage

from django.conf import settings
from django.core.validators import validate_email
from django.db import connection
from django.template.loader import render_to_string
from django.utils import timezone
from googleapiclient.discovery import build

from .models import MailJob
from emails.views import get_credentials

logger = logging.getLogger('ambassador_email')

SUBJECT = 'SPARC 2026 - Ambassador Application Received'


def build_service():
    creds = get_credentials()
    if not creds:
        raise RuntimeError('Google API needs re-authorisation')
    return build(settings.GOOGLE_MAIL_API_NAME,
                 settings.GOOGLE_MAIL_API_VERSION,
                 credentials=creds, cache_discovery=False)


def send_mail(service, to, name):
    validate_email(to)
    msg = EmailMessage()
    msg['From'] = getattr(settings, 'MAIL_SENDER', 'IEEE NSU SB Portal <ieeensusb.portal@gmail.com>')
    msg['To'] = to
    msg['Subject'] = SUBJECT
    msg.set_content(render_to_string('ambassador_email/ambassador_received.txt', {'name': name}))
    msg.add_alternative(
        render_to_string('ambassador_email/ambassador_received.html', {'name': name}),
        subtype='html')
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return service.users().messages().send(
        userId='me', body={'raw': raw}).execute()['id']


def process_job(job_id, service=None):
    try:
        job = MailJob.objects.select_related('ambassador').get(pk=job_id)
    except MailJob.DoesNotExist:
        logger.warning('[SKIP] MailJob %s vanished (deleted?)', job_id)
        return None

    # Atomic claim: a single conditional UPDATE means exactly one processor
    # (view thread / send_pending / admin action) can win.
    claimed = MailJob.objects.filter(
        pk=job.pk,
        status__in=[MailJob.PENDING, MailJob.SENDING, MailJob.FAILED],
    ).update(status=MailJob.SENDING)
    if not claimed:
        return job  # already SENT - never send twice

    if job.status == MailJob.SENDING:
        logger.warning('[RETRY] MailJob %s stuck in sending - taking over', job.pk)

    a = job.ambassador
    try:
        job.gmail_message_id = send_mail(
            service or build_service(), job.to_email, a.name)
        job.status, job.error, job.sent_at = MailJob.SENT, '', timezone.now()
        logger.info(f'[OK] ID={a.id} Name={a.name} Email={job.to_email} '
                    f'MsgId={job.gmail_message_id}')
    except Exception as exc:
        job.status, job.error = MailJob.FAILED, str(exc)[:500]
        logger.error(f'[FAIL] ID={a.id} Name={a.name} Reason={job.error}')
    job.save()
    return job


def process_job_in_thread(job_id):
    try:
        process_job(job_id)
    except Exception:
        logger.exception('[FAIL] job %s crashed the sender thread', job_id)
    finally:
        connection.close()
