from rest_framework.mixins import DestroyModelMixin, ListModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from core.models import Recipe, Tag

from .serializers import RecipeDetailSerializer, RecipeSerializer, TagSerializer


class RecipeViewSet(ModelViewSet):
    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.order_by('-id').filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return RecipeSerializer
        return RecipeDetailSerializer

    def get_serializer_context(self):
        return {'user': self.request.user}

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
