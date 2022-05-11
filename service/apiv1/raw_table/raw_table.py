from fastapi import APIRouter, Response, status, Header
import traceback
from pydantic import BaseModel
from typing import Dict, List, Optional
import time
import json

from service.db.elasticsearch import es
from service.db.redis import redis_queue
from utils.config import settings
from utils.logger import logger

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

INPUT_DATA_VALUE_MAPPING = {
    "organization": "name",
    "domain": "domain",
    "ip": "ip"
}

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
        es.bulk_insert(settings.elasticsearch.index_prefix + input_data.type, input_data.data, {"insert_raw_table_timestamp": time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))})
        redis_queue.produce(*[json.dumps({"source_index_type": input_data.type, "destination_index_type": input_data.type.split("_")[0], "value":e[INPUT_DATA_VALUE_MAPPING[input_data.type.split("_")[0]]]}) for e in input_data.data])
        if input_data.type == "domain_rr":
            ips = []
            for data in input_data.data:
                for a in data["A"]:
                    ips.append(a["ip"])
            redis_queue.produce(*[json.dumps({"source_index_type": "ip_ptr", "destination_index_type":"ip", "value":ip}) for ip in ips])
        return InputResponse(status=200, message="OK.")
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error(e)
        response.status_code=500
        return InputResponse(status=500, message=str(e))