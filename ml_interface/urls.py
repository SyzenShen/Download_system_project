from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MLTaskViewSet

router = DefaultRouter()
router.register(r'ml', MLTaskViewSet, basename='ml')

urlpatterns = [
  path('', include(router.urls)),
]
