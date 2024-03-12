from redis import Redis

class RedisStorage:
    def __init__(self):
        self.client = None

    def init_app(self, app):
        redis_url = app.config['REDIS_URL']
        if not redis_url:
            raise ValueError('Redis URL is not set')
        self.client = Redis.from_url(redis_url)

    def set(self, key, value):
        self.client.set(key, value)

    def get(self, key):
        return self.client.get(key)

# Create a global instance of RedisStorage
redis_storage = RedisStorage()
