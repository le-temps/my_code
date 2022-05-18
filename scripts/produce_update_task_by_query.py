import argparse
import json

from service.db.elasticsearch import es
from service.db.redis import redis_queue
from utils.config import settings
from utils.logger import logger
from utils.time import get_current_time_string

VALUE_NAME_MAPPING_DICT = {}
for i, e in enumerate(settings.raw_table.type):
    VALUE_NAME_MAPPING_DICT[e] = settings.raw_table.value_name[i]

def get_task_value(data, value_name):
    try:
        value_names = value_name.split(".")
        for e in value_names:
            data = data[e]
        if (type(data) is list) or (type(data) is dict):
            raise Exception("Get task value error: result is still a list or dict.")
        return data
    except Exception as e:
        raise Exception(f"Input data struct error: not include field: {value_name}")

def produce_update_task_by_query(type, query_string):
    if type not in VALUE_NAME_MAPPING_DICT:
        raise Exception("type not valid.")
    logger.info(f"正在生成任务，type: {type}, query_string: {query_string}")
    values = []
    for e in es.scan_by_query_string(settings.elasticsearch.index_prefix + type, query_string):
        values.append([get_task_value(e["_source"], VALUE_NAME_MAPPING_DICT[type]), get_current_time_string("time")])
    logger.info(f"查询ES结束，共可生成{len(values)}个更新任务")
    if len(values) > 0:
        redis_queue.produce(*[json.dumps({"source_index_type": type, "destination_index_type": type.split("_")[0], "value":e[0], "try_num":0, "create_time":e[1]}) for e in values if e is not None and e != ""])
    logger.info("生成更新任务结束。")