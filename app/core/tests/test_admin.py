from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework import status
from django.utils.translation import gettext as _


class AdminSiteTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.admin_user = get_user_model().objects.create_superuser(
            email='admin@example.com',
            password='sample_pass123'
        )

        self.client.force_login(user=self.admin_user)

        self.user = get_user_model().objects.create_user(
            email='user@example.com',
            password='sample_pass123',
            name='test'
        )

    def test_users_list(self):
        url = reverse('admin:core_user_changelist')
        response = self.client.get(url)

        self.assertContains(response, self.user.email)
        self.assertContains(response, self.user.name)

    def test_edit_user_page(self):
        url = reverse('admin:core_user_change', args=[self.user.id])
        response = self.client.get(url)

        self.assertContains(response, self.user.email)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_add_user_page(self):
        url = reverse('admin:core_user_add')

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, _('email'))
        self.assertContains(response, _('password'))

