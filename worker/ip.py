from service.db.elasticsearch import es
from utils.config import settings
from utils.logger import logger
from utils.time import get_current_time_string, compare_time_string
from utils.validator import valid_ip

IP_WIDE_TABLE_NAME = "squint_ip"
IP_CHINA_DNS_TABLE_NAME = "china_dns_info"
IP_GEO_TABLE_NAME = "ip_geo_street"

def new_ip_wide_table_record():
    return {
        "ip":"",
        "dns":{},
        "domains":{},
        "ports":[],
        "protocols":[],
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

def update_ip_port(ip, exist_record, tags):
    res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "ip_port", f"ip:{ip}", "insert_raw_table_timestamp")
    if len(res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: ip_update cannot find record(type:ip_port, ip:{ip})")
    update_data = assamble_ip_update_data(ip, res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"], exist_record)
    if not tags:
        tags = []
    update_data.update(
            {
                "ports": res["hits"]["hits"][0]["_source"]["ports"],
                "tags": tags
            }
        )
    return update_data

def update_ip_cert(ip, exist_record, tags):
    res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "ip", f"ip:{ip}", "update_timestamp")
    if len(res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: ip_update cannot find record(type:ip_cert, ip:{ip})")
    update_data = assamble_ip_update_data(ip, res["hits"]["hits"][0]["_source"]["update_timestamp"], exist_record)
    cert_hash = []
    for p in res["hits"]["hits"][0]["_source"]["protocols"]:
        if "cert_hash" in p["data"] and p["data"]["cert_hash"] != "" and p["data"]["cert_hash"] is not None:
            cert_hash.append(p["data"]["cert_hash"])
    if not tags:
        tags = []
    update_data.update(
            {
                "cert_hash": cert_hash,
                "tags": tags
            }
        )
    return update_data

def update_ip_ptr(ip, exist_record, tags):
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
    if not tags:
        tags = []
    update_data.update(
            {
                "domains": {
                    "ptr": ptr,
                    "reverse_domains": reverse_domains
                },
                "tags": tags
            }
        )
    return update_data

def update_ip_protocol(ip, exist_record, tags):
    ports_res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "ip_port", f"ip:{ip}", "insert_raw_table_timestamp")
    if len(ports_res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: ip_update cannot find record(type:ip_port, ip:{ip})")
    protocol_res = es.terms_and_top_hit(index=settings.elasticsearch.index_prefix + "ip_protocol", 
                                        query_string=f"port:({' OR '.join([str(p) for p in ports_res['hits']['hits'][0]['_source']['ports']])}) AND ip:{ip}",
                                        terms_size=65536,
                                        terms_field="port",
                                        top_hits_size=1,
                                        script_field="insert_raw_table_timestamp"
                                        )
    protocols = [delete_name_dict(e[0]["_source"], "ip") for e in protocol_res]
    update_data = assamble_ip_update_data(ip, ports_res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"], exist_record)
    if not tags:
        tags = []
    update_data.update(
            {
                "protocols": protocols,
                "tags": tags
            }
        )
    return update_data

def update_ip_dns(ip, exist_record, tags):
    res = es.search_latest_by_query_string(IP_CHINA_DNS_TABLE_NAME, f"ip:{ip} AND parsed_date:{get_current_time_string('date', '%Y%m%d')}", "parsed_date")
    dns_type = []
    dns_version = ""
    if res["hits"]["hits"]:
        for dns in ["open", "hidden", "forward", "morbid", "recursive", "edns", "dnssec"]:
            if res["hits"]["hits"][0]["_source"][dns] == "1":
                if f"{dns}_dns" not in tags:
                    tags += [f"{dns}_dns"]
                dns_type += [dns]
        if "version" in res["hits"]["hits"][0]["_source"]:
            dns_version = res["hits"]["hits"][0]["_source"]["version"].split("|")[0]
    update_data = assamble_ip_update_data(ip, get_current_time_string("time"), exist_record)
    if not tags:
        tags = []
    if dns_type:
        update_data.update(
                {
                    "dns": {"type": dns_type, "version": dns_version},
                    "tags": tags
                }
            )
    else:
        tags = tags + [e for e in tags if "dns" not in e]
        update_data.update(
                {
                    "dns": {},
                    "tags": tags
                }
            )
    return update_data

def update_ip_geo(ip, exist_record, tags):
    ip_geo_res = es.search_by_query_string(IP_GEO_TABLE_NAME, f"bip:<={ip} AND eip:>={ip}")
    if len(ip_geo_res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: ip_update cannot find record(type:ip_geo, ip:{ip})")
    update_data = assamble_ip_update_data(ip, get_current_time_string("time"), exist_record)
    if not tags:
        tags = []
    update_data.update(
            {
                "geo": {
                    "accuracy": ip_geo_res["hits"]["hits"][0]["_source"]["accuracy"],
                    "areacode": ip_geo_res["hits"]["hits"][0]["_source"]["areacode"],
                    "asnumber": ip_geo_res["hits"]["hits"][0]["_source"]["asnumber"],
                    "continent": ip_geo_res["hits"]["hits"][0]["_source"]["continent"],
                    "country": ip_geo_res["hits"]["hits"][0]["_source"]["country"],
                    "isp": ip_geo_res["hits"]["hits"][0]["_source"]["isp"],
                    "city": ip_geo_res["hits"]["hits"][0]["_source"]["multiAreas"][0]["city"],
                    "district": ip_geo_res["hits"]["hits"][0]["_source"]["multiAreas"][0]["district"],
                    "latbd": ip_geo_res["hits"]["hits"][0]["_source"]["multiAreas"][0]["latbd"],
                    "latwgs": ip_geo_res["hits"]["hits"][0]["_source"]["multiAreas"][0]["latwgs"],
                    "lngbd": ip_geo_res["hits"]["hits"][0]["_source"]["multiAreas"][0]["lngbd"],
                    "lngwgs": ip_geo_res["hits"]["hits"][0]["_source"]["multiAreas"][0]["lngwgs"],
                    "prov": ip_geo_res["hits"]["hits"][0]["_source"]["multiAreas"][0]["prov"],
                    "radius": ip_geo_res["hits"]["hits"][0]["_source"]["multiAreas"][0]["radius"]
                },
                "tags": tags
            }
        )
    return update_data

UPDATE_IP_FUNC = {
    "ip_port": update_ip_port,
    "ip_cert": update_ip_cert,
    "ip_ptr": update_ip_ptr,
    "ip_protocol": update_ip_protocol,
    "ip_dns": update_ip_dns,
    "ip_geo": update_ip_geo
}

def ip_update_data(ip, type):
    if not valid_ip(ip):
        raise Exception(f"Invalid IP: {ip}!")
    if type not in UPDATE_IP_FUNC:
        logger.error(f"ERROR: ip_update input arg type not in IP_TYPE({','.join(UPDATE_IP_FUNC.keys())}).")
    res = es.search_latest_by_query_string(IP_WIDE_TABLE_NAME, f"ip:{ip}", "update_timestamp")
    if len(res["hits"]["hits"]) == 0:
        update_data = new_ip_wide_table_record()
        update_data.update(UPDATE_IP_FUNC["ip_geo"](ip, False, None))
        update_data.update(UPDATE_IP_FUNC[type](ip, False, None))
    else:
        update_data = res["hits"]["hits"][0]["_source"]
        update_data.update(UPDATE_IP_FUNC[type](ip, True, update_data["tags"]))

    return update_data

def ip_update(ip, type):
    update_data = ip_update_data(ip, type)
    es.update(IP_WIDE_TABLE_NAME, ip, update_data)
    if type == "ip_protocol":
        for protocol in update_data["protocols"]:
            if "cert_hash" in protocol["data"] and protocol["data"]["cert_hash"] is not None and protocol["data"]["cert_hash"] != "":
                return [{"source_index_type":"ip_cert", "destination_index_type":"ip", "value":ip, "try_num":0, "create_time":get_current_time_string("time")}]