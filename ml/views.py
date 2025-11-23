from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import render
from django.views import View
import json

from .models import Experiment, MLModelVersion
from .serializers import (
    ExperimentSerializer,
    MLModelVersionSerializer,
    ExperimentCreateSerializer
)
from .services.deepseek_service import deepseek_service


class ExperimentViewSet(viewsets.ModelViewSet):
    serializer_class = ExperimentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Experiment.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = ExperimentCreateSerializer(data=request.data)
        if serializer.is_valid():
            experiment = Experiment.objects.create(
                user=request.user,
                title=serializer.validated_data['title'],
                description=serializer.validated_data['description'],
                input_data={
                    **serializer.validated_data['experimental_data'],
                    'hypothesis': serializer.validated_data.get('hypothesis', '')
                },
                status='pending'
            )

            # Синхронная обработка
            try:
                self._process_experiment(experiment)
            except Exception as e:
                experiment.status = 'failed'
                experiment.save()
                return Response(
                    {'error': f'Ошибка обработки: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response(
                ExperimentSerializer(experiment).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _process_experiment(self, experiment):
        """Синхронная обработка эксперимента"""
        experiment.status = 'processing'
        experiment.save()

        processed_data = deepseek_service.preprocess_experiment_data({
            'title': experiment.title,
            'description': experiment.description,
            **experiment.input_data
        })

        result = deepseek_service.validate_experiment_design(processed_data)

        experiment.output_data = result
        experiment.feasibility_score = result.get('feasibility_score', 0)
        experiment.plausibility_score = result.get('plausibility_score', 0)
        experiment.improvements = result.get('improvements', [])
        experiment.status = 'completed'
        experiment.save()



"""    @action(detail=False, methods=['post'], permission_classes=[AllowAny])  # Временно разрешаем без аутентификации
    def quick_validate(self, request):
        
        #Быстрая валидация эксперимента без сохранения в БД
        
        serializer = ExperimentCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Используем кэш для одинаковых запросов
                cache_key = f"quick_validate_{hash(str(serializer.validated_data))}"
                cached_result = cache.get(cache_key)

                if cached_result:
                    return Response(cached_result)

                processed_data = deepseek_service.preprocess_experiment_data({
                    'title': serializer.validated_data['title'],
                    'description': serializer.validated_data['description'],
                    'hypothesis': serializer.validated_data.get('hypothesis', ''),
                    **serializer.validated_data['experimental_data']
                })

                result = deepseek_service.validate_experiment_design(processed_data)

                cache.set(cache_key, result, timeout=3600)

                return Response(result)

            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)"""


@action(detail=False, methods=['get', 'post'], permission_classes=[AllowAny])
def quick_validate(self, request):
    """
    Быстрая валидация эксперимента - поддерживает GET и POST
    """
    if request.method == 'GET':
        # Показываем пример данных и форму для тестирования
        example_data = {
            "message": "Используйте эту форму для тестирования API анализа экспериментов",
            "example_request": {
                "title": "Исследование влияния температуры на скорость химической реакции",
                "description": "Эксперимент по изучению зависимости скорости реакции от температуры с использованием метода колориметрии",
                "hypothesis": "Повышение температуры увеличивает скорость химической реакции",
                "experimental_data": {
                    "materials": [
                        {"name": "раствор перекиси водорода", "quantity": 100, "unit": "ml"},
                        {"name": "йодид калия", "quantity": 5, "unit": "g"},
                        {"name": "крахмал", "quantity": 2, "unit": "g"}
                    ],
                    "methods": [
                        "Приготовление растворов",
                        "Измерение оптической плотности",
                        "Статистическая обработка данных"
                    ],
                    "expected_results": "График зависимости скорости реакции от температуры",
                    "budget_constraints": {"max_cost": 5000, "currency": "RUB"},
                    "time_constraints": {"duration": "2 недели"},
                    "equipment": ["спектрофотометр", "термостат", "мерные колбы"],
                    "safety_considerations": "Работа в перчатках и защитных очках",
                    "field_of_study": "chemistry"
                }
            }
        }
        return Response(example_data)

    else:  # POST запрос
        serializer = ExperimentCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                cache_key = f"quick_validate_{hash(str(serializer.validated_data))}"
                cached_result = cache.get(cache_key)

                if cached_result:
                    return Response(cached_result)

                processed_data = deepseek_service.preprocess_experiment_data({
                    'title': serializer.validated_data['title'],
                    'description': serializer.validated_data['description'],
                    'hypothesis': serializer.validated_data.get('hypothesis', ''),
                    **serializer.validated_data['experimental_data']
                })

                result = deepseek_service.validate_experiment_design(processed_data)

                cache.set(cache_key, result, timeout=3600)

                return Response(result)

            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])  # Временно разрешаем без аутентификации
    def suggest_improvements(self, request):
        """
        Получить предложения по улучшению эксперимента
        """
        serializer = ExperimentCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                processed_data = deepseek_service.preprocess_experiment_data({
                    'title': serializer.validated_data['title'],
                    'description': serializer.validated_data['description'],
                    'hypothesis': serializer.validated_data.get('hypothesis', ''),
                    **serializer.validated_data['experimental_data']
                })

                improvements = deepseek_service.suggest_improvements(processed_data)

                return Response(improvements)

            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MLModelVersionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MLModelVersion.objects.filter(is_active=True)
    serializer_class = MLModelVersionSerializer
    permission_classes = [AllowAny]  # Временно разрешаем без аутентификации


class ExperimentTestJWTView(View):
    """HTML страница для тестирования анализа экспериментов"""

    def get(self, request):
        return render(request, 'ml/experiment_test_jwt.html')


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .service import DeepSeekAnalyzer

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


"""@api_view(['GET', 'POST'])  # ✅ Добавляем GET для DRF интерфейса
@permission_classes([IsAuthenticated])
def analyze_experiment(request):

    API endpoint для анализа научных данных

    if request.method == 'GET':
        # Показываем пример данных для DRF интерфейса
        return Response({
            'message': 'Используйте POST запрос для анализа данных',
            'example_request': {
                'experiment_data': 'Температура: [20,25,30,35,40], Реакция: [1.2,1.8,2.5,3.1,3.8]',
                'research_question': 'Проанализируй зависимость скорости реакции от температуры'
            },
            'required_fields': ['experiment_data', 'research_question']
        })

    elif request.method == 'POST':
        # Существующая логика для POST запросов
        experiment_data = request.data.get('experiment_data')
        research_question = request.data.get('research_question')

        if not experiment_data or not research_question:
            return Response({
                'success': False,
                'error': 'Отсутствуют experiment_data или research_question'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            from .service import DeepSeekAnalyzer
            analyzer = DeepSeekAnalyzer()
            result = analyzer.analyze_scientific_data(experiment_data, research_question)
            return Response(result)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)"""


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_experiment(request):
    """
    API endpoint для анализа научных данных
    """
    try:
        experiment_data = request.data.get('experiment_data')
        research_question = request.data.get('research_question')

        if not experiment_data or not research_question:
            return Response({
                'success': False,
                'error': 'Отсутствуют experiment_data или research_question'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Используем наш сервис для анализа
        from .service import DeepSeekAnalyzer
        analyzer = DeepSeekAnalyzer()
        result = analyzer.analyze_scientific_data(experiment_data, research_question)

        return Response(result)

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@login_required
def ai_analysis_page(request):
    """Страница с интерфейсом AI анализа"""
    return render(request, 'ml/ai_analysis.html')