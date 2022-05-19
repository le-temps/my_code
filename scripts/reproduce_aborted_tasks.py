import json

from service.db.elasticsearch import es
from service.db.redis import redis_queue
from utils.config import settings
from utils.logger import logger
from utils.time import get_current_time_string

def reproduce_aborted_tasks(reproduce_all, task_string):
    if reproduce_all:
        logger.info(f"尝试reproduce所有aborted任务...")
        num = redis_queue.check_unfinished_task(settings.redis.aborted_list_name, settings.redis.tasks_list_name)
        logger.info(f"完成reproduce所有aborted任务，共计{num}")
    else:
        logger.info(f"尝试reproduce任务 {task_string} ...")
        redis_queue.produce(task_string)
        logger.info(f"完成reproduce任务 {task_string}")