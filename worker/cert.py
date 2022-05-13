from utils.logger import logger
import time
from asn1crypto.x509 import Certificate 

from service.db.elasticsearch import es
from utils.config import settings
from utils.config import logger

CERT_WIDE_TABLE_NAME = "squint_cert"
CERT_TYPE = ["cert_raw"]
PARSER_VERSION = "1.0"

def assamble_cert_data(cert, raw):
    return {
        "parser_version": PARSER_VERSION,
        "parsed_timestamp": time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())),
        "raw": raw,
        # TODO: cert data fields...
    }

def cert_parse(sha256, type):
    if type not in CERT_TYPE:
        logger.error(f"ERROR: cert_parse input arg type not in CERT_TYPE({",".join(CERT_TYPE)}).")
    res = es.search_latest_by_query_string(CERT_WIDE_TABLE_NAME, f"sha256:{sha256}", "update_timestamp")
    if len(res["hits"]["hits"]) == 0:
        res = es.search_latest_by_query_string(settings.elasticsearch.index_prefix + type, f"sha256:{sha256}", "insert_raw_table_timestamp")
        if len(res["hits"]["hits"]) == 0:
            raise Exception(f"ERROR: cert_parse cannot find record(type:{type}, sha256:{sha256})")
        cert = Certificate.load(base64.b64decode(res["hits"]["hits"][0]["_source"]["raw"]))
        cert_data = assamble_cert_data(cert, res["hits"]["hits"][0]["_source"]["raw"])
        es.update(CERT_WIDE_TABLE_NAME, None, cert_data)
    else:
        logger.warning(f"Trying to parse existed cert, sha256: {sha256}")