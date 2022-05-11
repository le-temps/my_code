from elasticsearch import Elasticsearch, helpers
from elasticsearch.helpers import bulk, scan
import traceback

from utils.config import settings
from utils.logger import logger

class ElasticsearchConn:

    def __init__(self, url, auth):
        self.es = Elasticsearch([url], http_auth=auth)

    def search(self, index, query_body):
        try:
            res = self.es.search(index=index, body=query_body)
            return res
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(e)
            raise
            return []

    def search_by_query_string(self, index, query_string):
        return self.search(index=index, body={"size":1, "query":{"query_string":{"query":query_string}}})

    def search_latest_by_query_string(self, index, query_string, timestamp_field):
        return self.search(index=index, body={"size":1, "query":{"query_string":{"query":query_string}}, "sort":{timestamp_field:{"order":"desc"}}})

    def insert(self, index, insert_body):
        try:
            es.index(index=index, body=insert_body)
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(e)
            raise

    def bulk_insert(self, index, data_list, additional_field_dict=None):
        try:
            if additional_field_dict is not None:
                for data in data_list:
                    data.update(additional_field_dict)
            actions = [{"_op_type": "index", "_index":index, "_source":data} for data in data_list]
            bulk(self.es, actions)
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(e)
            raise

    def update(self, index, id, update_body):
        try:
            es.update(index=index, doc_type='_doc', id=id, body=update_body)
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(e)
            raise

    def terms_and_top_hit(self, index, query_string, terms_size, terms_field, top_hits_size, script_field):
        query_body = {
            "size": 0,
            "query": {
                "query_string": {
                    "query": query_string
                }
            },
            "aggs": {
                "terms_aggs": {
                    "terms": {
                        "size": terms_size,
                        "order": {
                            "top_hit": "desc"
                        },
                        "field": terms_field
                    },
                    "aggs": {
                        "top_hits_aggs": {
                            "top_hits": {
                                "size": top_hits_size
                            }
                        },
                        "top_hit": {
                            "max": {
                                "script": {
                                    "source": f"doc['{script_field}']"
                                }
                            }
                        }
                    }
                }
            }
        }
        try:
            res = self.search(index, query_body)
            return [e["top_hits_aggs"]["hits"]["hits"] for e in res["aggregations"]["terms_aggs"]["buckets"]]
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(e)
            raise

    def scan_by_query_string(self, index, query_string):
        return scan(client=self.es, index=index, body={"size":1, "query":{"query_string":{"query":query_string}}})

es = ElasticsearchConn(f"{settings.elasticsearch.host}:{settings.elasticsearch.port}", (f"{settings.elasticsearch_auth.user}", f"{settings.elasticsearch_auth.password}"))