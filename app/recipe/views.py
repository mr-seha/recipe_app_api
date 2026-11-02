from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import DestroyModelMixin, ListModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from core.models import Ingredient, Recipe, Tag

from .serializers import (
    IngredientSerializer,
    RecipeDetailSerializer,
    RecipeSerializer,
    TagSerializer, RecipeImageSerializer,
)


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticated]

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def get_queryset(self):
        return self.queryset.order_by('-id').filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return RecipeSerializer
        elif self.action == 'upload_image':
            return RecipeImageSerializer
        return RecipeDetailSerializer

    def get_serializer_context(self):
        return {'request': self.request}

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TagViewSet(ListModelMixin,
                 UpdateModelMixin,
                 DestroyModelMixin,
                 GenericViewSet):
    queryset = Tag.objects.order_by('-name')
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


class IngredientList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Ingredient.objects.filter(user=request.user).order_by('-name')
        serializer = IngredientSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class IngredientDetail(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, id):
        ingredient = get_object_or_404(Ingredient, id=id, user=request.user)
        serializer = IngredientSerializer(ingredient, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, id):
        ingredient = get_object_or_404(Ingredient, id=id, user=request.user)
        ingredient.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
