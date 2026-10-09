from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from core.models import Recipe

from .serializers import RecipeDetailSerializer, RecipeSerializer


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

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
