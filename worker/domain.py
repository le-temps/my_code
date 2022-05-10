from utils.logger import logger
import time

from service.db.elasticsearch import es
from utils.config import settings

DOMAIN_WIDE_TABLE_NAME = "squint_domain"
DOMAIN_TYPE = ["domain_cert", "domain_icp", "domain_psr", "domain_rr", "domain_snapshot", "domain_subdomain", "domain_web"]

def new_domain_wide_table_record():
    return {
        "domain":"",
        "icp":{},
        "psr":{},
        "rr":{},
        "subdomains":[],
        "web":{},
        "snapshot":{},
        "whois":{},
        "cert_hash":[],
        "create_timestamp":"",
        "update_timestamp":"",
        "tags":{}
    }

def domain_update(domain, type):
    if type not in DOMAIN_TYPE:
        logger.error("ERROR: domain_update input arg type not in DOMAIN_TYPE(domain_cert, domain_icp, domain_psr, domain_rr, domain_snapshot, domain_subdomain, domain_web).")
    res = es.search_latest_by_query_string(DOMAIN_WIDE_TABLE_NAME, f"domain:{domain}", "update_timestamp")
    if len(res["hits"]["hits"]) == 0:
        update_data = new_domain_wide_table_record()
        if type == "domain_cert":
            res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + type, f"domain:{domain}", "insert_raw_table_timestamp")
            if len(res["hits"]["hits"]) == 0:
                raise Exception(f"ERROR: domain_update cannot find record(type:{type}, domain:{domain})")
            update_data.update({
                    "domain": res["hits"]["hits"][0]["_source"]["domain"],
                    "cert_hash": res["hits"]["hits"][0]["_source"]["sha256"],
                    "create_timestamp": res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"],
                    "update_timestamp": res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"]
                })
        elif type == "domain_icp":
            res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + type, f"domain:{domain}", "insert_raw_table_timestamp")
            if len(res["hits"]["hits"]) == 0:
                raise Exception(f"ERROR: domain_update cannot find record(type:{type}, domain:{domain})") 
            update_data.update({
                    "domain": res["hits"]["hits"][0]["_source"]["domain"],
                    "icp": res["hits"]["hits"][0]["_source"],
                    "create_timestamp": res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"],
                    "update_timestamp": res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"]
                })
        elif type == "domain_psr":
            res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + type, f"domain:{domain}", "insert_raw_table_timestamp")
            if len(res["hits"]["hits"]) == 0:
                raise Exception(f"ERROR: domain_update cannot find record(type:{type}, domain:{domain})") 
            update_data.update({
                    "domain": res["hits"]["hits"][0]["_source"]["domain"],
                    "psr": res["hits"]["hits"][0]["_source"],
                    "create_timestamp": res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"],
                    "update_timestamp": res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"]
                })
        elif type == "domain_protocol":
            res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + type, f"domain:{domain}", "insert_raw_table_timestamp")
            if len(res["hits"]["hits"]) == 0:
                raise Exception(f"ERROR: domain_update cannot find record(type:{type}, domain:{domain})") 
            update_data.update({
                    "domain": res["hits"]["hits"][0]["_source"]["domain"],
                    "protocols": res["hits"]["hits"][0]["_source"]["protocols"],
                    "create_timestamp": res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"],
                    "update_timestamp": res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"]
                })
    else:
        update_data = res["hits"]["hits"][0]["_source"]
        if type == "domain_port":
            res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + type, f"domain:{domain}", "insert_raw_table_timestamp")
            if len(res["hits"]["hits"]) == 0:
                raise Exception(f"ERROR: domain_update cannot find record(type:{type}, domain:{domain})")
            update_data.update({
                    "ports": res["hits"]["hits"][0]["_source"]["ports"],
                    "update_timestamp": time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
                })
        elif type == "domain_cert":
            res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + type, f"domain:{domain}", "insert_raw_table_timestamp")
            if len(res["hits"]["hits"]) == 0:
                raise Exception(f"ERROR: domain_update cannot find record(type:{type}, domain:{domain})") 
            update_data.update({
                    "cert_hash": [res["hits"]["hits"][0]["_source"]["sha256"]],
                    "update_timestamp": time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
                })
        elif type == "domain_ptr":
            res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + type, f"domain:{domain}", "insert_raw_table_timestamp")
            if len(res["hits"]["hits"]) == 0:
                raise Exception(f"ERROR: domain_update cannot find record(type:{type}, domain:{domain})") 
            update_data.update({
                    "domains": {"ptr":res["hits"]["hits"][0]["_source"]["ptr"]},
                    "update_timestamp": time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
                })
        elif type == "domain_protocol":
            res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + type, f"domain:{domain}", "insert_raw_table_timestamp")
            if len(res["hits"]["hits"]) == 0:
                raise Exception(f"ERROR: domain_update cannot find record(type:{type}, domain:{domain})") 
            update_data.update({
                    "protocols": res["hits"]["hits"][0]["_source"]["protocols"],
                    "update_timestamp": time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
                })