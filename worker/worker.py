import json
import time
import traceback
from multiprocessing import Process

from utils.logger import logger
from utils.config import settings
from utils.time import get_current_time_string
from service.db.redis import redis_queue
from worker.ip import ip_update
from worker.domain import domain_update
from worker.organization import organization_update
from worker.cert import cert_parse
from worker.heartbeat import heartbeat
from scripts.bakup_index_by_date import bakup_index_by_date

update_func = {
    "ip": ip_update,
    "domain": domain_update,
    "organization": organization_update,
    "cert": cert_parse,
    "heartbeat": heartbeat
}

def worker():
    _count = 0
    date = get_current_time_string("date")
    while True:
        logger.debug("尝试从redis获取更新任务...")
        task = json.loads(redis_queue.consume())
        logger.debug(f"获取到任务: {task}，正在执行中...")
        # 如果任务日期发生改变，则先备份一下业务宽表，再进行更新任务
        # 此过程应该在每个天第一个新任务执行前进行
        # 因此每天至少应该自动生成一个单天任务，以进行宽表的备份
        task_create_date = task["create_time"][:10]
        if task_create_date != date:
            logger.info(f"Start bakuping elasticsearch wide_table of date: {date}")
            for k in update_func.keys():
                if k == "heartbeat":
                    continue
                index = settings.elasticsearch.index_prefix + k
                logger.info(f"Start bakuping index {index} of date: {date}")
                bakup_index_by_date(index, date)
                logger.info(f"Finished bakuping index {index} of date: {date}")
            logger.info(f"Finished bakuping elasticsearch wide_table of date: {date}")
            date = task_create_date
        try:
            if task["value"] == "" or task["value"] is None:
                logger.warning(f"Got a empty task: {task}")
                continue
            tasks = update_func[task["destination_index_type"]](task["value"], task["source_index_type"])
            # 如果某个任务会触发提交一个后续任务，则提交
            if tasks is not None and len(tasks) > 0:
                redis_queue.produce(*[json.dumps(task) for task in tasks])
            redis_queue.finish(json.dumps(task))
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(e)
            redis_queue.reproduce(task)
        _count += 1
        if _count % 1000 == 0:
            logger.info(f"Worker finished task num: {_count}")

def heartbeat_producer():
    while True:
        time.sleep(3600)
        redis_queue.produce(json.dumps({"source_index_type":"heartbeat", "destination_index_type":"heartbeat", "value":"heartbeat", "try_num":0, "create_time":get_current_time_string("time")}))
        


def start_worker(worker_num):
    process = []
    for i in range(worker_num):
        process.append(Process(target=worker))
    process.append(Process(target=heartbeat_producer))
    for p in process:
        p.start()
    for p in process:
        p.join()
