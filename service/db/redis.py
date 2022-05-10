import redis
import traceback

from utils.config import settings
from utils.logger import logger

class RedisQueue:

    def __init__(self, host, port, password):
        self.redis = redis.Redis(host=host, port=port, password=password)
        logger.info(f"Init Redis done, check_unfinished_task num: {self.check_unfinished_task()}")

    def check_unfinished_task(self):
        _count = 0
        e = self.redis.rpop(settings.redis.distributed_list_name)
        while(e):
            _count += 1
            self.redis.lpush(settings.redis.tasks_list_name, e)
        return _count

    def produce(self, task):
        self.redis.lpush(settings.redis.tasks_list_name, task)

    def consume(self):
        return self.redis.brpoplpush(settings.redis.tasks_list_name, settings.redis.distributed_list_name)

    def finish(self, task):
        return self.redis.lrem(settings.redis.distributed_list_name, 1, task)

    def reproduce(self, task):
        self.redis.lrem(settings.redis.distributed_list_name, 1, task)
        self.produce(task)
        logger.warning(f"REPRODUCE TASK: {task}")


redis_queue = RedisQueue(host=settings.redis.host, port=settings.redis.port, password=settings.redis_auth.passowrd)

