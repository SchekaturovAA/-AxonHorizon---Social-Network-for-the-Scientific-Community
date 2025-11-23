from django.core.management.base import BaseCommand
from utils.mongo_cache import MongoCacheHelper


class Command(BaseCommand):
    help = 'Show MongoDB cache statistics'

    def handle(self, *args, **options):
        stats = MongoCacheHelper.get_cache_stats()

        self.stdout.write("MongoDB Cache Statistics:")
        self.stdout.write(f"  Total items: {stats['total_items']}")
        self.stdout.write(f"  Active items: {stats['active_items']}")
        self.stdout.write(f"  Expired items: {stats['expired_items']}")