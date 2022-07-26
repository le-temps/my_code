import time
import json
from ctypes import cdll, c_char_p

from service.db.elasticsearch import es
from utils.config import settings
from utils.logger import logger
from utils.time import get_current_time_string

CERT_WIDE_TABLE_NAME = "squint_cert"##表名
CERT_TYPE = ["cert_raw"]
PARSER_VERSION = "1.0"

def assamble_cert_data(raw, sha256):
    # TODO: LoadLibrary 初始化改进
    LIB_CERTIFICATE_PEM_TO_JSON = cdll.LoadLibrary("./worker/certificate_entry_and_pem_to_json_v3.so")#动态链接库
    parseRaw = LIB_CERTIFICATE_PEM_TO_JSON.parseRaw
    parseRaw.argtype = c_char_p
    parseRaw.restype = c_char_p

    cert_json = {
        "raw": raw,
        "cert": sha256,
        "parser_version": PARSER_VERSION,
        "parsed_timestamp": get_current_time_string("time"),
        "parse_status": 1,
        "tags": []
    }
    try:
        cert_json.update(json.loads(parseRaw(raw.encode("utf-8")).decode("utf-8")))
    except:
        cert_json.update({"parse_status": 0})
    return cert_json

def cert_parse(sha256, type):
    if type not in CERT_TYPE:
        logger.error(f"ERROR: cert_parse input arg type not in CERT_TYPE({','.join(CERT_TYPE)}).")
    res = es.search_latest_by_query_string(CERT_WIDE_TABLE_NAME, f"cert:{sha256}", "parsed_timestamp")
    if len(res["hits"]["hits"]) == 0:
        res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + type, f"sha256:{sha256}", "insert_raw_table_timestamp")
        if len(res["hits"]["hits"]) == 0:
            raise Exception(f"ERROR: cert_parse cannot find record(type:{type}, sha256:{sha256})")
        cert_data = assamble_cert_data(res["hits"]["hits"][0]["_source"]["raw"], sha256)
        es.update(CERT_WIDE_TABLE_NAME, sha256, cert_data)
    else:
        logger.warning(f"Trying to parse existed cert, sha256: {sha256}, ignore.")