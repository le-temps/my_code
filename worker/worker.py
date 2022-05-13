import json
from multiprocessing import Process
from utils.logger import logger

from service.db.redis import redis_queue
from worker.ip import ip_update
from worker.domain import domain_update
from worker.organization import organization_update

update_func = {
    "ip": ip_update,
    "domain": domain_update,
    "organization": organization_update,
    "cert": cert_parse
}

def worker():
    _count = 0
    while True:
        task = json.loads(redis_queue.consume())
        try:
            update_func[task["destination_index_type"]](task["value"], task["source_index_type"])
            redis_queue.finish(task)
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(e)
            redis_queue.reproduce(task)
        _count += 1
        if _count % 1000 == 0:
            logger.info(f"Worker finished task num: {_count}")


def start_worker():
    p = Process(target=worker)
    p.start()
    p.join()

