from utils.logger import logger

from service.db.elasticsearch import es
from utils.config import settings
from utils.time import get_current_time_string

DOMAIN_WIDE_TABLE_NAME = "squint_domain"
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
        "cert_hash":[],
        "create_timestamp":"",
        "update_timestamp":"",
        "tags":[]
    }

def delete_name_dict(dict, name):
    dict.pop(name)
    return dict

def assamble_domain_update_data(domain, insert_raw_table_timestamp, exist_record):
    if exist_record:
        return {"update_timestamp": get_current_time_string("time")}
    else:
        return {"domain":domain, "create_timestamp":insert_raw_table_timestamp, "update_timestamp":insert_raw_table_timestamp}

def update_domain_cert(domain, exist_record):
    res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "domain_cert", f"domain:{domain}", "insert_raw_table_timestamp")
    if len(res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: domain_update cannot find record(type:domain_cert, domain:{domain})")
    return assamble_domain_update_data(domain, res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"], exist_record).update(
            "cert_hash": res["hits"]["hits"][0]["_source"]["sha256"]
        )

def update_domain_icp(domain, exist_record):
    res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "domain_icp", f"domain:{domain}", "insert_raw_table_timestamp")
    if len(res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: domain_update cannot find record(type:domain_icp, domain:{domain})")
    return assamble_domain_update_data(domain, res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"], exist_record).update(
            "icp": delete_name_dict(res["hits"]["hits"][0]["_source"], "domain")
        )

def update_domain_psr(domain, exist_record):
    res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "domain_psr", f"domain:{domain}", "insert_raw_table_timestamp")
    if len(res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: domain_update cannot find record(type:domain_psr, domain:{domain})")
    return assamble_domain_update_data(domain, res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"], exist_record).update(
            "psr": delete_name_dict(res["hits"]["hits"][0]["_source"], "domain")
        )

def update_domain_rr(domain, exist_record):
    res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "domain_rr", f"domain:{domain}", "insert_raw_table_timestamp")
    if len(res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: domain_update cannot find record(type:domain_rr, domain:{domain})")
    for e in res["hits"]["hits"][0]["_source"]["A"]:
        delete_name_dict(e, "id")
    return assamble_domain_update_data(domain, res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"], exist_record).update(
            "rr": delete_name_dict(res["hits"]["hits"][0]["_source"], "domain")
        )

def update_domain_subdomain(domain, exist_record):
    res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "domain_subdomain", f"main_domain:{domain}", "insert_raw_table_timestamp")
    if len(res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: domain_update cannot find record(type:domain_subdomain, domain:{domain})")
    return assamble_domain_update_data(domain, res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"], exist_record).update(
            "subdomains": res["hits"]["hits"][0]["_source"]["subdomains"]
        )

def update_domain_whois(domain, exist_record):
    res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "domain_whois", f"domain:{domain}", "insert_raw_table_timestamp")
    if len(res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: domain_update cannot find record(type:domain_whois, domain:{domain})")
    return assamble_domain_update_data(domain, res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"], exist_record).update(
            "whois": delete_name_dict(res["hits"]["hits"][0]["_source"], "domain")
        )

def update_domain_web(domain, exist_record):
    res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "domain_web", f"domain:{domain}", "insert_raw_table_timestamp")
    if len(res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: domain_update cannot find record(type:domain_web, domain:{domain})")
    return assamble_domain_update_data(domain, res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"], exist_record).update(
            "web": delete_name_dict(res["hits"]["hits"][0]["_source"], "domain")
        )

def update_domain_snapshot(domain, exist_record):
    res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "domain_snapshot", f"request.domain:{domain}", "insert_raw_table_timestamp")
    if len(res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: domain_update cannot find record(type:domain_snapshot, domain:{domain})")
    remote_address_ip = res["hits"]["hits"][0]["response"]["remote_address"]["ip"]
    ip_geo_res = es.search_by_query_string(IP_GEO_TABLE_NAME, f"bip:<={remote_address_ip} AND eip:>={remote_address_ip}")
    res["hits"]["hits"][0]["_source"]["response"]["remote_address"].update(
            {
                "accuracy": ip_geo_res["hits"]["hits"][0]["_source"]["accuracy"],
                "areacode": ip_geo_res["hits"]["hits"][0]["_source"]["areacode"],
                "asnumber": ip_geo_res["hits"]["hits"][0]["_source"]["asnumber"],
                "continent": ip_geo_res["hits"]["hits"][0]["_source"]["continent"],
                "country": ip_geo_res["hits"]["hits"][0]["_source"]["country"],
                "isp": ip_geo_res["hits"]["hits"][0]["_source"]["isp"],
                "city": ip_geo_res["hits"]["hits"][0]["_source"]["multiAreas"]["city"],
                "district": ip_geo_res["hits"]["hits"][0]["_source"]["multiAreas"]["district"],
                "latbd": ip_geo_res["hits"]["hits"][0]["_source"]["multiAreas"]["latbd"],
                "latwgs": ip_geo_res["hits"]["hits"][0]["_source"]["multiAreas"]["latwgs"],
                "lngbd": ip_geo_res["hits"]["hits"][0]["_source"]["multiAreas"]["lngbd"],
                "lngwgs": ip_geo_res["hits"]["hits"][0]["_source"]["multiAreas"]["lngwgs"],
                "prov": ip_geo_res["hits"]["hits"][0]["_source"]["multiAreas"]["prov"],
                "radius": ip_geo_res["hits"]["hits"][0]["_source"]["multiAreas"]["radius"]
            }
        )
    return assamble_domain_update_data(domain, res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"], exist_record).update(
            "snapshot": delete_name_dict(res["hits"]["hits"][0]["_source"], "domain")
        )

UPDARE_DOMAIN_FUNC = {
    "domain_cert": update_domain_cert,
    "domain_icp": update_domain_icp,
    "domain_psr": update_domain_psr,
    "domain_rr": update_domain_rr,
    "domain_snapshot": update_domain_snapshot,
    "domain_subdomain": update_domain_subdomain,
    "domain_web": update_domain_web
    "domain_whois": update_domain_whois
}

def domain_update(domain, type):
    if type not in UPDARE_DOMAIN_FUNC:
        logger.error(f"ERROR: domain_update input arg type not in DOMAIN_TYPE({','.join(UPDARE_DOMAIN_FUNC.keys())}).")
    res = es.search_latest_by_query_string(DOMAIN_WIDE_TABLE_NAME, f"domain:{domain}", "update_timestamp")
    _id = None
    if len(res["hits"]["hits"]) == 0:
        update_data = new_domain_wide_table_record().update(UPDARE_DOMAIN_FUNC[type](domain, False))
    else:
        _id = res["hits"]["hits"][0]["_id"]
        update_data = res["hits"]["hits"][0]["_source"].update(UPDARE_DOMAIN_FUNC[type](domain, True))
        
    return update_data, _id

def domain_update(name, type):
    update_data, _id = domain_update_data(name, type)
    es.update(DOMAIN_WIDE_TABLE_NAME, _id, update_data)