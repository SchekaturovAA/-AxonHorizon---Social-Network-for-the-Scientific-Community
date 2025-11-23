from django.core.management.base import BaseCommand
from utils.mongo_cache import MongoCacheHelper


class Command(BaseCommand):
    help = 'Clear MongoDB cache'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Clear entire cache'
        )

    def handle(self, *args, **options):
        if options['all']:
            MongoCacheHelper.clear_cache()
            self.stdout.write(
                self.style.SUCCESS('Successfully cleared entire MongoDB cache')
            )
        else:
            self.stdout.write('Use --all to clear entire cache')