from django.core.management.base import BaseCommand
from ml.models import MLModelVersion

class Command(BaseCommand):
    help = 'Create initial ML model versions'

    def handle(self, *args, **options):
        MLModelVersion.objects.get_or_create(
            name='DeepSeek Experiment Analyzer',
            version='1.0',
            defaults={
                'description': 'Модель для анализа научных экспериментов и оценки их реализуемости',
                'is_active': True,
                'api_endpoint': 'https://api.deepseek.com/v1'
            }
        )
        self.stdout.write(
            self.style.SUCCESS('Successfully created ML model versions')
        )