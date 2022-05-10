from utils.logger import logger
import time

from service.db.elasticsearch import es
from utils.config import settings

ORGANIZATION_WIDE_TABLE_NAME = "squint_organization"
ORGANIZATION_TYPE = ["organization_businessinfo", "organization_domain"]

def new_organization_wide_table_record():
    return {
        "name":"",
        "info":{},
        "domains":[],
        "create_timestamp":"",
        "update_timestamp":"",
        "tags":{}
    }

def delete_name_dict(dict, name):
    dict.pop(name)
    return dict

def organization_update(name, type):
    if type not in ORGANIZATION_TYPE:
        logger.error("ERROR: organization_update input arg type not in ORGANIZATION_TYPE(organization_businessinfo, organization_domain).")
    res = es.search_latest_by_query_string(ORGANIZATION_WIDE_TABLE_NAME, f"name:{name}", "update_timestamp")
    if len(res["hits"]["hits"]) == 0:
        update_data = new_organization_wide_table_record()
        if type == "organization_businessinfo":
            res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + type, f"name:{name}", "insert_raw_table_timestamp")
            if len(res["hits"]["hits"]) == 0:
                raise Exception(f"ERROR: organization_update cannot find record(type:{type}, name:{name})")
            update_data.update({
                    "name": res["hits"]["hits"][0]["_source"]["name"],
                    "info": delete_name_dict(res["hits"]["hits"][0]["_source"], "name"),
                    "create_timestamp": res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"],
                    "update_timestamp": res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"]
                })
        elif type == "organization_domain":
            res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + type, f"company:{name}", "insert_raw_table_timestamp")
            if len(res["hits"]["hits"]) == 0:
                raise Exception(f"ERROR: organization_update cannot find record(type:{type}, name:{name})") 
            update_data.update({
                    "name": res["hits"]["hits"][0]["_source"]["company"],
                    "domains": res["hits"]["hits"][0]["_source"]["domains"],
                    "create_timestamp": res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"],
                    "update_timestamp": res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"]
                })
        es.update()
    else:
        update_data = res["hits"]["hits"][0]["_source"]
        if type == "organization_businessinfo":
            res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + type, f"name:{name}", "insert_raw_table_timestamp")
            if len(res["hits"]["hits"]) == 0:
                raise Exception(f"ERROR: organization_update cannot find record(type:{type}, name:{name})")
            update_data.update({
                    "info": delete_name_dict(res["hits"]["hits"][0]["_source"], "name"),
                    "update_timestamp": time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
                })
        elif type == "organization_domain":
            res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + type, f"company:{name}", "insert_raw_table_timestamp")
            if len(res["hits"]["hits"]) == 0:
                raise Exception(f"ERROR: organization_update cannot find record(type:{type}, name:{name})") 
            update_data.update({
                    "domains": res["hits"]["hits"][0]["_source"]["domains"],
                    "update_timestamp": time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
                })