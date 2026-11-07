from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


def ingredient_url(id):
    return reverse('recipe:ingredient-detail', args=[id])


def create_ingredient(user, name='test'):
    return Ingredient.objects.create(user=user, name=name)


def create_user(email='user@example.com'):
    return get_user_model().objects.create_user(
        email=email,
        password='test_pass1234'
    )


class PublicIngredientsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_authentication_required(self):
        response = self.client.get(INGREDIENTS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsAPITests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_ingredients(self):
        create_ingredient(self.user)
        create_ingredient(self.user, 'other ingredient')

        response = self.client.get(INGREDIENTS_URL)

        queryset = Ingredient.objects.order_by('-name')
        serializer = IngredientSerializer(queryset, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        user2 = create_user('user2@example.com')
        create_ingredient(user2, 'test2')

        ingredient = create_ingredient(self.user, 'test1')

        response = self.client.get(INGREDIENTS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], ingredient.name)
        self.assertEqual(response.data[0]['id'], ingredient.id)

    def test_update_ingredient(self):
        ingredient = create_ingredient(self.user)

        url = ingredient_url(ingredient.id)
        payload = {'name': 'new name'}
        response = self.client.patch(url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ingredient.refresh_from_db()

        self.assertEqual(payload['name'], ingredient.name)

    def test_delete_ingredient(self):
        ingredient = create_ingredient(self.user)
        url = ingredient_url(ingredient.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ingredient.objects.filter(id=ingredient.id).exists())

    def test_filter_ingredients_assigned_to_recipe(self):
        ing1 = create_ingredient(self.user)
        ing2 = create_ingredient(self.user)

        data = {
            'title': 'new recipe',
            'time_minutes': 5,
            'price': Decimal('15.75'),
        }

        recipe1 = Recipe.objects.create(user=self.user, **data)
        recipe2 = Recipe.objects.create(user=self.user, **data)

        recipe1.ingredients.add(ing1)
        recipe2.ingredients.add(ing2)

        params = {'assigned_only': 1}
        response = self.client.get(INGREDIENTS_URL, params)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(IngredientSerializer(ing1).data, response.data)
        self.assertIn(IngredientSerializer(ing2).data, response.data)

    def test_filtered_ingredients_unique(self):
        ingredient = create_ingredient(self.user, name='ingredient')
        create_ingredient(self.user, name='ing2')

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

        recipe1.ingredients.add(ingredient)
        recipe2.ingredients.add(ingredient)

        params = {'assigned_only': f'{recipe1.id}'}
        response = self.client.get(INGREDIENTS_URL, params)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn(IngredientSerializer(ingredient).data, response.data)
