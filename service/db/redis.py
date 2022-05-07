import redis
import traceback

from utils.config import settings
from utils.logger import logger

class RedisQueue:

    def __init__(self, host, port, password):
        self.redis = redis.Redis(host=host, port=port, password=password)

    def produce(task):
        self.redis.lpush(settings.redis.tasks_list_name, task)

    def consume():
        return self.redis.brpoplpush(settings.redis.tasks_list_name, settings.redis.distributed_list_name)

    def finish(task):
        return self.redis.lrem(settings.redis.distributed_list_name, 1, task)

redis_queue = RedisQueue(host=settings.redis.host, port=settings.redis.port, password=settings.redis_auth.passowrd)

