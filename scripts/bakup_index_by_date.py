import argparse
import json

from service.db.elasticsearch import es
from service.db.redis import redis_queue
from utils.config import settings
from utils.logger import logger

def bakup_index_by_date(index, date):
    body_str = ""
    with open(f"data/{index}.json", "r") as r:
        for i, line in enumerate(r):
            if i != 0:
                body_str += line
    bakup_index = index + "_" + date
    body = json.loads(body_str)
    logger.debug("create index request body: ", body)
    es.create_index(bakup_index, body)
    logger.info(f"创建Index: {bakup_index}成功。")
    es.reindex(index, bakup_index)
    index_count = es.count_by_query_string(index, "*")
    bakup_index_count = es.count_by_query_string(index, "*")
    logger.info(f"备份到Index: {bakup_index}完成，源Index count: {index_count}, 备份Index count: {bakup_index_count}")