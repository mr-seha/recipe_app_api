from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import IngredientDetail, IngredientList, RecipeViewSet, TagViewSet

app_name = 'recipe'

router = DefaultRouter()
router.register('recipe', RecipeViewSet, basename='recipe')
router.register('tags', TagViewSet, basename='tag')

urlpatterns = router.urls + [
    path('ingredients/', IngredientList.as_view(), name='ingredient-list'),
    path('ingredients/<int:id>/', IngredientDetail.as_view(), name='ingredient-detail')
]
