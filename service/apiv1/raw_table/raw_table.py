from fastapi import APIRouter, Response, status, Header
import traceback
from pydantic import BaseModel
from typing import Dict, List, Optional
import json

from service.db.elasticsearch import es
from service.db.redis import redis_queue
from utils.config import settings
from utils.logger import logger
from utils.time import get_current_time_string

router = APIRouter()


##### raw_table insert
class InputData(BaseModel):
    type: str
    data: list

class InputResponse(BaseModel):
    status: str
    message: str


def check_input_type(type):
    if type in settings.raw_table.type:
        return True
    else:
        return False

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

@router.post("/api/v1/raw_table", response_model=InputResponse, tags=["raw_table"])
async def insert_data_to_raw_table(input_data: InputData, response: Response, token: Optional[str]=Header(None)):
    if token != settings.service_auth.token:
        response.status_code=401
        return InputResponse(status=401, message="Unauthorized request.")
    response.status_code=200
    try:
        if not check_input_type(input_data.type):
            response.status_code=400
            return InputResponse(status=400, message="Input data not correct.")
        insert_time = get_current_time_string("time")
        es.bulk_insert(settings.elasticsearch.index_prefix + input_data.type, input_data.data, {"insert_raw_table_timestamp": insert_time})
        tasks = []
        for e in input_data.data:
            tasks.append({"source_index_type":input_data.type, "destination_index_type":input_data.type.split("_")[0], "value":get_task_value(e, VALUE_NAME_MAPPING_DICT[input_data.type]), "try_num":0, "create_time":insert_time})
        tasks = [json.dumps(t) for t in tasks if t["value"] != "" and t["value"] is not None]
        redis_queue.produce(*tasks)
        return InputResponse(status=200, message="OK.")
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error(e)
        response.status_code=500
        return InputResponse(status=500, message=str(e))