import redis
import json
import traceback

from utils.config import settings
from utils.logger import logger
from utils.time import get_current_time_string

class RedisQueue:

    def __init__(self, host, port, password):
        self.redis = redis.Redis(host=host, port=port, password=password)
        logger.info(f"Init Redis done, check_unfinished_task num: {self.check_unfinished_task(settings.redis.distributed_list_name, settings.redis.tasks_list_name)}")

    def __instance__(self):
        return self.redis

    def check_unfinished_task(self, src, dst):
        _count = 0
        e = self.redis.rpop(src)
        while(e):
            _count += 1
            self.redis.lpush(dst, e)
            e = self.redis.rpop(src)
        return _count

    def produce(self, *task):
        self.redis.lpush(settings.redis.tasks_list_name, *task)
        logger.debug(f"redis_queue produce tasks count: {len(task)}")

    def consume(self):
        return self.redis.brpoplpush(settings.redis.tasks_list_name, settings.redis.distributed_list_name)

    def finish(self, task):
        self.redis.lrem(settings.redis.distributed_list_name, 1, task)
        task = json.loads(task)
        task["finish_time"] = get_current_time_string("time")
        task = json.dumps(task)  
        self.redis.lpush(settings.redis.finished_list_name, task)
        logger.debug(f"redis_queue finish task: {task}")

    def reproduce(self, task):
        self.redis.lrem(settings.redis.distributed_list_name, 1, task)
        task = json.loads(task)
        if task["try_num"] > settings.redis.max_try_num:
            self.redis.lpush(settings.redis.aborted_list_name, task)
            logger.debug(f"redis_queue abort task: {task}")
            return
        else:
            task["try_num"] += 1
        task = json.dumps(task)
        self.produce(task)
        logger.warning(f"REPRODUCE TASK: {task}")


redis_queue = RedisQueue(host=settings.redis_auth.host, port=settings.redis_auth.port, password=settings.redis_auth.password)

