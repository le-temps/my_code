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

#### main_page
class TrendResponse(BaseModel):
    state: int
    meta: Optional[dict] = None
    payload: Optional[dict] = None
    msg: Optional[str]

#@router.post("/api/v1/trend/{field}", response_model=SearchResponse, tags=["wide_table"])
#async def get_search(field: str, page: int, rows: int, input_data: SearchInput, response: Response, token: Optional[str]=Header(None)):
#    if token != settings.service_auth.token:
#        response.status_code=401
#        return SearchResponse(state=903, msg="Authentication Failed")
#    try:
#        if input_data.filters:
#            query_string = input_data.filters
#        elif input_data.keyword:
#            query_string = input_data.keyword
#        else:
#            query_string = "*"
#        if page <= 0 or page >= 1000 or rows <= 0 or rows >= 1000:
#            response.status_code=400
#            return SearchResponse(status=900, msg="Input data not correct.")
#        res = es.search_by_query_string_with_from_size(index=settings.elasticsearch.index_prefix + field, query_string=query_string, from_num=page * rows, size=rows, source=IMPORTANT[field])
#        if len(res["hits"]["hits"]) > 0:
#            return SearchResponse(state=800, meta={"total": res["aggregations"]["count"]["value"]}, payload=[trim_important_result(remove_object_field(e["_source"], "insert_raw_table_timestamp")) for e in res["hits"]["hits"]])
#        else:
#            return SearchResponse(state=800, meta={"total":0}, payload={})
#    except Exception as e:
#        logger.error(traceback.format_exc())
#        logger.error(e)
#        response.status_code=500
#        return SearchResponse(state=910, msg=str(e))



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
            return SearchResponse(state=800, meta={"total": res["aggregations"]["count"]["value"]}, payload=[trim_important_result(remove_object_field(e["_source"], "insert_raw_table_timestamp")) for e in res["hits"]["hits"]])
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