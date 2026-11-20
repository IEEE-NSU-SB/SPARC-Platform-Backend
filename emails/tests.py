from urllib.parse import parse_qs, urlsplit
from unittest import mock
from django.test import TestCase, override_settings
from django.urls import resolve, reverse
from django.contrib.auth import get_user_model
from google.oauth2.credentials import Credentials

from emails.views import _redirect_uri, get_credentials, save_credentials

User = get_user_model()


class OAuthURLResolutionTests(TestCase):
    def test_urls_resolve(self):
        r_auth = resolve('/init/authorise/')
        self.assertEqual(r_auth.func.__name__, 'authorize')

        r_cb_bare = resolve('/init/oauth2callback')
        self.assertEqual(r_cb_bare.func.__name__, 'oauth2callback')

        r_cb_slash = resolve('/init/oauth2callback/')
        self.assertEqual(r_cb_slash.func.__name__, 'oauth2callback')


class OAuthFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin_test',
            email='admin@example.com',
            password='testpassword123',
        )

    def test_canonical_host_redirects_from_127_to_localhost(self):
        self.client.force_login(self.user)
        response = self.client.get('/init/authorise/', HTTP_HOST='127.0.0.1:8000')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'http://localhost:8000/init/authorise/')

    @override_settings(SITE_URL='http://localhost:8000')
    def test_authorise_redirects_to_google_with_correct_parameters(self):
        self.client.force_login(self.user)
        response = self.client.get('/init/authorise/', HTTP_HOST='localhost:8000')
        self.assertEqual(response.status_code, 302)
        target = response['Location']
        self.assertTrue(target.startswith('https://accounts.google.com/o/oauth2/auth'))

        parsed = urlsplit(target)
        qs = parse_qs(parsed.query)
        self.assertEqual(qs['redirect_uri'], ['http://localhost:8000/init/oauth2callback'])
        self.assertEqual(qs['access_type'], ['offline'])
        self.assertEqual(qs['prompt'], ['consent'])
        self.assertIn('state', self.client.session)
        self.assertEqual(self.client.session['state'], qs['state'][0])

    def test_callback_without_state_is_rejected(self):
        self.client.force_login(self.user)
        response = self.client.get('/init/oauth2callback')
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Invalid state parameter', response.content)

    def test_callback_with_mismatched_state_is_rejected(self):
        self.client.force_login(self.user)
        session = self.client.session
        session['state'] = 'correct-state'
        session.save()
        response = self.client.get('/init/oauth2callback', {'state': 'wrong-state'})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Invalid state parameter', response.content)

    def test_callback_google_error_is_reported(self):
        self.client.force_login(self.user)
        session = self.client.session
        session['state'] = 'valid-state'
        session.save()
        response = self.client.get('/init/oauth2callback', {'state': 'valid-state', 'error': 'access_denied'})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'access_denied', response.content)

