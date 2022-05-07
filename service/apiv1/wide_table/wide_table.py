from fastapi import APIRouter, Response, status, Header
import traceback
from pydantic import BaseModel
from typing import Dict, List, Optional
import time

from service.db.elasticsearch import es
from utils.config import settings
from utils.logger import logger

router = APIRouter()


##### wide_table organization detail search

class DetailOrganizationResponse(BaseModel):
    status: str
    message: str


@router.get("/api/v1/organization/{organization_name}", response_model=DetailOrganizationResponse, tags=["wide_table", "organization"])
async def insert_data_to_raw_table(organization_name: str, response: Response, token: Optional[str]=Header(None)):
    if token != settings.service_auth.token:
        response.status_code=401
        return DetailOrganizationResponse(status=401, message="Unauthorized request.")
    response.status_code=200
    try:
        res = es.search_by_query_string(index=settings.wide_table.organization_index, query_string=f"name:{organization_name}")
        if len(res["hits"]["hits"]) > 0:
            return DetailOrganizationResponse(status=200, message=res["hits"]["hits"][0]["_source"])
        else:
            return DetailOrganizationResponse(status=200, message={})
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error(e)
        response.status_code=500
        return DetailOrganizationResponse(status=500, message=str(e))
