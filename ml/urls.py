from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import ExperimentTestJWTView

router = DefaultRouter()
router.register(r'experiments', views.ExperimentViewSet, basename='experiments')
router.register(r'models', views.MLModelVersionViewSet, basename='models')

urlpatterns = [
    # Сначала кастомные страницы
    path('', views.ai_analysis_page, name='ai_analysis'),  # ← Теперь этот ПЕРВЫЙ
    path('test-jwt/', ExperimentTestJWTView.as_view(), name='experiment_test_jwt'),
    path('analyze/', views.analyze_experiment, name='analyze_experiment'),

    # API routes должны идти ПОСЛЕ кастомных страниц
    path('', include(router.urls)),
]