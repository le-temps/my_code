from elasticsearch import Elasticsearch, helpers
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
            helpers.bulk(self.es, actions)
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

es = ElasticsearchConn(f"{settings.elasticsearch.host}:{settings.elasticsearch.port}", (f"{settings.elasticsearch_auth.user}", f"{settings.elasticsearch_auth.password}"))