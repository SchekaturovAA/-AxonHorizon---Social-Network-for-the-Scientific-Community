from AxonHorizon.mongo_cache import MongoCacheBackend
from datetime import datetime
import json
# Инициализация кэша
cache = MongoCacheBackend(location='', params={})


class MongoCacheHelper:
    @staticmethod
    def cache_recommendations(user_id, recommendations, timeout=3600):
        """Кэширование рекомендаций постов на 1 час"""
        cache_key = f'user_{user_id}_recommendations'
        cache.set(cache_key, recommendations, timeout)
        return True

    @staticmethod
    def get_cached_recommendations(user_id):
        """Получение кэшированных рекомендаций"""
        cache_key = f'user_{user_id}_recommendations'
        return cache.get(cache_key)

    @staticmethod
    def cache_page(path, content, timeout=300):
        """Кэширование HTML страниц на 5 минут"""
        cache_key = f'page_{path}'
        cache.set(cache_key, content, timeout)

    @staticmethod
    def cache_chat_messages(chat_id, messages, timeout=86400):
        """Кэширование сообщений чата на 24 часа"""
        cache_key = f'chat_{chat_id}_messages'
        cache.set(cache_key, messages, timeout)

    @staticmethod
    def cache_popular_posts(posts, timeout=1800):
        """Кэширование популярных постов на 30 минут"""
        cache_key = 'popular_posts'
        cache.set(cache_key, posts, timeout)

    @staticmethod
    def get_cached_popular_posts():
        """Получение кэшированных популярных постов"""
        return cache.get('popular_posts')

    @staticmethod
    def get_cache_stats():
        """Статистика кэша"""
        collection = cache._collection
        total = collection.count_documents({})
        expired = collection.count_documents({
            'expires': {'$lt': datetime.utcnow()}
        })
        return {
            'total_items': total,
            'expired_items': expired,
            'active_items': total - expired
        }

    @staticmethod
    def clear_cache():
        """Очистка всего кэша"""
        cache.clear()

    @staticmethod
    def cache_news_feed(user_id, content_type, page_number, posts_data, timeout=300):
        """Кэширование ленты новостей на 5 минут"""
        cache_key = f'news_feed_{user_id}_{content_type}_{page_number}'
        cache.set(cache_key, posts_data, timeout)

    @staticmethod
    def get_cached_news_feed(user_id, content_type, page_number):
        """Получение кэшированной ленты новостей"""
        cache_key = f'news_feed_{user_id}_{content_type}_{page_number}'
        return cache.get(cache_key)

    @staticmethod
    def cache_favourite_posts(user_id, scientific_field_id, post_type, posts_data, timeout=600):
        """Кэширование избранных постов на 10 минут"""
        cache_key = f'favourites_{user_id}_{scientific_field_id or "all"}_{post_type or "all"}'
        cache.set(cache_key, posts_data, timeout)

    @staticmethod
    def get_cached_favourite_posts(user_id, scientific_field_id, post_type):
        """Получение кэшированных избранных постов"""
        cache_key = f'favourites_{user_id}_{scientific_field_id or "all"}_{post_type or "all"}'
        return cache.get(cache_key)

    @staticmethod
    def cache_post_detail(post_id, post_data, timeout=1800):
        """Кэширование деталей поста на 30 минут"""
        cache_key = f'post_detail_{post_id}'
        cache.set(cache_key, post_data, timeout)

    @staticmethod
    def get_cached_post_detail(post_id):
        """Получение кэшированных деталей поста"""
        cache_key = f'post_detail_{post_id}'
        return cache.get(cache_key)

    @staticmethod
    def cache_chat_list(user_id, chats_data, timeout=300):
        """Кэширование списка чатов на 5 минут"""
        cache_key = f'chat_list_{user_id}'
        cache.set(cache_key, chats_data, timeout)

    @staticmethod
    def get_cached_chat_list(user_id):
        """Получение кэшированного списка чатов"""
        cache_key = f'chat_list_{user_id}'
        return cache.get(cache_key)

    @staticmethod
    def cache_chat_messages(chat_id, messages_data, timeout=300):
        """Кэширование сообщений чата на 5 минут"""
        cache_key = f'chat_messages_{chat_id}'
        cache.set(cache_key, messages_data, timeout)

    @staticmethod
    def get_cached_chat_messages(chat_id):
        """Получение кэшированных сообщений чата"""
        cache_key = f'chat_messages_{chat_id}'
        return cache.get(cache_key)

    @staticmethod
    def invalidate_user_cache(user_id):
        """Инвалидация всего кэша пользователя"""
        # В реальной реализации нужно удалить все ключи, связанные с пользователем
        # Это упрощенная версия
        pass

    @staticmethod
    def invalidate_post_cache(post_id):
        """Инвалидация кэша поста"""
        cache_key = f'post_detail_{post_id}'
        cache.delete(cache_key)

    @staticmethod
    def invalidate_chat_cache(chat_id):
        """Инвалидация кэша чата"""
        cache_key = f'chat_messages_{chat_id}'
        cache.delete(cache_key)


class CacheStats:
    hits = 0
    misses = 0

    @classmethod
    def hit(cls):
        cls.hits += 1

    @classmethod
    def miss(cls):
        cls.misses += 1

    @classmethod
    def get_stats(cls):
        total = cls.hits + cls.misses
        if total == 0:
            return 0
        return (cls.hits / total) * 100


