from utils.logger import logger
import time

from service.db.elasticsearch import es
from utils.config import settings

IP_WIDE_TABLE_NAME = "squint_ip"

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

def assamble_ip_update_data(ip, insert_raw_table_timestamp, exist_record):
    if exist_record:
        return {"update_timestamp": time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))}
    else:
        return {"ip":ip, "create_timestamp":insert_raw_table_timestamp, "update_timestamp":insert_raw_table_timestamp}

def update_ip_port(ip, exist_record):
    res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "ip_port", f"ip:{ip}", "insert_raw_table_timestamp")
    if len(res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: ip_update cannot find record(type:ip_port, ip:{ip})")
    return assamble_ip_update_data(ip, res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"], exist_record).update(
            "ports": res["hits"]["hits"][0]["_source"]["ports"]
        )

def update_ip_cert(ip, exist_record):
    res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "ip_cert", f"ip:{ip}", "insert_raw_table_timestamp")
    if len(res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: ip_update cannot find record(type:ip_cert, ip:{ip})")
    return assamble_ip_update_data(ip, res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"], exist_record).update(
            "cert_hash": res["hits"]["hits"][0]["_source"]["sha256"]
        )

def update_ip_ptr(ip, exist_record):
    res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "ip_ptr", f"ip:{ip}", "insert_raw_table_timestamp")
    if len(res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: ip_update cannot find record(type:ip_ptr, ip:{ip})")
    revers_domains_res = es.search_by_query_string(settings.elasticsearch.index_prefix + "domain_rr", f"A.ip:{ip}")
    return assamble_ip_update_data(ip, res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"], exist_record).update(
            "domains": {
                "ptr": res["hits"]["hits"][0]["_source"]["ptr"],
                "reverse_domains": [e["domain"] for e in revers_domains_res["hits"]["hits"]]
            }
        )

def update_ip_protocol(ip, exist_record):
    res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "ip_protocol", f"ip:{ip}", "insert_raw_table_timestamp")
    if len(res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: ip_update cannot find record(type:ip_protocol, ip:{ip})")
    protocol_res = es.terms_and_top_hit(index=settings.elasticsearch.index_prefix + "ip_port", 
                                        query_string=f"ip:({' OR '.join(ports_res['hits']['hits'][0]['_source']['ports'])}) AND ip:{ip}",
                                        terms_size=65536,
                                        terms_field="port",
                                        top_hits_size=1,
                                        script_field="insert_raw_table_timestamp"
                                        )
    protocols = [delete_name_dict(e[0]["_source"], "ip") for e in protocol_res]
    return assamble_ip_update_data(ip, res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"], exist_record).update(
            "protocols": protocols
        )

UPDARE_IP_FUNC = {
    "ip_port": update_ip_port,
    "ip_cert": update_ip_cert,
    "ip_ptr": update_ip_ptr,
    "ip_protocol": update_ip_protocol
}

def ip_update_data(ip, type):
    if type not in UPDARE_IP_FUNC:
        logger.error(f"ERROR: ip_update input arg type not in IP_TYPE({','.join(UPDARE_IP_FUNC.keys())}).")
    res = es.search_latest_by_query_string(IP_WIDE_TABLE_NAME, f"ip:{ip}", "update_timestamp")
    _id = None
    if len(res["hits"]["hits"]) == 0:
        update_data = new_ip_wide_table_record().update(UPDARE_IP_FUNC[type](ip, False))
    else:
        _id = res["hits"]["hits"][0]["_id"]
        update_data = res["hits"]["hits"][0]["_source"].update(UPDARE_IP_FUNC[type](ip, True))

    return update_data, _id 

def ip_update(name, type):
    update_data, _id = ip_update_data(name, type)
    es.update(IP_WIDE_TABLE_NAME, _id, update_data)