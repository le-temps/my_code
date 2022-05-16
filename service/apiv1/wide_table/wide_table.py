from fastapi import APIRouter, Response, status, Header
import traceback
from pydantic import BaseModel
from typing import Dict, List, Optional

from service.db.elasticsearch import es
from utils.config import settings
from utils.logger import logger
from utils.time import get_current_time_string

router = APIRouter()

#### wide_table search
#TODO add wide_table search api

##### wide_table detail
class DetailResponse(BaseModel):
    status: str
    message: str

def get_detail(type, value, response, token):
    if token != settings.service_auth.token:
        response.status_code=401
        return DetailResponse(status=401, message="Unauthorized request.")
    response.status_code=200
    try:
        res = es.search_by_query_string(index=settings.elasticsearch.index_prefix + value, query_string=f"{type}:{value}")
        if len(res["hits"]["hits"]) > 0:
            return DetailResponse(status=200, message=res["hits"]["hits"][0]["_source"])
        else:
            return DetailResponse(status=200, message={})
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error(e)
        response.status_code=500
        return DetailResponse(status=500, message=str(e))

@router.get("/api/v1/domain/{domain}", response_model=DetailResponse, tags=["wide_table", "domain"])
async def get_domain_detail(domain: str, response: Response, token: Optional[str]=Header(None)):
    return get_detail("domain", domain, response, token)

@router.get("/api/v1/ip/{ip}", response_model=DetailResponse, tags=["wide_table", "ip"])
async def get_ip_detail(ip: str, response: Response, token: Optional[str]=Header(None)):
    return get_detail("ip", ip, response, token)

@router.get("/api/v1/organization/{organization}", response_model=DetailResponse, tags=["wide_table", "organization"])
async def get_organization_detail(organization: str, response: Response, token: Optional[str]=Header(None)):
    return get_detail("organization", ip, response, token)

@router.get("/api/v1/cert/{cert}", response_model=DetailResponse, tags=["wide_table", "cert"])
async def get_cert_detail(cert: str, response: Response, token: Optional[str]=Header(None)):
    return get_detail("cert", cert, response, token)