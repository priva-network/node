from cachetools import TTLCache
import shelve

class CacheStorage:
    def __init__(self):
        self.cache = None

    def init_config(self, config):
        self.cache = TTLCache(maxsize=config.CACHE_MAX_SIZE, ttl=config.CACHE_DEFAULT_TTL)

    def get(self, key):
        return self.cache.get(key)
    
    def set(self, key, value):
        self.cache[key] = value

class PersistentStorage:
    def __init__(self):
        self.db_file_path = None
        # internal cache for faster access
        self._cache = None

    def init_config(self, config):
        self.db_file_path = config.DATABASE_FILE_PATH
        self._cache = TTLCache(maxsize=config.CACHE_MAX_SIZE, ttl=config.CACHE_DEFAULT_TTL)

    def get(self, key):
        if key in self._cache:
            return self._cache[key]
        
        with shelve.open(self.db_file_path) as db:
            value = db.get(key)
            self._cache[key] = value
            return value

    def set(self, key, value):
        with shelve.open(self.db_file_path) as db:
            db[key] = value
        self._cache[key] = value

# Create a global instances of the storage classes
cache_storage = CacheStorage()
persistent_storage = PersistentStorage()
