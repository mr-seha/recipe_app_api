from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
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
    RecipeImageSerializer,
    RecipeSerializer,
    TagSerializer,
)


@extend_schema(
    # extra parameters added to the schema
    parameters=[
        OpenApiParameter(name='tags', description='Filter by tags', required=False, type=str),
        OpenApiParameter(
            name='ingredients',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter by ingredients',
        ),
    ]
)
class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['ingredients']

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def get_queryset(self):
        tags = self.request.query_params.get('tags')

        if tags:
            tag_ids = [int(id) for id in tags.split(',')]
            self.queryset = self.queryset.filter(tags__id__in=tag_ids)
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
        assigned_only = bool(int(self.request.query_params.get('assigned_only', 0)))
        if assigned_only:
            self.queryset = self.queryset.filter(recipe__isnull=False)
        return self.queryset.filter(user=self.request.user).distinct()


class IngredientList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        assigned_only = bool(int(request.query_params.get('assigned_only', 0)))

        queryset = Ingredient.objects.filter(user=request.user).order_by('-name')

        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)
        serializer = IngredientSerializer(queryset.distinct(), many=True)
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
