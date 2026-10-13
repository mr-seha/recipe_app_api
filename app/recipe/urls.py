from rest_framework.routers import DefaultRouter

from .views import RecipeViewSet, TagViewSet

app_name = 'recipe'

router = DefaultRouter()
router.register('recipe', RecipeViewSet, basename='recipe')
router.register('tags', TagViewSet, basename='tag')

urlpatterns = router.urls
