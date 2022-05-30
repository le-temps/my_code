from fastapi import APIRouter, Response, status, Header
import traceback
from pydantic import BaseModel
from typing import Dict, List, Optional
import json

from service.db.redis import redis_queue
from utils.config import settings
from utils.logger import logger
from utils.time import get_current_time_string

router = APIRouter()


##### raw_table insert
class InputData(BaseModel):
    source_index_type: str
    destination_index_type: str
    values: list

class InputResponse(BaseModel):
    status: str
    message: str

@router.post("/api/v1/task", response_model=InputResponse, tags=["raw_table"])
async def insert_data_to_raw_table(input_data: InputData, response: Response, token: Optional[str]=Header(None)):
    if token != settings.service_auth.token:
        response.status_code=401
        return InputResponse(status=401, message="Unauthorized request.")
    response.status_code=200
    try:
        tasks = []
        task_create_time = get_current_time_string("time")
        for value in input_data.values:
            tasks.append(json.dumps({"source_index_type": input_data.source_index_type, "destination_index_type": input_data.destination_index_type, "value": value, "try_num": 0, "create_time": task_create_time}))
        redis_queue.produce(*tasks)
        return InputResponse(status=200, message="OK.")
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error(e)
        response.status_code=500
        return InputResponse(status=500, message=str(e))