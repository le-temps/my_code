import requests
import json

from utils.config import settings

def test_service_wide():
    headers = {"token": settings.service_auth.token}

    # 1. wide_table detail
    def wide_table_detail():
        res = requests.get("http://10.245.146.64:27000/api/v1/organization/厦门市元芝庄药业有限责任公司", headers=headers)
        print(res.text)
        res = requests.get("http://10.245.146.64:27000/api/v1/ip/27.152.73.250", headers=headers)
        print(res.text)
        res = requests.get("http://10.245.146.64:27000/api/v1/domain/jiuyepay.cn", headers=headers)
        print(res.text)

    # 2. wide_table search
    def wide_table_search():
        res = requests.post("http://10.245.146.64:27000/api/v1/search/organization?page=1&rows=10", headers=headers, data=json.dumps({"keyword": "*"}))
        print(res.text)
        res = requests.post("http://10.245.146.64:27000/api/v1/search/ip?page=1&rows=10", headers=headers, data=json.dumps({"keyword": "*"}))
        print(res.text)
        res = requests.post("http://10.245.146.64:27000/api/v1/search/domain?page=1&rows=10", headers=headers, data=json.dumps({"keyword": "*"}))
        print(res.text)

    wide_table_search()