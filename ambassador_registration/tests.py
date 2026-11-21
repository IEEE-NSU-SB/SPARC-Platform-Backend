"""Test suite for the ambassador_registration app.

Covers the verification requirements:
- models: unique email, one row per application, MailJob constraint/cascade
- form:   every validation rule (conditional IEEE, 50-word bio, photo
          type/size, WhatsApp format, agreements, activity whitelist,
          unique email)
- views:  GET renders the form, POST success/duplicate/error flows with the
          exact AJAX JSON contract, /thanks/, mail-job hook after commit
- admin:  both models registered, changelists render
"""
import json
import shutil
import tempfile
from io import BytesIO
from pathlib import Path
from unittest import mock

from django.contrib import admin as django_admin
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from ambassador_email.models import MailJob

from .forms import AmbassadorForm
from .models import Ambassador, AmbassadorFormStatus


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------

def jpeg_bytes(size=(40, 40)):
    buf = BytesIO()
    Image.new('RGB', size, (10, 10, 10)).save(buf, 'JPEG')
    return buf.getvalue()


def png_bytes():
    buf = BytesIO()
    Image.new('RGB', (30, 30), (1, 2, 3)).save(buf, 'PNG')
    return buf.getvalue()


def oversized_png_bytes():
    """A valid PNG padded past the 10 MB limit."""
    return png_bytes() + b'\x00' * (10 * 1024 * 1024)


def photo_file(name='photo.jpg', data=None):
    return SimpleUploadedFile(
        name, data if data is not None else jpeg_bytes(), content_type='image/jpeg')


def valid_data(**overrides):
    payload = {
        'name': 'Test Applicant',
        'email': 'applicant@example.com',
        'whatsapp': '+8801712345678',
        'date_of_birth': '2000-01-01',
        'gender': 'female',
        'university': 'North South University',
        'department': 'CSE',
        'year_of_study': '2nd',
        'student_id': 'NSU-203',
        'is_ieee_member': 'False',
        'ieee_number': '', 'ieee_grade': '', 'ieee_branch': '', 'ieee_position': '',
        'bio': 'A short bio with a few words only.',
        'why_ambassador': 'I love SPARC.',
        'activities': ['social_media_posts'],
        'heard_from': 'friend',
        'agree_info_accurate': 'on',
        'agree_media_usage': 'on',
        'agree_points_ranking': 'on',
        'agree_contact_consent': 'on',
    }
    for key, value in overrides.items():
        if value is None:
            payload.pop(key, None)
        else:
            payload[key] = value
    return payload


def valid_files(**overrides):
    overrides.setdefault('photo', photo_file())
    return {key: value for key, value in overrides.items() if value is not None}


def full_post_payload(**overrides):
    payload = valid_data(**overrides)
    payload.update(valid_files())
    return payload


class MediaRootMixin:
    """Point MEDIA_ROOT at a fresh temp dir; remove it afterwards."""

    def setUp(self):
        super().setUp()
        self._media_root = tempfile.mkdtemp(prefix='sparc-test-media-')
        override = override_settings(MEDIA_ROOT=self._media_root)
        override.enable()
        self.addCleanup(override.disable)
        self.addCleanup(shutil.rmtree, self._media_root, True)


def make_ambassador(email='db@example.com', photo='ambassador_photos/db.jpg', name='DB Applicant'):
    return Ambassador.objects.create(
        name=name, email=email, whatsapp='+8801700000000',
        date_of_birth='2000-01-01', gender='female', university='NSU',
        department='CSE', year_of_study='2nd', student_id='ID-1',
        photo=photo, bio='b', why_ambassador='w', activities=[],
        heard_from='friend', agree_info_accurate=True, agree_media_usage=True,
        agree_points_ranking=True, agree_contact_consent=True)


# ----------------------------------------------------------------------
# models
# ----------------------------------------------------------------------

class ModelTests(TestCase):
    def test_str_and_mailjob_defaults(self):
        amb = make_ambassador()
        job = MailJob.objects.create(
            campaign='ambassador_received', ambassador=amb, to_email=amb.email)
        self.assertEqual(str(amb), 'DB Applicant <db@example.com>')
        self.assertEqual(
            str(job), 'ambassador_received -> db@example.com (pending)')
        self.assertEqual(job.status, MailJob.PENDING)
        self.assertEqual(job.error, '')
        self.assertIsNone(job.sent_at)
        self.assertEqual(job.gmail_message_id, '')

    def test_unique_email_constraint(self):
        make_ambassador(email='dupe@example.com')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                make_ambassador(email='dupe@example.com')

    def test_one_ambassador_mail_per_campaign_constraint(self):
        amb = make_ambassador()
        MailJob.objects.create(
            campaign='ambassador_received', ambassador=amb, to_email=amb.email)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                MailJob.objects.create(
                    campaign='ambassador_received', ambassador=amb,
                    to_email=amb.email)
        # A different campaign for the same ambassador is allowed.
        MailJob.objects.create(
            campaign='other_campaign', ambassador=amb, to_email=amb.email)

    def test_deleting_ambassador_cascades_to_mailjob(self):
        amb = make_ambassador()
        job = MailJob.objects.create(
            campaign='ambassador_received', ambassador=amb, to_email=amb.email)
        amb.delete()
        self.assertFalse(MailJob.objects.filter(pk=job.pk).exists())


# ----------------------------------------------------------------------
# form validation
# ----------------------------------------------------------------------

class FormTests(TestCase):
    def form(self, **overrides):
        data, files = valid_data(), valid_files()
        for key, value in overrides.items():
            if hasattr(value, 'read'):
                files[key] = value
            elif value is None:
                data.pop(key, None)
                files.pop(key, None)
            else:
                data[key] = value
        return AmbassadorForm(data, files)

    def test_valid_form_and_cleaning(self):
        form = self.form()
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['email'], 'applicant@example.com')
        self.assertIs(form.cleaned_data['is_ieee_member'], False)
        self.assertEqual(form.cleaned_data['activities'], ['social_media_posts'])

    def test_email_is_lowercased_and_duplicate_is_case_insensitive(self):
        make_ambassador(email='taken@example.com')
        form = self.form(email='UPPER@EXAMPLE.com')
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['email'], 'upper@example.com')
        form = self.form(email='TAKEN@EXAMPLE.com')
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_bio_word_limit(self):
        form = self.form(bio='word ' * 50)
        self.assertTrue(form.is_valid(), form.errors)
        form = self.form(bio='word ' * 51)
        self.assertFalse(form.is_valid())
        self.assertIn('bio', form.errors)
        self.assertIn('50', form.errors['bio'][0])

    def test_whatsapp_formats(self):
        for number in ('+8801712345678', '0171234567', '017 123-45(6)'):
            form = self.form(whatsapp=number)
            self.assertTrue(form.is_valid(), form.errors)
        for number in ('abc123', '12', 'not a phone'):
            form = self.form(whatsapp=number)
            self.assertFalse(form.is_valid())
            self.assertIn('whatsapp', form.errors)

    def test_photo_required(self):
        form = self.form(photo=None)
        self.assertFalse(form.is_valid())
        self.assertIn('photo', form.errors)

    def test_photo_accepts_png(self):
        form = self.form(photo=photo_file('photo.png', png_bytes()))
        self.assertTrue(form.is_valid(), form.errors)

    def test_photo_rejects_wrong_extension(self):
        form = self.form(photo=photo_file('photo.gif', jpeg_bytes()))
        self.assertFalse(form.is_valid())
        self.assertIn('photo', form.errors)

    def test_photo_rejects_corrupted_file(self):
        form = self.form(photo=photo_file('fake.jpg', b'this is not an image'))
        self.assertFalse(form.is_valid())
        self.assertIn('photo', form.errors)

    def test_photo_rejects_oversized(self):
        form = self.form(photo=photo_file('big.png', oversized_png_bytes()))
        self.assertFalse(form.is_valid())
        self.assertIn('photo', form.errors)
        self.assertIn('Maximum is 10 MB', form.errors['photo'][0])

    def test_ieee_fields_required_only_for_members(self):
        form = self.form(is_ieee_member='True')
        self.assertFalse(form.is_valid())
        for field in ('ieee_number', 'ieee_grade', 'ieee_branch',
                      'ieee_position'):
            self.assertIn(field, form.errors)
        form = self.form(is_ieee_member='True', ieee_number='IEEE-123',
                         ieee_grade='student_member', ieee_branch='IEEE NSU SB',
                         ieee_position='Member')
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIs(form.cleaned_data['is_ieee_member'], True)
        form = self.form(is_ieee_member='False')
        self.assertTrue(form.is_valid(), form.errors)

    def test_all_four_agreements_required(self):
        for field in ('agree_info_accurate', 'agree_media_usage',
                      'agree_points_ranking', 'agree_contact_consent'):
            form = self.form(**{field: None})
            self.assertFalse(form.is_valid(), f'{field} unchecked must fail')
            self.assertIn(field, form.errors)

    def test_activity_whitelist(self):
        form = self.form(activities=['hacking'])
        self.assertFalse(form.is_valid())
        self.assertIn('activities', form.errors)


# ----------------------------------------------------------------------
# views: GET/POST flows and the mail hook
# ----------------------------------------------------------------------

class ViewTests(MediaRootMixin, TestCase):
    AJAX = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}

    def setUp(self):
        super().setUp()
        cache.clear()
        AmbassadorFormStatus.objects.create(is_published=True)
        self.url = reverse('ambassador_registration:ambassador_apply')
        self.thanks_url = reverse('ambassador_registration:thanks')

    def test_get_renders_form_page(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ambassador_registration/apply.html')
        body = response.content.decode()
        self.assertIn('viewport', body)
        self.assertIn('form.css', body)
        self.assertIn('Photo guide:', body)
        self.assertIn('max 10 MB', body)
        self.assertIn('Full name (as on your ID)', body)
        self.assertIn('unique Ambassador Code', body)

    def test_post_success_ajax_creates_ambassador_and_pending_job(self):
        with self.captureOnCommitCallbacks(execute=False) as callbacks:
            response = self.client.post(
                self.url, full_post_payload(), **self.AJAX)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        self.assertEqual(
            data['message'], 'Application received. Thank you!')

        amb = Ambassador.objects.get(email='applicant@example.com')
        self.assertEqual(amb.name, 'Test Applicant')
        job = MailJob.objects.get(
            campaign='ambassador_received', ambassador=amb)
        self.assertEqual(job.status, MailJob.PENDING)
        self.assertEqual(job.to_email, amb.email)
        self.assertEqual(len(callbacks), 1)
        saved = Path(self._media_root) / 'ambassador_photos'
        self.assertEqual(len(list(saved.iterdir())), 1)

    def test_post_success_non_ajax_redirects_to_thanks(self):
        response = self.client.post(self.url, full_post_payload())
        self.assertRedirects(response, self.thanks_url)
        self.assertEqual(Ambassador.objects.count(), 1)

    def test_post_duplicate_email_ajax(self):
        make_ambassador(email='applicant@example.com')
        response = self.client.post(
            self.url, full_post_payload(), **self.AJAX)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertIn('email', data['errors'])
        self.assertIn('already exists', data['errors']['email'][0])
        self.assertEqual(Ambassador.objects.count(), 1)
        self.assertEqual(MailJob.objects.count(), 0)

    def test_post_duplicate_email_race_is_friendly(self):
        original_save = AmbassadorForm.save

        def racing_save(form_self):
            make_ambassador(email='applicant@example.com')
            return original_save(form_self)

        with mock.patch.object(AmbassadorForm, 'save', racing_save):
            response = self.client.post(self.url, full_post_payload(), **self.AJAX)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('email', data['errors'])
        self.assertIn('already exists', data['errors']['email'][0])
        self.assertEqual(MailJob.objects.count(), 0)

    def test_post_invalid_ajax_returns_field_errors(self):
        response = self.client.post(self.url, {}, **self.AJAX)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        for field in ('name', 'email', 'photo'):
            self.assertIn(field, data['errors'])
        self.assertEqual(Ambassador.objects.count(), 0)

    def test_post_invalid_non_ajax_rerenders_form(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ambassador_registration/apply.html')
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].is_bound)

    def test_thanks_page(self):
        response = self.client.get(self.thanks_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ambassador_registration/thanks.html')

    def test_post_rate_limiting_ajax(self):
        with override_settings(RATE_LIMIT_APPLY_PER_HOUR=2):
            r1 = self.client.post(self.url, {}, **self.AJAX)
            self.assertEqual(r1.status_code, 400)
            r2 = self.client.post(self.url, {}, **self.AJAX)
            self.assertEqual(r2.status_code, 400)
            r3 = self.client.post(self.url, {}, **self.AJAX)
            self.assertEqual(r3.status_code, 429)
            data = json.loads(r3.content)
            self.assertFalse(data['success'])
            self.assertIn('__all__', data['errors'])
            self.assertIn('Too many submissions', data['errors']['__all__'][0])

    def test_post_rate_limiting_non_ajax(self):
        with override_settings(RATE_LIMIT_APPLY_PER_HOUR=1):
            r1 = self.client.post(self.url, {})
            self.assertEqual(r1.status_code, 200)
            r2 = self.client.post(self.url, {})
            self.assertEqual(r2.status_code, 429)
            self.assertContains(r2, 'Too many submissions', status_code=429)


# ----------------------------------------------------------------------
# admin registration
# ----------------------------------------------------------------------

class AdminTests(MediaRootMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_superuser(
            'ops-admin', 'ops-admin@example.com', 'secret-123')
        self.client.force_login(self.user)

    def test_models_registered(self):
        from .admin import AmbassadorAdmin
        from ambassador_email.admin import MailJobAdmin
        self.assertIsInstance(
            django_admin.site._registry[Ambassador], AmbassadorAdmin)
        self.assertIsInstance(
            django_admin.site._registry[MailJob], MailJobAdmin)

    def test_changelists_render(self):
        amb = make_ambassador()
        MailJob.objects.create(
            campaign='ambassador_received', ambassador=amb, to_email=amb.email)
        self.assertEqual(
            self.client.get('/admin/ambassador_registration/ambassador/').status_code, 200)
        self.assertEqual(
            self.client.get('/admin/ambassador_email/mailjob/').status_code, 200)

    def test_ambassador_admin_resend_action_sends_pending_and_failed(self):
        from ambassador_email.tests import FakeService
        import ambassador_registration.admin as amb_admin

        amb1 = make_ambassador(email='pending@example.com', name='Pending User')
        amb2 = make_ambassador(email='failed@example.com', name='Failed User')
        job1 = MailJob.objects.create(campaign='ambassador_received', ambassador=amb1, to_email=amb1.email, status=MailJob.PENDING)
        job2 = MailJob.objects.create(campaign='ambassador_received', ambassador=amb2, to_email=amb2.email, status=MailJob.FAILED, error='error')

        service = FakeService()
        with mock.patch.object(amb_admin, 'build_service', return_value=service):
            res = self.client.post(
                '/admin/ambassador_registration/ambassador/',
                {
                    'action': 'resend_failed_emails',
                    '_selected_action': [str(amb1.id), str(amb2.id)],
                    'index': '0',
                    'select_across': '0'
                },
                follow=True
            )
        self.assertEqual(res.status_code, 200)
        job1.refresh_from_db()
        job2.refresh_from_db()
        self.assertEqual(job1.status, MailJob.SENT)
        self.assertEqual(job2.status, MailJob.SENT)
        self.assertEqual(len(service.bodies), 2)

    def test_ambassador_admin_force_resend_action(self):
        from ambassador_email.tests import FakeService
        import ambassador_registration.admin as amb_admin

        amb = make_ambassador(email='sent@example.com', name='Sent User')
        job = MailJob.objects.create(campaign='ambassador_received', ambassador=amb, to_email=amb.email, status=MailJob.SENT, gmail_message_id='msg-001')

        service = FakeService()
        with mock.patch.object(amb_admin, 'build_service', return_value=service):
            res = self.client.post(
                '/admin/ambassador_registration/ambassador/',
                {
                    'action': 'force_resend_emails',
                    '_selected_action': [str(amb.id)],
                    'index': '0',
                    'select_across': '0'
                },
                follow=True
            )
        self.assertEqual(res.status_code, 200)
        job.refresh_from_db()
        self.assertEqual(job.status, MailJob.SENT)
        self.assertEqual(len(service.bodies), 1)

    def test_ambassador_admin_single_resend_endpoint(self):
        from ambassador_email.tests import FakeService
        import ambassador_registration.admin as amb_admin

        amb = make_ambassador(email='single@example.com', name='Single User')
        job = MailJob.objects.create(campaign='ambassador_received', ambassador=amb, to_email=amb.email, status=MailJob.FAILED, error='boom')

        service = FakeService()
        with mock.patch.object(amb_admin, 'build_service', return_value=service):
            res = self.client.get(
                f'/admin/ambassador_registration/ambassador/{amb.id}/resend-email/',
                follow=True
            )
        self.assertEqual(res.status_code, 200)
        job.refresh_from_db()
        self.assertEqual(job.status, MailJob.SENT)
        self.assertEqual(len(service.bodies), 1)

    def test_ambassador_admin_change_form_renders_inline(self):
        amb = make_ambassador(name='Inline User')
        MailJob.objects.create(
            campaign='ambassador_received', ambassador=amb, to_email=amb.email,
            status=MailJob.FAILED, error='Temporary failure'
        )
        res = self.client.get(f'/admin/ambassador_registration/ambassador/{amb.id}/change/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Temporary failure')
        self.assertContains(res, 'FAILED')

    def test_ambassador_admin_email_status_filter(self):
        amb_failed = make_ambassador(email='fail@example.com')
        MailJob.objects.create(campaign='ambassador_received', ambassador=amb_failed, to_email=amb_failed.email, status=MailJob.FAILED)
        amb_sent = make_ambassador(email='ok@example.com')
        MailJob.objects.create(campaign='ambassador_received', ambassador=amb_sent, to_email=amb_sent.email, status=MailJob.SENT)

        res_failed = self.client.get('/admin/ambassador_registration/ambassador/?email_status=failed')
        self.assertEqual(res_failed.status_code, 200)
        self.assertContains(res_failed, amb_failed.email)
        self.assertNotContains(res_failed, amb_sent.email)

        res_sent = self.client.get('/admin/ambassador_registration/ambassador/?email_status=sent')
        self.assertEqual(res_sent.status_code, 200)
        self.assertContains(res_sent, amb_sent.email)
        self.assertNotContains(res_sent, amb_failed.email)


class AmbassadorManagementTests(MediaRootMixin, TestCase):
    """Tests for publish controls, admin preview, response table, detail view,
    bulk selection, and 3-sheet Excel export."""

    def setUp(self):
        super().setUp()
        cache.clear()
        self.admin_user = User.objects.create_superuser(
            'amb-admin', 'amb-admin@example.com', 'secret-123'
        )
        self.apply_url = reverse('ambassador_registration:ambassador_apply')
        self.admin_url = reverse('ambassador_registration:admin_ambassador')
        self.toggle_url = reverse('ambassador_registration:toggle_publish')
        self.table_url = reverse('ambassador_registration:response_table')
        self.save_url = reverse('ambassador_registration:save_selected')
        self.excel_url = reverse('ambassador_registration:download_excel')

    def test_unpublished_form_renders_closed_state_and_blocks_post(self):
        AmbassadorFormStatus.objects.create(is_published=False)
        res = self.client.get(self.apply_url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Registration is currently closed.')

        post_res = self.client.post(
            self.apply_url, full_post_payload(), HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(post_res.status_code, 403)
        self.assertEqual(Ambassador.objects.count(), 0)

    def test_staff_redirected_to_admin_and_can_preview_live_form(self):
        AmbassadorFormStatus.objects.create(is_published=True)
        self.client.force_login(self.admin_user)

        res = self.client.get(self.apply_url)
        self.assertRedirects(res, self.admin_url)

        preview_res = self.client.get(f'{self.apply_url}?preview=1')
        self.assertEqual(preview_res.status_code, 200)
        self.assertFalse(preview_res.context['is_staff_view'])

    def test_admin_view_and_toggle_publish(self):
        make_ambassador(email='a1@example.com', name='Alice')
        self.client.force_login(self.admin_user)

        res = self.client.get(self.admin_url)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.context['is_staff_view'])
        self.assertEqual(res.context['registration_count'], 1)
        self.assertContains(res, 'Preview Live Form')
        self.assertContains(res, 'See Responses')
        self.assertContains(res, 'Publish Form?')

        t1 = self.client.post(self.toggle_url)
        self.assertEqual(t1.status_code, 200)
        self.assertTrue(json.loads(t1.content)['is_published'])

        t2 = self.client.post(self.toggle_url)
        self.assertEqual(t2.status_code, 200)
        self.assertFalse(json.loads(t2.content)['is_published'])

    def test_response_table_and_detail_view(self):
        amb = make_ambassador(email='detail@example.com', name='Zara Khan')
        amb.activities = ['social_media_posts', 'organizing_sessions']
        amb.save()
        self.client.force_login(self.admin_user)

        table_res = self.client.get(self.table_url)
        self.assertEqual(table_res.status_code, 200)
        self.assertTemplateUsed(
            table_res, 'ambassador_registration/ambassador_response_table.html'
        )
        self.assertContains(table_res, 'Zara Khan')
        self.assertContains(table_res, 'Ambassadors (1)')
        self.assertContains(table_res, 'Coming Soon')

        detail_url = reverse('ambassador_registration:view_response', args=[amb.id])
        detail_res = self.client.get(detail_url)
        self.assertEqual(detail_res.status_code, 200)
        self.assertTemplateUsed(
            detail_res, 'ambassador_registration/ambassador_response_detail.html'
        )
        self.assertContains(detail_res, 'Zara Khan')
        self.assertContains(detail_res, 'Social media posts and stories')
        self.assertContains(detail_res, 'Organizing campus sessions')

    def test_save_selected_bulk_updates_status(self):
        a1 = make_ambassador(email='sel1@example.com', name='One')
        a2 = make_ambassador(email='sel2@example.com', name='Two')
        self.client.force_login(self.admin_user)

        res = self.client.post(
            self.save_url,
            data=json.dumps({'selected_ids': [a1.id]}),
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(json.loads(res.content)['status'], 'success')

        a1.refresh_from_db()
        a2.refresh_from_db()
        self.assertTrue(a1.is_selected)
        self.assertFalse(a2.is_selected)

    def test_download_excel_has_three_required_sheets(self):
        import openpyxl

        a1 = make_ambassador(email='ieee@example.com', name='IEEE Amb')
        a1.is_ieee_member = True
        a1.ieee_number = '98765432'
        a1.ieee_grade = 'student_member'
        a1.ieee_branch = 'IEEE NSU SB'
        a1.save()
        make_ambassador(email='nonieee@example.com', name='Regular Amb')

        self.client.force_login(self.admin_user)
        res = self.client.get(self.excel_url)
        self.assertEqual(res.status_code, 200)
        self.assertIn('ambassador_data.xlsx', res['Content-Disposition'])

        wb = openpyxl.load_workbook(BytesIO(res.content))
        self.assertEqual(
            wb.sheetnames, ['Ambassador Name', 'University Name', 'IEEE Members']
        )
        self.assertEqual(wb['Ambassador Name'].max_row, 3)  # header + 2 rows
        self.assertEqual(wb['University Name'].max_row, 3)  # header + 2 rows
        self.assertEqual(wb['IEEE Members'].max_row, 2)  # header + 1 IEEE row
