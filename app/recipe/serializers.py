from django.db import transaction
from rest_framework import serializers

from core.models import Recipe, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link', 'tags']
        read_only_fields = ['id']


class RecipeDetailSerializer(RecipeSerializer):
    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']

    def _get_or_create_tag(self, tags, recipe):
        for tag_data in tags:
            created_tag, created = Tag.objects.get_or_create(user=self.context['user'], **tag_data)
            recipe.tags.add(created_tag)

    @transaction.atomic()
    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        recipe = Recipe.objects.create(**validated_data)

        self._get_or_create_tag(tags, recipe)

        return recipe

    @transaction.atomic()
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()

        if tags is not None:
            instance.tags.clear()

            self._get_or_create_tag(tags, instance)

        return instance
