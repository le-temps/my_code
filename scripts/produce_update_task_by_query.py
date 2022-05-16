import argparse

from service.db.elasticsearch import es
from service.db.redis import redis_queue
from utils.config import settings
from utils.logger import logger

INPUT_DATA_VALUE_MAPPING = {
    "organization": "name",
    "domain": "domain",
    "ip": "ip"
}

def produce_update_task_by_query(type, query_string):
    values = []
    for e in es.scan_by_query_string(settings.elasticsearch.index_prefix + type, query_string):
        values.append([e["_source"][INPUT_DATA_VALUE_MAPPING[type.split("_")[0]]], e["_source"]["insert_raw_table_timestamp"]])
    logger.info(f"查询ES结束，共可生成{len(values)}个更新任务")
    redis_queue.produce(*[json.dumps({"source_index_type": type, "destination_index_type": type.split("_")[0], "value":e[0], "try_num":0, "create_time":e[1]}) for e in value])
    logger.info("生成更新任务结束。")