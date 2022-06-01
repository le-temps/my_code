from elasticsearch import Elasticsearch, helpers
from elasticsearch.helpers import bulk, scan, reindex
import traceback

from utils.config import settings
from utils.logger import logger

class ElasticsearchConn:

    def __init__(self, url, auth):
        self.es = Elasticsearch([url], http_auth=auth)

    def get_instance(self):
        return self.es

    def search(self, index, body):
        try:
            res = self.es.search(index=index, body=body)
            return res
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(e)
            raise
            return []

    def search_by_query_string(self, index, query_string):
        return self.search(index=index, body={"size":1, "query":{"query_string":{"query":query_string}}})

    def search_by_query_string_with_from_size(self, index, query_string, from_num, size, source=None):
        if source:
            return self.search(index=index, body={"from":from_num, "size":size, "_source":source, "query":{"query_string":{"query":query_string}}, "aggs":{"count":{"value_count":{"field":"_id"}}}})
        else:
            return self.search(index=index, body={"from":from_num, "size":size, "query":{"query_string":{"query":query_string}}, "aggs":{"count":{"value_count":{"field":"_id"}}}})

    def search_latest_by_query_string(self, index, query_string, timestamp_field):
        return self.search(index=index, body={"size":1, "query":{"query_string":{"query":query_string}}, "sort":{timestamp_field:{"order":"desc"}}})

    def count_by_query_string(self, index, query_string):
        return self.es.count(index=index, body={"query":{"query_string":{"query":query_string}}})["count"]

    def insert(self, index, id, insert_body):
        try:
            self.es.index(index=index, id=id, body=insert_body)
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
            self.es.update(index=index, doc_type='_doc', id=id, body={"doc":update_body, "doc_as_upsert":True})
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

    def search_and_terms(self, index, query_string, terms_fields, terms_size):
        query_body = {
            "size": 0,
            "query": {
                "query_string": {
                    "query": query_string
                }
            },
            "aggs": {}
        }
        for i, field in enumerate(terms_fields):
            query_body["aggs"][str(i)] = {"terms":{"field":field, "size":terms_size, "order":{"_count":"desc"}}}
        try:
            res = self.search(index, query_body)
            return [res["aggregations"][key]["buckets"] for key in res["aggregations"]]
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(e)
            raise

    def scan_by_query_string(self, index, query_string):
        return scan(client=self.es, index=index, query={"query":{"query_string":{"query":query_string}}})

    def create_index(self, index, body):
        self.es.indices.create(index=index, body=body)

    def reindex(self, source_index, target_index):
        reindex(client=self.es, source_index=source_index, target_index=target_index, target_client=self.es)

    def stats_by_query_string(self, index, query_string, fields, buckets):
        pass

es = ElasticsearchConn(f"{settings.elasticsearch_auth.host}:{settings.elasticsearch_auth.port}", (f"{settings.elasticsearch_auth.user}", f"{settings.elasticsearch_auth.password}"))