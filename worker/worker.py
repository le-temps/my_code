import json
import time
import traceback
from multiprocessing import Process

from utils.logger import logger
from utils.config import settings
from utils.time import get_current_time_string, compare_time_string
from service.db.redis import redis_queue
from worker.ip import ip_update
from worker.domain import domain_update
from worker.organization import organization_update
from worker.cert import cert_parse
from worker.bakup_wide_table import bakup_wide_table

worker_func = {
    "ip": ip_update,
    "domain": domain_update,
    "organization": organization_update,
    "cert": cert_parse,
    "bakup_wide_table": bakup_wide_table
}

def worker():
    _count = 0
    while True:
        logger.debug("尝试从redis获取更新任务...")
        task = json.loads(redis_queue.consume())
        try:
            logger.debug(f"获取到任务: {task}，正在执行中...")
            # execute task
            if task["value"] == "" or task["value"] is None:
                logger.warning(f"Got a empty task: {task}")
            else:
                tasks = worker_func[task["destination_index_type"]](task["value"], task["source_index_type"])
                # 如果某个任务会触发提交一个后续任务，则提交
                if tasks is not None and len(tasks) > 0:
                    redis_queue.produce(*[json.dumps(task) for task in tasks])
            redis_queue.finish(json.dumps(task))
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(e)
            try:
                redis_queue.reproduce(json.dumps(task))
            except:
                pass
        _count += 1
        if _count % 1000 == 0:
            logger.info(f"Worker finished task num: {_count}")

def timeloop_worker():
    for work_config in settings.timeloop:
        t = timeloop(work_config)
        t.start()


def start_worker(worker_num):
    process = []
    for i in range(worker_num):
        process.append(Process(target=worker))
    process.append(Process(target=timeloop_worker))
    for p in process:
        p.start()
    for p in process:
        p.join()
