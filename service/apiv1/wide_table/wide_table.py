from fastapi import APIRouter, Response, status, Header
import traceback
from pydantic import BaseModel
from typing import Dict, List, Optional

from service.db.elasticsearch import es
from utils.config import settings
from utils.logger import logger
from utils.time import get_current_time_string


#### trim result
def trim_important_result(object):
    if type(object) is dict:
        for key in object:
            object[key] = trim_important_result(object[key])
        return object
    elif type(object) is list:
        if type(object[0]) is dict:
            key = list(object[0].keys())[0]
            if key == "title":
                object = [object[-1]]
            return {key:list(set([e[key] for e in object]))}
        else:
            return object
    else:
        return object

IMPORTANT = {
    "domain": ["domain", "icp.service_licence", "icp.unit_name", "psr.record_id", "psr.unit_name", "rr.A.ip", "certs.cert", "whois.registrant.organization", "web.http.title", "web.https.title"],
    "ip": ["ip", "ports", "geo.country", "geo.prov", "geo.city", "geo.district", "domains.reverse_domains", "protocols.port", "protocols.protocol", "dns.type", "certs.cert"],
    "organization": ["organization", "info.business_status", "info.legal_person", "info.registered_capital", "info.province", "info.city", "info.district"],
    "cert": ["cert", "issuer", "subject", "subject_dn", "validity", "signature_algorithm.key_algorithm"]
}

STATS = {
    "domain": ["web.http.server", "web.https.server"],
    "ip": ["ports", "protocols.protocol", "dns.type"],
    "organization": ["info.business_status", "info.type", "info.industry"]
}

TRENDS = ["active_ip", "asset", "key_communication_infra"]
TRENDS_SORT_ORDER_FIELD_NAME = {
    "daily": "parsed_date",
    "monthly": "parsed_month"
}
TRENDS_SIZE = {
    "daily": "30",
    "monthly": "12"
}

STATES = ["port", "protocol", "http_server", "https_server"]
STATES_FIELDS = {
    "port": "ports",
    "protocol": "protocols.protocol",
    "http_server": "web.http.server",
    "https_server": "web.https.server"
}


router = APIRouter()


#### main_page
class TrendResponse(BaseModel):
    state: int
    meta: Optional[dict] = None
    payload: Optional[list] = None
    msg: Optional[str]

class StateResponse(BaseModel):
    state: int
    meta: Optional[dict] = None
    payload: Optional[list] = None
    msg: Optional[str]

@router.get("/api/v1/trend/{field}", response_model=TrendResponse, tags=["wide_table"])
async def get_search(field: str, scale: str, response: Response, token: Optional[str]=Header(None)):
    if token != settings.service_auth.token:
        response.status_code=401
        return TrendResponse(state=903, msg="Authentication Failed")
    try:
        if (field not in TRENDS) or (scale not in ["daily", "monthly"]):
            response.status_code=400
            return TrendResponse(status=900, msg="Input data not correct.")
        res = es.search_latest_by_query_string(index=f"squint_trend_{scale}_{field}", query_string="*", timestamp_field=TRENDS_SORT_ORDER_FIELD_NAME[scale], size=TRENDS_SIZE[scale])
        if len(res["hits"]["hits"]) > 0:
            return TrendResponse(state=800, meta={"scale": scale}, payload=[e["_source"] for e in res["hits"]["hits"]])
        else:
            return TrendResponse(state=800, meta={"scale": scale}, payload=[])
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error(e)
        response.status_code=500
        return TrendResponse(state=910, msg=str(e))

@router.get("/api/v1/state/{field}", response_model=StateResponse, tags=["wide_table"])
async def get_search(field: str, size: int, response: Response, token: Optional[str]=Header(None)):
    if token != settings.service_auth.token:
        response.status_code=401
        return StateResponse(state=903, msg="Authentication Failed")
    try:
        if (field not in STATES) or size <= 0 or size >= 1000:
            response.status_code=400
            return StateResponse(status=900, msg="Input data not correct.")
        if field in ["port", "protocol"]:
            count = es.count_by_query_string(index=settings.elasticsearch.index_prefix + "ip", query_string="*")
            terms_res = es.search_and_terms(index=settings.elasticsearch.index_prefix + "ip", query_string="*", terms_fields=[STATES_FIELDS[field]], terms_size=size)
        elif field in ["http_server", "https_server"]:
            count = es.count_by_query_string(index=settings.elasticsearch.index_prefix + "domain", query_string="*")
            terms_res = es.search_and_terms(index=settings.elasticsearch.index_prefix + "domain", query_string="*", terms_fields=[STATES_FIELDS[field]], terms_size=size)
        if len(terms_res) > 0:
            return StateResponse(state=800, meta={"total": count, "size": size}, payload=terms_res)
        else:
            return StateResponse(state=800, meta={"total": count, "size": size}, payload=[])
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error(e)
        response.status_code=500
        return StateResponse(state=910, msg=str(e))

#### wide_table search
class SearchInput(BaseModel):
    keyword: Optional[str] = "*"
    filters: Optional[str] = "*"

class SearchResponse(BaseModel):
    state: int
    meta: Optional[dict] = None
    payload: Optional[list] = None
    msg: Optional[str]

class SearchStatsResponse(BaseModel):
    state: int
    meta: Optional[dict] = None
    payload: Optional[dict] = None
    msg: Optional[str]

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
        if page <= 0 or page >= 1000 or rows <= 0 or rows >= 1000:
            response.status_code=400
            return SearchResponse(status=900, msg="Input data not correct.")
        res = es.search_by_query_string_with_from_size(index=settings.elasticsearch.index_prefix + field, query_string=query_string, from_num=page * rows, size=rows, source=IMPORTANT[field])
        if len(res["hits"]["hits"]) > 0:
            return SearchResponse(state=800, meta={"total": res["aggregations"]["count"]["value"]}, payload=[trim_important_result(e["_source"]) for e in res["hits"]["hits"]])
        else:
            return SearchResponse(state=800, meta={"total":0}, payload={})
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error(e)
        response.status_code=500
        return SearchResponse(state=910, msg=str(e))

@router.post("/api/v1/search/{field}/stats", response_model=SearchStatsResponse, tags=["wide_table"])
async def get_search_stats(field: str, input_data: SearchInput, response: Response, token: Optional[str]=Header(None)):
    if token != settings.service_auth.token:
        response.status_code=401
        return SearchStatsResponse(state=903, msg="Authentication Failed")
    try:
        if input_data.filters:
            query_string = input_data.filters
        elif input_data.keyword:
            query_string = input_data.keyword
        else:
            query_string = "*"
        # domain stats 
        stats_results = {}
        terms_res = es.search_and_terms(index=settings.elasticsearch.index_prefix + field, query_string=query_string, terms_fields=STATS[field], terms_size=10)
        for i, key in enumerate(STATS[field]):
            stats_results[key] = terms_res[i]
        if len(terms_res) > 0:
            return SearchStatsResponse(state=800, payload=stats_results)
        else:
            return SearchStatsResponse(state=800, payload={})
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error(e)
        response.status_code=500
        return SearchStatsResponse(state=910, msg=str(e))

##### wide_table detail
class DetailResponse(BaseModel):
    state: int
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
                cert_res = es.search_by_query_string_with_from_size(index=settings.elasticsearch.index_prefix + "cert", query_string=" OR ".join([f"cert:{cert}" for cert in res["hits"]["hits"][0]["_source"]["cert_hash"]]), from_num=0, size=10, source=IMPORTANT["cert"])
                res["hits"]["hits"][0]["_source"]["certs"] = [e["_source"] for e in cert_res["hits"]["hits"]]
            if type == "domain":
                # domain_cert
                if res['hits']['hits'][0]['_source']['cert_hash']:
                    cert_res = es.search_by_query_string_with_from_size(index=settings.elasticsearch.index_prefix + "cert", query_string=f"cert:{res['hits']['hits'][0]['_source']['cert_hash']}", from_num=0, size=10, source=IMPORTANT["cert"])
                    res["hits"]["hits"][0]["_source"]["cert"] = cert_res["hits"]["hits"][0]["_source"]
                # domain_subdomain
                subdomains_res = es.search_by_query_string_with_from_size(index=settings.elasticsearch.index_prefix + "domain", query_string=" OR ".join([f"domain:{domain}" for domain in res["hits"]["hits"][0]["_source"]["subdomains"]]), from_num=0, size=10, source=IMPORTANT["domain"])
                res["hits"]["hits"][0]["_source"]["subdomains"] = [trim_important_result(e["_source"]) for e in subdomains_res["hits"]["hits"]]
            if type == "organization":
                # organization_subdomain
                domains_res = es.search_by_query_string_with_from_size(index=settings.elasticsearch.index_prefix + "domain", query_string=" OR ".join([f"domain:{domain}" for domain in res["hits"]["hits"][0]["_source"]["domains"]]), from_num=0, size=10, source=IMPORTANT["domain"])
                res["hits"]["hits"][0]["_source"]["domains"] = [trim_important_result(e["_source"]) for e in domains_res["hits"]["hits"]]
            return DetailResponse(state=800, payload=res["hits"]["hits"][0]["_source"])
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