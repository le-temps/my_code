# TODO1 ip_protocol 更新逻辑
# TODO2 ip_cert解析及 domain_reverse反查的插入

from utils.logger import logger
import time

from service.db.elasticsearch import es
from utils.config import settings

IP_WIDE_TABLE_NAME = "squint_ip"
IP_TYPE = ["ip_port", "ip_cert", "ip_ptr", "ip_protocol"]

def new_ip_wide_table_record():
    return {
        "ip":"",
        "dns":{},
        "domains":{},
        "ports":[],
        "protocols":{},
        "router":{},
        "router_cluster":{},
        "geo":{},
        "cert_hash":[],
        "create_timestamp":"",
        "update_timestamp":"",
        "tags":{}
    }

def delete_name_dict(dict, name):
    dict.pop(name)
    return dict

def ip_update(ip, type):
    if type not in IP_TYPE:
        logger.error("ERROR: ip_update input arg type not in IP_TYPE(ip_port, ip_cert, ip_ptr, ip_protocol).")
    res = es.search_latest_by_query_string(IP_WIDE_TABLE_NAME, f"ip:{ip}", "update_timestamp")
    if len(res["hits"]["hits"]) == 0:
        update_data = new_ip_wide_table_record()
        if type == "ip_port":
            res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + type, f"ip:{ip}", "insert_raw_table_timestamp")
            if len(res["hits"]["hits"]) == 0:
                raise Exception(f"ERROR: ip_update cannot find record(type:{type}, ip:{ip})")
            update_data.update({
                    "ip": res["hits"]["hits"][0]["_source"]["ip"],
                    "ports": res["hits"]["hits"][0]["_source"]["ports"],
                    "create_timestamp": res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"],
                    "update_timestamp": res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"]
                })
        elif type == "ip_cert":
            res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + type, f"ip:{ip}", "insert_raw_table_timestamp")
            if len(res["hits"]["hits"]) == 0:
                raise Exception(f"ERROR: ip_update cannot find record(type:{type}, ip:{ip})") 
            update_data.update({
                    "ip": res["hits"]["hits"][0]["_source"]["ip"],
                    "cert_hash": res["hits"]["hits"][0]["_source"]["sha256"],
                    "create_timestamp": res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"],
                    "update_timestamp": res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"]
                })
        elif type == "ip_ptr":
            res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + type, f"ip:{ip}", "insert_raw_table_timestamp")
            if len(res["hits"]["hits"]) == 0:
                raise Exception(f"ERROR: ip_update cannot find record(type:{type}, ip:{ip})") 
            update_data.update({
                    "ip": res["hits"]["hits"][0]["_source"]["ip"],
                    "domains": {"ptr":res["hits"]["hits"][0]["_source"]["ptr"]},
                    "create_timestamp": res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"],
                    "update_timestamp": res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"]
                })
        elif type == "ip_protocol":
            res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + type, f"ip:{ip}", "insert_raw_table_timestamp")
            if len(res["hits"]["hits"]) == 0:
                raise Exception(f"ERROR: ip_update cannot find record(type:{type}, ip:{ip})") 
            update_data.update({
                    "ip": res["hits"]["hits"][0]["_source"]["ip"],
                    "protocols": res["hits"]["hits"][0]["_source"]["protocols"],
                    "create_timestamp": res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"],
                    "update_timestamp": res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"]
                })
    else:
        update_data = res["hits"]["hits"][0]["_source"]
        if type == "ip_port":
            res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + type, f"ip:{ip}", "insert_raw_table_timestamp")
            if len(res["hits"]["hits"]) == 0:
                raise Exception(f"ERROR: ip_update cannot find record(type:{type}, ip:{ip})")
            update_data.update({
                    "ports": res["hits"]["hits"][0]["_source"]["ports"],
                    "update_timestamp": time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
                })
        elif type == "ip_cert":
            res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + type, f"ip:{ip}", "insert_raw_table_timestamp")
            if len(res["hits"]["hits"]) == 0:
                raise Exception(f"ERROR: ip_update cannot find record(type:{type}, ip:{ip})") 
            update_data.update({
                    "cert_hash": res["hits"]["hits"][0]["_source"]["sha256"],
                    "update_timestamp": time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
                })
        elif type == "ip_ptr":
            res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + type, f"ip:{ip}", "insert_raw_table_timestamp")
            if len(res["hits"]["hits"]) == 0:
                raise Exception(f"ERROR: ip_update cannot find record(type:{type}, ip:{ip})") 
            update_data.update({
                    "domains": {"ptr":res["hits"]["hits"][0]["_source"]["ptr"]},
                    "update_timestamp": time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
                })
        elif type == "ip_protocol":
            res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + type, f"ip:{ip}", "insert_raw_table_timestamp")
            if len(res["hits"]["hits"]) == 0:
                raise Exception(f"ERROR: ip_update cannot find record(type:{type}, ip:{ip})") 
            update_data.update({
                    "protocols": res["hits"]["hits"][0]["_source"]["protocols"],
                    "update_timestamp": time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
                })