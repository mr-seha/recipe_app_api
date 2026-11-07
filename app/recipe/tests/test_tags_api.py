from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag
from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


def detail_url(id):
    return reverse('recipe:tag-detail', args=[id])


def create_user(**params):
    defaults = {
        'email': 'user@example.com',
        'password': 'test-pass1234'
    }

    defaults.update(params)

    return get_user_model().objects.create_user(**defaults)


def create_tag(user, name='default'):
    return Tag.objects.create(user=user, name=name)


class PublicTagsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(TAGS_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsAPITests(TestCase):
    def setUp(self):
        self.user = create_user()

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_tags(self):
        create_tag(user=self.user)
        create_tag(user=self.user)

        response = self.client.get(TAGS_URL)

        queryset = Tag.objects.order_by('-name')
        serializer = TagSerializer(queryset, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_tags_limited_to_user(self):
        other_user = create_user(email='other@example.com')
        create_tag(user=other_user)
        create_tag(user=self.user)
        create_tag(user=self.user)

        queryset = Tag.objects.filter(user=self.user).order_by('-name')
        serializer = TagSerializer(queryset, many=True)

        response = self.client.get(TAGS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_update_tag(self):
        tag = create_tag(user=self.user)

        url = detail_url(tag.id)

        response = self.client.patch(url, payload := {'name': 'new name'})

        tag.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        tag = create_tag(self.user)

        url = detail_url(tag.id)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(id=tag.id).exists())

    def test_filter_tags_assigned_to_recipes(self):
        tag1 = create_tag(self.user)
        tag2 = create_tag(self.user)

        data1 = {
            'title': 'new recipe',
            'time_minutes': 5,
            'price': Decimal('15.75'),
        }

        data2 = {
            'title': 'other recipe',
            'time_minutes': 8,
            'price': Decimal('20.75'),
        }

        recipe1 = Recipe.objects.create(user=self.user, **data1)
        recipe2 = Recipe.objects.create(user=self.user, **data2)

        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)

        params = {'assigned_only': 1}

        response = self.client.get(TAGS_URL, params)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(TagSerializer(tag1).data, response.data)
        self.assertIn(TagSerializer(tag2).data, response.data)

    def test_filter_tags_assigned_to_recipes_unique(self):
        tag = create_tag(self.user)
        create_tag(self.user, 'tag2')

        data1 = {
            'title': 'new recipe',
            'time_minutes': 5,
            'price': Decimal('15.75'),
        }

        data2 = {
            'title': 'other recipe',
            'time_minutes': 8,
            'price': Decimal('20.75'),
        }

        recipe1 = Recipe.objects.create(user=self.user, **data1)
        recipe2 = Recipe.objects.create(user=self.user, **data2)

        recipe1.tags.add(tag)
        recipe2.tags.add(tag)

        params = {'assigned_only': 1}

        response = self.client.get(TAGS_URL, params)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn(TagSerializer(tag).data, response.data)