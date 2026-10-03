from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        payload = {
            'email': 'email@example.com',
            'password': 'test-pass12345',
            'name': 'reza'

        }
        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', response.data)

    def test_create_user_with_repetitive_email_return_error(self):
        payload = {
            'email': 'email@example.com',
            'password': 'test-pass1231',
            'name': 'reza'
        }
        create_user(**payload)

        response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_password_too_short_error(self):
        payload = {
            'email': 'email@example.com',
            'password': 'test',
            'name': 'reza'
        }

        response = self.client.post(CREATE_USER_URL, payload)
        user_exists = get_user_model().objects.filter(email=payload['email']).exists()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        user_details = {
            'email': 'email@example.com',
            'password': 'test-pass12345',
            'name': 'reza',
        }

        create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': user_details['password']
        }

        response = self.client.post(TOKEN_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_create_token_with_bad_credential(self):
        user_details = {
            'email': 'email@example.com',
            'password': 'test-pass12345',
            'name': 'reza',
        }

        create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': 'wrong_password'
        }

        response = self.client.post(TOKEN_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', response.data)

    def test_create_token_blank_password(self):
        payload = {
            'email': 'email@example.com',
            'password': ''
        }

        response = self.client.post(TOKEN_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', response.data)

    def test_retrieve_user_unauthorized(self):
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserAPITests(TestCase):
    def setUp(self):
        user_info = {
            'email': 'example@email.com',
            'password': 'test-pass1234',
            'name': 'ali'
        }
        self.user = create_user(**user_info)

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_successfully(self):
        response = self.client.get(ME_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                'email': self.user.email,
                'name': self.user.name
            }
        )

    def test_post_me_not_allowed(self):
        response = self.client.post(ME_URL, {})

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile_successfully(self):
        payload = {
            'name': 'new name',
            'password': 'new_test_pass12345'
        }

        response = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
