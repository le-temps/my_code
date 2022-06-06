from utils.logger import logger

from service.db.elasticsearch import es
from utils.config import settings
from utils.time import get_current_time_string
from utils.processor import replace_value_by_value

DOMAIN_WIDE_TABLE_NAME = "squint_domain"
CERT_WIDE_TABLE_NAME = "squint_cert"
IP_GEO_TABLE_NAME = "ip_geo_street"

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
        "cert_hash":None,
        "create_timestamp":"",
        "update_timestamp":"",
        "tags":[]
    }

def delete_dict_fields(dict, names):
    for name in names:
        dict.pop(name)
    return dict

def assamble_domain_update_data(domain, insert_raw_table_timestamp, exist_record):
    if exist_record:
        return {"update_timestamp": get_current_time_string("time")}
    else:
        return {"domain":domain, "create_timestamp":insert_raw_table_timestamp, "update_timestamp":insert_raw_table_timestamp}

def update_domain_cert(domain, exist_record, tags):
    res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "domain_web", f"domain:\"{domain}\"", "insert_raw_table_timestamp")
    if len(res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: domain_update cannot find record(type:domain_cert, domain:{domain})")
    update_data = assamble_domain_update_data(domain, res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"], exist_record)
    cert_hash = None
    if "cert_hash" in res["hits"]["hits"][0]["_source"]["https"][-1]:
        cert_hash = res["hits"]["hits"][0]["_source"]["https"][0]["cert_hash"]
    if not tags:
        tags = []
    update_data.update(
            {
                "cert_hash": replace_value_by_value(cert_hash, "", None),
                "tags": tags
            }
        )
    return update_data

def update_domain_icp(domain, exist_record, tags):
    res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "domain_icp", f"domain:\"{domain}\"", "insert_raw_table_timestamp")
    if len(res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: domain_update cannot find record(type:domain_icp, domain:{domain})")
    update_data = assamble_domain_update_data(domain, res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"], exist_record)
    if not tags:
        tags = []
    tags += ["icp"]
    update_data.update(
            {
                "icp": replace_value_by_value(delete_dict_fields(res["hits"]["hits"][0]["_source"], ["domain", "insert_raw_table_timestamp"]), "", None),
                "tags": tags
            }
        )
    return update_data

def update_domain_psr(domain, exist_record, tags):
    res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "domain_psr", f"domain:\"{domain}\"", "insert_raw_table_timestamp")
    if len(res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: domain_update cannot find record(type:domain_psr, domain:{domain})")
    update_data = assamble_domain_update_data(domain, res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"], exist_record)
    if not tags:
        tags = []
    tags += ["psr"]
    update_data.update(
            {
                "psr": replace_value_by_value(delete_dict_fields(res["hits"]["hits"][0]["_source"], ["domain", "insert_raw_table_timestamp"]), "", None),
                "tags": tags
            }
        )
    return update_data

def update_domain_rr(domain, exist_record, tags):
    res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "domain_rr", f"domain:\"{domain}\"", "insert_raw_table_timestamp")
    if len(res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: domain_update cannot find record(type:domain_rr, domain:{domain})")
    for e in res["hits"]["hits"][0]["_source"]["A"]:
        delete_dict_fields(e, ["id"])
    update_data = assamble_domain_update_data(domain, res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"], exist_record)
    if not tags:
        tags = []
    update_data.update(
            {
                "rr": replace_value_by_value(delete_dict_fields(res["hits"]["hits"][0]["_source"], ["domain", "insert_raw_table_timestamp"]), "", None),
                "tags": tags
            }
        )
    return update_data

def update_domain_subdomain(domain, exist_record, tags):
    res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "domain_subdomain", f"main_domain:\"{domain}\"", "insert_raw_table_timestamp")
    if len(res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: domain_update cannot find record(type:domain_subdomain, domain:{domain})")
    update_data = assamble_domain_update_data(domain, res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"], exist_record)
    if not tags:
        tags = []
    update_data.update(
            {
                "subdomains": replace_value_by_value(res["hits"]["hits"][0]["_source"]["subdomains"], "", None),
                "tags": tags
            }
        )
    return update_data

def update_domain_whois(domain, exist_record, tags):
    res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "domain_whois", f"domain:\"{domain}\"", "insert_raw_table_timestamp")
    if len(res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: domain_update cannot find record(type:domain_whois, domain:{domain})")
    update_data = assamble_domain_update_data(domain, res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"], exist_record)
    if not tags:
        tags = []
    update_data.update(
            {
                "whois": replace_value_by_value(delete_dict_fields(res["hits"]["hits"][0]["_source"], ["domain", "insert_raw_table_timestamp"]), "", None),
                "tags": tags
            }
        )
    return update_data

def update_domain_web(domain, exist_record, tags):
    res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "domain_web", f"domain:\"{domain}\"", "insert_raw_table_timestamp")
    if len(res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: domain_update cannot find record(type:domain_web, domain:{domain})")
    update_data = assamble_domain_update_data(domain, res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"], exist_record)
    if not tags:
        tags = []
    if res["hits"]["hits"][0]["_source"]["http"]:
        tags += ["http"]
    if res["hits"]["hits"][0]["_source"]["https"]:
        tags += ["https"]
    if 200 in ([e["status_code"] for e in res["hits"]["hits"][0]["_source"]["http"]] + [e["status_code"] for e in res["hits"]["hits"][0]["_source"]["https"]]):
        tags += ["access_successful"]
    else:
        tags += ["access_failed"]
    update_data.update(
            {
                "web": replace_value_by_value(delete_dict_fields(res["hits"]["hits"][0]["_source"], ["domain", "insert_raw_table_timestamp"]), "", None),
                "tags": tags
            }
        )
    return update_data

def update_domain_snapshot(domain, exist_record, tags):
    res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "domain_snapshot", f"request.domain:\"{domain}\"", "insert_raw_table_timestamp")
    if len(res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: domain_update cannot find record(type:domain_snapshot, domain:{domain})")
    remote_address_ip = res["hits"]["hits"][0]["_source"]["response"]["remote_address"]["ip"]
    if remote_address_ip is not None and remote_address_ip != "":
        ip_geo_res = es.search_by_query_string(IP_GEO_TABLE_NAME, f"bip:<={remote_address_ip} AND eip:>={remote_address_ip}")
        res["hits"]["hits"][0]["_source"]["response"]["remote_address"].update(
            {
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
            }
        )
    update_data = assamble_domain_update_data(domain, res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"], exist_record)
    if not tags:
        tags = []
    if remote_address_ip is not None and remote_address_ip != "" and res["hits"]["hits"][0]["_source"]["response"]["remote_address"]["country"] == "中国" and res["hits"]["hits"][0]["_source"]["response"]["remote_address"]["prov"] not in ["中国香港", "中国台湾", "澳门特别行政区"]:
        tags += ["in_mainland"]
    else:
        tags += ["not_in_mainland"]
    if res["hits"]["hits"][0]["_source"]["classification"]["type"] in ["赌博", "色情"]:
        tags += ["illegal"]
    else:
        tags += ["legal"]
    update_data.update(
            {
                "snapshot": replace_value_by_value(delete_dict_fields(res["hits"]["hits"][0]["_source"], ["insert_raw_table_timestamp"]), "", None),
                "tags": tags
            }
        )
    return update_data

UPDARE_DOMAIN_FUNC = {
    "domain_cert": update_domain_cert,
    "domain_icp": update_domain_icp,
    "domain_psr": update_domain_psr,
    "domain_rr": update_domain_rr,
    "domain_snapshot": update_domain_snapshot,
    "domain_subdomain": update_domain_subdomain,
    "domain_web": update_domain_web,
    "domain_whois": update_domain_whois
}

def domain_update_data(domain, type):
    if type not in UPDARE_DOMAIN_FUNC:
        logger.error(f"ERROR: domain_update input arg type not in DOMAIN_TYPE({','.join(UPDARE_DOMAIN_FUNC.keys())}).")
    res = es.search_latest_by_query_string(DOMAIN_WIDE_TABLE_NAME, f"domain.keyword:\"{domain}\"", "update_timestamp")
    if len(res["hits"]["hits"]) == 0:
        update_data = new_domain_wide_table_record()
        update_data.update(UPDARE_DOMAIN_FUNC[type](domain, False, None))
    else:
        update_data = res["hits"]["hits"][0]["_source"]
        update_data.update(UPDARE_DOMAIN_FUNC[type](domain, True, update_data["tags"]))
        
    return update_data

def domain_update(domain, type):
    update_data = domain_update_data(domain, type)
    es.update(DOMAIN_WIDE_TABLE_NAME, domain, update_data)
    if type == "domain_web" and len(update_data["web"]["https"]) > 1:
        return [{"source_index_type":"domain_cert", "destination_index_type":"domain", "value":domain, "try_num":0, "create_time":get_current_time_string("time")}]
    elif type == "domain_rr":
        return [{"source_index_type":"ip_ptr", "destination_index_type":"ip", "value":a["ip"], "try_num":0, "create_time":get_current_time_string("time")} for a in update_data["rr"]["A"]]