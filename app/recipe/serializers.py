from django.db import transaction
from rest_framework import serializers

from core.models import Ingredient, Recipe, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name']
        read_only_fields = ['id']


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link', 'tags', 'ingredients']
        read_only_fields = ['id']


class RecipeDetailSerializer(RecipeSerializer):
    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']

    def _get_or_create_tag(self, tags, recipe):
        for tag_data in tags:
            created_tag, created = Tag.objects.get_or_create(user=self.context['request'].user, **tag_data)
            recipe.tags.add(created_tag)

    @transaction.atomic()
    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        recipe = Recipe.objects.create(**validated_data)

        for ingredient in ingredients:
            ingredient, created = Ingredient.objects.get_or_create(user=self.context['request'].user, **ingredient)
            recipe.ingredients.add(ingredient)

        self._get_or_create_tag(tags, recipe)

        return recipe

    @transaction.atomic()
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()

        if ingredients is not None:
            instance.ingredients.clear()
            for item in ingredients:
                ingredient, created = Ingredient.objects.get_or_create(
                    user=self.context['request'].user,
                    name=item['name']
                )
                instance.ingredients.add(ingredient)

        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tag(tags, instance)

        return instance


class RecipeImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image': {'required': 'True'}}
