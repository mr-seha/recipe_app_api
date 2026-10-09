from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe
from recipe.serializers import RecipeDetailSerializer, RecipeSerializer

RECIPE_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    defaults = {
        'title': 'new recipe',
        'time_minutes': 5,
        'price': Decimal('15.75'),
        'description': 'New recipe description for test',
        'link': 'example.com/recipe'
    }

    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(RECIPE_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email='example@email.com',
            password='test-pass1234',
            name='ali'
        )

        self.client.force_authenticate(user=self.user)

    def test_retrieve_recipes(self):
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        response = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        other_user = create_user(
            email='other@email.com',
            password='test-pass1234',
            name='reza'
        )
        create_recipe(user=other_user)

        create_recipe(user=self.user)
        create_recipe(user=self.user)

        response = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.filter(user=self.user).order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_retrieve_specific_recipe(self):
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)

        response = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_recipe_successfully(self):
        payload = {
            'title': 'new recipe',
            'time_minutes': 5,
            'price': Decimal('15.75'),
        }
        response = self.client.post(RECIPE_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.first()
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

        self.assertEqual(recipe.user, self.user)

    def test_recipe_partial_update(self):
        original_link = 'example.com/recipe'
        recipe = create_recipe(
            user=self.user,
            title='new recipe',
            link=original_link
        )

        payloads = {
            'title': 'edited title',
            'description': 'edited description'
        }
        url = detail_url(recipe.id)
        response = self.client.patch(url, payloads)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payloads['title'])
        self.assertEqual(recipe.description, payloads['description'])
        self.assertEqual(recipe.link, original_link)

    def test_recipe_full_update(self):
        recipe = create_recipe(user=self.user)

        payload = {
            'title': 'Edited title',
            'time_minutes': 8,
            'price': Decimal('20.75'),
            'description': 'Edited recipe description for test',
            'link': 'example.com/new-recipe'
        }

        url = detail_url(recipe.id)
        response = self.client.put(url, payload)
        recipe.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.user, self.user)
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

    def test_update_recipe_user_forbidden(self):
        recipe = create_recipe(user=self.user)

        other_user = create_user(
            email='new_other@example.com',
            password='test-pass1234'
        )

        url = detail_url(recipe.id)
        self.client.patch(url, {'user': other_user})

        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe_successfully(self):
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_users_recipe_forbidden(self):
        other_user = create_user(
            email='new_other@example.com',
            password='test-pass1234'
        )
        recipe = create_recipe(user=other_user)

        url = detail_url(recipe.id)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())


