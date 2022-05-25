from fastapi import APIRouter, Response, status, Header
import traceback
from pydantic import BaseModel
from typing import Dict, List, Optional

from service.db.elasticsearch import es
from utils.config import settings
from utils.logger import logger
from utils.time import get_current_time_string

IMPORTANT = {
    "domain": ["domain", "icp.main_licence", "icp.unit_name", "psr.record_id", "psr.unit_name", "rr.A.ip", "certs.cert", "whois.registrant.organization", "web.http.title", "web.https.title"],
    "ip": ["ip", "geo.country", "geo.prov", "geo.city", "geo.district", "domains.reverse_domains", "protocols.port", "protocols.protocol", "dns.type", "certs.cert"],
    "organization": ["organization", "info.business_status", "info.legal_person", "info.registered_capital", "info.province", "info.city", "info.district"]
}

router = APIRouter()

def remove_object_field(object, field_name):
    if type(object) is dict:
        if field_name in object:
            object.pop(field_name)
        for key in object:
            if type(object[key]) is dict or type(object[key]) is list:
                remove_object_field(object[key], field_name)
    elif type(object) is list:
        for e in object:
            if type(e) is dict or type(e) is list:
                remove_object_field(e, field_name)
    return object

#### wide_table search
#TODO add wide_table search api
class SearchInput(BaseModel):
    keyword: str
    filters: str

class SearchResponse(BaseModel):
    state: str
    meta: dict
    payload: dict = []
    msg: str = ""

@router.post("/api/v1/search/{field}", response_model=SearchResponse, tags=["wide_table"])
async def get_search(field: str, page: int, rows: int, input_data: SearchInput, response: Response, token: Optional[str]=Header(None)):
    if token != settings.service_auth.token:
        response.status_code=401
        return SearchResponse(state=903, msg="Authentication Failed")
    try:
        if input_data.filters:
            query_string = input_data.filters
        elif input_data.keyword:
            query_string = input_data.keyword
        else:
            query_string = "*"
        res = es.search_by_query_string_with_from_size(index=settings.elasticsearch.index_prefix + field, query_string=query_string, page * rows, rows, source=IMPORTANT[field])
        if len(res["hits"]["hits"]) > 0:
            return DetailResponse(state=800, {"total":len(res["hits"]["hits"][0]["_source"])}, payload=remove_object_field(res["hits"]["hits"][0]["_source"], "insert_raw_table_timestamp"))
        else:
            return DetailResponse(state=800, {"total":0}, payload={})
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error(e)
        response.status_code=500
        return DetailResponse(state=910, msg=str(e))

@router.post("/api/v1/search/{field}/stats", response_model=SearchResponse, tags=["wide_table"])
async def get_search_stats(field: str, input_data: SearchInput, response: Response, token: Optional[str]=Header(None)):
    if token != settings.service_auth.token:
        response.status_code=401
        return SearchResponse(state=903, msg="Authentication Failed")
    try:
        if input_data.filters:
            query_string = input_data.filters
        elif input_data.keyword:
            query_string = input_data.keyword
        else:
            query_string = "*"
        res = es.search_by_query_string_with_from_size(index=settings.elasticsearch.index_prefix + field, query_string=f"{type}:{value}")
        if len(res["hits"]["hits"]) > 0:
            return DetailResponse(state=800, payload=remove_object_field(res["hits"]["hits"][0]["_source"], "insert_raw_table_timestamp"))
        else:
            return DetailResponse(state=800, payload={})
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error(e)
        response.status_code=500
        return DetailResponse(state=910, msg=str(e))

##### wide_table detail
class DetailResponse(BaseModel):
    state: str
    payload: dict = []
    msg: str = ""

def get_detail(type, value, response, token):
    if token != settings.service_auth.token:
        response.status_code=401
        return DetailResponse(state=903, msg="Authentication Failed")
    response.status_code=200
    try:
        res = es.search_by_query_string(index=settings.elasticsearch.index_prefix + type, query_string=f"{type}:{value}")
        if len(res["hits"]["hits"]) > 0:
            if type == "ip":
                # ip_cert
                for protocol in res["hits"]["hits"][0]["_source"]["protocols"]:
                    if protocol["protocol"] == "https" and cert_hash in protocol["data"]:
                        cert_res = es.search_by_query_string(index=settings.elasticsearch.index_prefix + "cert", query_string=f"cert:{protocol["data"]["cert_hash"]}")
                        res["hits"]["hits"][0]["_source"]["certs"] = [cert_res["hits"]["hits"][0]["_source"]]
                        break
            if type == "domain":
                # domain_cert
                if res["hits"]["hits"][0]["_source"]["web"] and res["hits"]["hits"][0]["_source"]["web"]["https"] and cert_hash in res["hits"]["hits"][0]["_source"]["web"]["https"][0]:
                    cert_res = es.search_by_query_string(index=settings.elasticsearch.index_prefix + "cert", query_string=f"cert:{res["hits"]["hits"][0]["_source"]["web"]["https"][0]["cert_hash"]}")
                    res["hits"]["hits"][0]["_source"]["certs"] = [cert_res["hits"]["hits"][0]["_source"]]
                    break
                # domain_subdomain
                subdomains_res = es.search_by_query_string_with_from_size(index=settings.elasticsearch.index_prefix + "domain", query_string=" OR ".join([f"domain:{domain}" for domain in res["hits"]["hits"][0]["_source"]["subdomains"]]), 0, 10, source=IMPORTANT["domain"])
                res["hits"]["hits"][0]["_source"]["subdomains"] = [e["_source"] for e in subdomains_res["hits"]["hits"]]
            if type == "organization":
                # organization_subdomain
                domains_res = es.search_by_query_string_with_from_size(index=settings.elasticsearch.index_prefix + "domain", query_string=" OR ".join([f"domain:{domain}" for domain in res["hits"]["hits"][0]["_source"]["domains"]]), 0, 10, source=IMPORTANT["domain"])
                res["hits"]["hits"][0]["_source"]["domains"] = [e["_source"] for e in domains_res["hits"]["hits"]]
            return DetailResponse(state=800, payload=remove_object_field(res["hits"]["hits"][0]["_source"], "insert_raw_table_timestamp"))
        else:
            return DetailResponse(state=800, payload={})
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error(e)
        response.status_code=500
        return DetailResponse(state=910, msg=str(e))

@router.get("/api/v1/domain/{domain}", response_model=DetailResponse, tags=["wide_table", "domain"])
async def get_domain_detail(domain: str, response: Response, token: Optional[str]=Header(None)):
    return get_detail("domain", domain, response, token)

@router.get("/api/v1/ip/{ip}", response_model=DetailResponse, tags=["wide_table", "ip"])
async def get_ip_detail(ip: str, response: Response, token: Optional[str]=Header(None)):
    return get_detail("ip", ip, response, token)

@router.get("/api/v1/organization/{organization}", response_model=DetailResponse, tags=["wide_table", "organization"])
async def get_organization_detail(organization: str, response: Response, token: Optional[str]=Header(None)):
    return get_detail("organization", organization, response, token)

@router.get("/api/v1/cert/{cert}", response_model=DetailResponse, tags=["wide_table", "cert"])
async def get_cert_detail(cert: str, response: Response, token: Optional[str]=Header(None)):
    return get_detail("cert", cert, response, token)