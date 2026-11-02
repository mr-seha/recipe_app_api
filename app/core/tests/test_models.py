from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import Ingredient, Recipe, Tag, recipe_image_file_path


def create_user(email='user@exaample.com', password='test-pass1234'):
    return get_user_model().objects.create_user(email, password)


class TestModels(TestCase):
    def test_create_user_with_email_successful(self):
        email = 'test@example.com'
        password = 'test_pass12345'
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(email, user.email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        sample_emails = [
            ['TEST1@example.com', 'TEST1@example.com'],
            ['test2@EXAMPLE.com', 'test2@example.com'],
            ['Test3@EXAMPLE.com', 'Test3@example.com'],
            ['test4@example.com', 'test4@example.com']
        ]

        for email, expected_email in sample_emails:
            user = get_user_model().objects.create_user(email, 'sample123')
            self.assertEqual(
                expected_email,
                user.email
            )

    def test_create_user_without_email_raises_error(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', '12345sample')

    def test_create_superuser_successful(self):
        user = get_user_model().objects.create_superuser('test2@example.com')
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        user = create_user()

        recipe = Recipe.objects.create(
            user=user,
            title='new recipe',
            time_minutes=5,
            price=Decimal('15.75'),
            description='New recipe description for test',
        )

        self.assertTrue(Recipe.objects.filter(id=recipe.pk).exists())

    def test_create_tag(self):
        user = create_user()
        tag = Tag.objects.create(user=user, name='test')

        self.assertEqual(tag.name, str(tag))

    def test_create_ingredient(self):
        data = {
            'name': 'test',
            'user': create_user()
        }

        ingredient = Ingredient.objects.create(**data)
        self.assertTrue(Ingredient.objects.filter(name=data['name'], user=data['user']).exists())
        self.assertEqual(ingredient.name, str(ingredient))

    @patch('core.models.uuid4')
    def test_recipe_file_name_uuid(self, patched_uuid):
        uuid = 'test-uuid'
        patched_uuid.return_value = uuid
        file_path = recipe_image_file_path(None, 'example.name.jpg')

        self.assertEqual(file_path, f'uploads/recipe/{uuid}.jpg')
