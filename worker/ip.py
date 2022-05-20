from utils.logger import logger

from service.db.elasticsearch import es
from utils.config import settings
from utils.logger import logger
from utils.time import get_current_time_string, compare_time_string

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
        "tags":[]
    }

def delete_name_dict(dict, name):
    dict.pop(name)
    return dict

def assamble_ip_update_data(ip, insert_raw_table_timestamp, exist_record):
    if exist_record:
        return {"update_timestamp": get_current_time_string("time")}
    else:
        return {"ip":ip, "create_timestamp":insert_raw_table_timestamp, "update_timestamp":insert_raw_table_timestamp}

def update_ip_port(ip, exist_record):
    res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "ip_port", f"ip:{ip}", "insert_raw_table_timestamp")
    if len(res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: ip_update cannot find record(type:ip_port, ip:{ip})")
    update_data = assamble_ip_update_data(ip, res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"], exist_record)
    update_data.update(
            {"ports": res["hits"]["hits"][0]["_source"]["ports"]}
        )
    return update_data

def update_ip_cert(ip, exist_record):
    res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "ip_protocol", f"ip:{ip}", "insert_raw_table_timestamp")
    if len(res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: ip_update cannot find record(type:ip_cert, ip:{ip})")
    update_data = assamble_ip_update_data(ip, res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"], exist_record)
    cert_hash = []
    protocol_res = es.terms_and_top_hit(index=settings.elasticsearch.index_prefix + "ip_port", 
                                        query_string=f"ip:({' OR '.join(ports_res['hits']['hits'][0]['_source']['ports'])}) AND ip:{ip}",
                                        terms_size=65536,
                                        terms_field="port",
                                        top_hits_size=1,
                                        script_field="insert_raw_table_timestamp"
                                        )
    protocols = [delete_name_dict(e[0]["_source"], "ip") for e in protocol_res]
    for p in protocols:
        if "cert_hash" in p["data"] and p["data"]["cert_hash"] != "" and p["data"]["cert_hash"] is not None:
            cert_hash.append(p["data"]["cert_hash"])
    update_data.update(
            {"cert_hash": cert_hash}
        )
    return update_data

def update_ip_ptr(ip, exist_record):
    ptr = []
    reverse_domains = []
    timestamp = get_current_time_string("time")
    res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "ip_ptr", f"ip:{ip}", "insert_raw_table_timestamp")
    if len(res["hits"]["hits"]) != 0:
        ptr = res["hits"]["hits"][0]["_source"]["ptr"]
        timestamp = res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"]
    revers_domains_res = es.search_by_query_string(settings.elasticsearch.index_prefix + "domain_rr", f"A.ip:{ip}")
    if len(revers_domains_res["hits"]["hits"]) != 0:
        reverse_domains = [e["_source"]["domain"] for e in revers_domains_res["hits"]["hits"]]
        if compare_time_string(timestamp, revers_domains_res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"], "time"):
            timestamp = revers_domains_res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"]
    update_data = assamble_ip_update_data(ip, timestamp, exist_record)
    update_data.update(
            {
                "domains": {
                    "ptr": ptr,
                    "reverse_domains": reverse_domains
                }
            }
        )
    return update_data

def update_ip_protocol(ip, exist_record):
    ports_res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "ip_port", f"ip:{ip}", "insert_raw_table_timestamp")
    if len(ports_res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: ip_update cannot find record(type:ip_port, ip:{ip})")
    protocol_res = es.terms_and_top_hit(index=settings.elasticsearch.index_prefix + "ip_port", 
                                        query_string=f"ip:({' OR '.join(ports_res['hits']['hits'][0]['_source']['ports'])}) AND ip:{ip}",
                                        terms_size=65536,
                                        terms_field="port",
                                        top_hits_size=1,
                                        script_field="insert_raw_table_timestamp"
                                        )
    protocols = [delete_name_dict(e[0]["_source"], "ip") for e in protocol_res]
    update_data = assamble_ip_update_data(ip, protocol_res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"], exist_record)
    update_data.update(
            {"protocols": protocols}
        )
    return update_data

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
    if len(res["hits"]["hits"]) == 0:
        update_data = new_ip_wide_table_record()
        update_data.update(UPDARE_IP_FUNC[type](ip, False))
    else:
        update_data = res["hits"]["hits"][0]["_source"]
        update_data.update(UPDARE_IP_FUNC[type](ip, True))

    return update_data

def ip_update(ip, type):
    update_data = ip_update_data(ip, type)
    es.update(IP_WIDE_TABLE_NAME, ip, update_data)
    if type == "ip_protocol" and "cert_hash" in update_data["data"] and update_data["data"]["cert_hash"] is not None and update_data["data"]["cert_hash"] != "":
        return [{"source_index_type":"ip_cert", "destination_index_type":"ip", "value":ip, "try_num":0, "create_time":get_current_time_string("time")}]