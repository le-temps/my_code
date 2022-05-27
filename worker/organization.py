from utils.logger import logger

from service.db.elasticsearch import es
from utils.config import settings
from utils.time import get_current_time_string

ORGANIZATION_WIDE_TABLE_NAME = "squint_organization"

def new_organization_wide_table_record():
    return {
        "organization":"",
        "info":{},
        "domains":[],
        "create_timestamp":"",
        "update_timestamp":"",
        "tags":[]
    }

def delete_name_dict(dict, name):
    dict.pop(name)
    return dict

def assamble_organization_update_data(organization, insert_raw_table_timestamp, exist_record):
    if exist_record:
        return {"update_timestamp": get_current_time_string("time")}
    else:
        return {"organization":organization, "create_timestamp":insert_raw_table_timestamp, "update_timestamp":insert_raw_table_timestamp}

def update_organization_businessinfo(organization, exist_record, tags):
    res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "organization_businessinfo", f"name:{organization}", "insert_raw_table_timestamp")
    if len(res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: organization_update cannot find record(type:organization_businessinfo, name:{organization})")
    update_data = assamble_organization_update_data(organization, res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"], exist_record)
    if "create_date" in res["hits"]["hits"][0]["_source"] and res["hits"]["hits"][0]["_source"]["create_date"] == "":
        res["hits"]["hits"][0]["_source"]["create_date"] = None
    if "approval_date" in res["hits"]["hits"][0]["_source"] and res["hits"]["hits"][0]["_source"]["approval_date"] == "":
        res["hits"]["hits"][0]["_source"]["approval_date"] = None
    if not tags:
        tags = []
    if "business_status" in res["hits"]["hits"][0]["_source"] and res["hits"]["hits"][0]["_source"]["business_status"] not in ["", "存续", "开业", "正常", "在业"]:
        tags += ["business_abnormal"]
    update_data.update(
            {
                "info": delete_name_dict(res["hits"]["hits"][0]["_source"], "name"),
                "tags": tags
            }
        )
    return update_data

def update_organization_domain(organization, exist_record, tags):
    res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + "organization_domain", f"company:{organization}", "insert_raw_table_timestamp")
    if len(res["hits"]["hits"]) == 0:
        raise Exception(f"ERROR: organization_update cannot find record(type:organization_domain, name:{organization})")
    update_data = assamble_organization_update_data(organization, res["hits"]["hits"][0]["_source"]["insert_raw_table_timestamp"], exist_record)
    if not tags:
        tags = []
    update_data.update(
            {
                "domains": res["hits"]["hits"][0]["_source"]["domains"],
                "tags": tags
            }
        )
    return update_data

UPDATE_ORGANIZATION_FUNC = {
    "organization_businessinfo": update_organization_businessinfo,
    "organization_domain": update_organization_domain
}

def organization_update_data(name, type):
    if type not in UPDATE_ORGANIZATION_FUNC:
        logger.error(f"ERROR: organization_update input arg type not in ORGANIZATION_TYPE({','.join(UPDATE_ORGANIZATION_FUNC.keys())}).")
    res = es.search_latest_by_query_string(ORGANIZATION_WIDE_TABLE_NAME, f"organization:{name}", "update_timestamp")
    if len(res["hits"]["hits"]) == 0:
        update_data = new_organization_wide_table_record()
        update_data.update(UPDATE_ORGANIZATION_FUNC[type](name, False, None))
    else:
        update_data = res["hits"]["hits"][0]["_source"]
        update_data.update(UPDATE_ORGANIZATION_FUNC[type](name, True, update_data["tags"]))

    return update_data

def organization_update(name, type):
    update_data = organization_update_data(name, type)
    es.update(ORGANIZATION_WIDE_TABLE_NAME, name, update_data)