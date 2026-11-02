from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe, Tag
from recipe.serializers import RecipeDetailSerializer, RecipeSerializer
import tempfile
import os
from PIL import Image

RECIPE_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=[recipe_id])


def image_upload_url(recipe_id):
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


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

    def test_create_recipe(self):
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

    def test_create_recipe_with_tags(self):
        payload = {
            'title': 'new recipe',
            'time_minutes': 5,
            'price': Decimal('15.75'),
            'tags':
                [
                    {'name': 'tag1'},
                    {'name': 'tag2'}
                ]
        }

        response = self.client.post(RECIPE_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        for tag in payload['tags']:
            self.assertIn(tag, recipe.tags.values('name'))

    def test_create_recipe_with_existing_tags(self):
        tag = Tag.objects.create(user=self.user, name='tag1')
        payload = {
            'title': 'new recipe',
            'time_minutes': 5,
            'price': Decimal('15.75'),
            'tags':
                [
                    {'name': 'tag1'},
                    {'name': 'tag2'},
                ]
        }

        response = self.client.post(RECIPE_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertIn(tag, recipe.tags.all())

    def test_create_tags_on_update(self):
        recipe = create_recipe(user=self.user)

        new_tag_name = 'new tag'
        payload = {'tags': [{'name': new_tag_name}]}

        url = detail_url(recipe.id)
        response = self.client.patch(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        tag = Tag.objects.get(user=self.user, name=new_tag_name)
        self.assertIn(tag, recipe.tags.all())

    def test_update_recipe_assign_tags(self):
        recipe = create_recipe(user=self.user)
        tag1 = Tag.objects.create(user=self.user, name='tag1')
        tag2 = Tag.objects.create(user=self.user, name='tag2')

        payload = {'tags': [{'name': 'tag1'}]}

        url = detail_url(recipe.id)
        response = self.client.patch(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 1)
        self.assertIn(tag1, recipe.tags.all())
        self.assertNotIn(tag2, recipe.tags.all())

    def test_clear_recipe_tags(self):
        recipe = create_recipe(user=self.user)
        tag = Tag.objects.create(user=self.user, name='tag')

        recipe.tags.add(tag)

        url = detail_url(recipe.id)
        response = self.client.patch(url, {'tags': []}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)
        self.assertNotIn(tag, recipe.tags.all())

    def test_create_recipe_with_new_ingredients(self):
        payload = {
            'title': 'new recipe',
            'time_minutes': 5,
            'price': Decimal('15.75'),
            'ingredients': [
                {'name': 'ing1'},
                {'name': 'ing2'}
            ]
        }

        response = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.first()

        for ingredient in payload['ingredients']:
            self.assertIn(ingredient, recipe.ingredients.values('name'))

    def test_create_recipe_with_existing_ingredient(self):
        ingredient = Ingredient.objects.create(user=self.user, name='ing1')

        payload = {
            'title': 'new recipe',
            'time_minutes': 5,
            'price': Decimal('15.75'),
            'ingredients': [
                {'name': 'ing1'},
                {'name': 'ing2'}
            ]
        }

        response = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Ingredient.objects.filter(user=self.user).count(), 2)

        queryset = Recipe.objects.filter(user=self.user)
        self.assertEqual(queryset.count(), 1)
        self.assertIn(ingredient, queryset[0].ingredients.all())

    def test_create_ingredients_on_recipe_update(self):
        recipe = create_recipe(user=self.user)

        payload = {'ingredients': [{'name': 'new ing2'}, {'name': 'new ing3'}]}

        url = detail_url(recipe.id)
        response = self.client.patch(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            self.assertIn(ingredient, recipe.ingredients.values('name'))

    def test_assign_ingredients_on_update_recipe(self):
        recipe = create_recipe(user=self.user)
        ingredient1 = Ingredient.objects.create(user=self.user, name='ing1')
        recipe.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(user=self.user, name='ing2')
        payload = {'ingredients': [{'name': 'ing2'}]}

        url = detail_url(recipe.id)
        response = self.client.patch(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(Ingredient.objects.filter(user=self.user).count(), 2)
        self.assertEqual(recipe.ingredients.count(), 1)

        self.assertNotIn(ingredient1, recipe.ingredients.all())
        self.assertIn(ingredient2, recipe.ingredients.all())

    def test_clear_ingredients_on_recipe_update(self):
        ingredient = Ingredient.objects.create(user=self.user, name='ing1')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)

        url = detail_url(recipe.id)
        payload = {'ingredients': []}
        response = self.client.patch(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)


class ImageUploadTest(TestCase):
    def setUp(self):
        self.user = create_user(
            email='example@email.com',
            password='test-pass1234',
            name='ali'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)

            payload = {'image': image_file}

            response = self.client.post(url, payload, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('image', response.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        url = image_upload_url(self.recipe.id)
        payload = {'image': 'nonimage'}
        response = self.client.post(url, payload, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
