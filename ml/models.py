from django.db import models
from django.conf import settings

class UserEmbedding(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='embedding', verbose_name="Пользователь")
    embedding_vector = models.TextField(verbose_name="Вектор эмбеддинга")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Эмбеддинг пользователя"
        verbose_name_plural = "Эмбеддинги пользователей"

    def __str__(self):
        return f"Эмбеддинг {self.user}"

class PaperEmbedding(models.Model):
    doi = models.CharField(max_length=100, unique=True, verbose_name="DOI")
    title = models.CharField(max_length=255, verbose_name="Название")
    embedding_vector = models.TextField(verbose_name="Вектор эмбеддинга")
    scientific_field = models.ForeignKey('users.ScientificField', on_delete=models.CASCADE, verbose_name="Научная область")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Эмбеддинг статьи"
        verbose_name_plural = "Эмбеддинги статей"

    def __str__(self):
        return self.title

class Recommendation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recommendations', verbose_name="Пользователь")
    recommended_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recommended_to', verbose_name="Рекомендованный пользователь")
    score = models.FloatField(verbose_name="Оценка сходства")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Рекомендация"
        verbose_name_plural = "Рекомендации"
        unique_together = ('user', 'recommended_user')

    def __str__(self):
        return f"Рекомендация для {self.user} -> {self.recommended_user}"

# блок для анализа данных
class Experiment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'В обработке'),
        ('processing', 'Обрабатывается'),
        ('completed', 'Завершен'),
        ('failed', 'Ошибка'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='experiments',
                             verbose_name="Пользователь")
    title = models.CharField(max_length=255, verbose_name='Название эксперимента')
    description = models.TextField(verbose_name='Описание эксперимента')
    input_data = models.JSONField(verbose_name='Входные данные')
    output_data = models.JSONField(verbose_name='Результаты', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    feasibility_score = models.FloatField(null=True, blank=True, verbose_name='Оценка реализуемости')
    plausibility_score = models.FloatField(null=True, blank=True, verbose_name='Оценка правдоподобности')
    improvements = models.JSONField(null=True, blank=True, verbose_name='Предложения по улучшению')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Эксперимент"
        verbose_name_plural = "Эксперименты"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user}"


class MLModelVersion(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название модели')
    version = models.CharField(max_length=50, verbose_name='Версия')
    description = models.TextField(verbose_name='Описание модели')
    is_active = models.BooleanField(default=True, verbose_name='Активная версия')
    api_endpoint = models.URLField(verbose_name='API эндпоинт')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Версия ML модели"
        verbose_name_plural = "Версии ML моделей"
        unique_together = ['name', 'version']

    def __str__(self):
        return f"{self.name} v{self.version}"