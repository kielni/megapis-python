import json

import redis

class MegapisTask():
    store = None
    default_config = {}
    config = {}

    def __init__(self, config):
        for key in self.default_config:
            if not config.get(key):
                config[key] = self.default_config[key]
        self.config = config
        redis_config = self.config.get('redis', {})
        self.store = redis.StrictRedis(
            host=redis_config.get('host', 'localhost'),
            port=redis_config.get('port', 6379),
            db=redis_config.get('db', 0)
        )

    def run(self):
        print('MegapisTask.run -- override me')

    def add(self, key, values):
        for value in values:
            self.store.sadd(key, json.dumps(value))

    def replace(self, key, values):
        self.store.delete(key)
        self.add(key, values)

    def consume(self, key):
        values = self.store.smembers(key)
        self.store.delete(key)
        return list(values)

    def read(self, key):
        return [json.loads(x.decode()) for x in list(self.store.smembers(key))]

