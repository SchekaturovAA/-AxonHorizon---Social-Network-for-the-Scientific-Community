from django.core.cache.backends.base import BaseCache
import pymongo
from datetime import datetime, timedelta
import pickle


class MongoCacheBackend(BaseCache):
    def __init__(self, location, params):
        super().__init__(params)
        self._collection = self._get_collection()

    def _get_collection(self):
        # Подключение к локальной MongoDB
        client = pymongo.MongoClient('localhost', 27017)
        db = client['axon_horizon_cache']
        collection = db['django_cache']

        # Создаем TTL индекс для автоматического удаления просроченных записей
        collection.create_index("expires", expireAfterSeconds=0)
        return collection

    def add(self, key, value, timeout=None, version=None):
        key = self.make_key(key, version=version)
        expires = self._get_expires(timeout)

        try:
            self._collection.insert_one({
                '_id': key,
                'value': pickle.dumps(value),
                'expires': expires
            })
            return True
        except pymongo.errors.DuplicateKeyError:
            return False

    def get(self, key, default=None, version=None):
        key = self.make_key(key, version=version)
        doc = self._collection.find_one({'_id': key})

        if doc:
            # Проверяем не истекло ли время
            if doc.get('expires') and doc['expires'] < datetime.utcnow():
                self._collection.delete_one({'_id': key})
                return default

            return pickle.loads(doc['value'])
        return default

    def set(self, key, value, timeout=None, version=None):
        key = self.make_key(key, version=version)
        expires = self._get_expires(timeout)

        self._collection.replace_one(
            {'_id': key},
            {
                '_id': key,
                'value': pickle.dumps(value),
                'expires': expires
            },
            upsert=True
        )

    def delete(self, key, version=None):
        key = self.make_key(key, version=version)
        self._collection.delete_one({'_id': key})

    def clear(self):
        self._collection.delete_many({})

    def _get_expires(self, timeout):
        if timeout is None:
            return None
        return datetime.utcnow() + timedelta(seconds=timeout)