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
        #res = requests.post("http://10.245.146.64:27000/api/v1/search/organization?page=1&rows=10", headers=headers, json={"keyword": "*"})
        #print(res.text)
        res = requests.post("http://10.245.146.64:27000/api/v1/search/ip?page=1&rows=10", headers=headers, json={"keyword": "protocols:*"})
        print(res.text)
        #res = requests.post("http://10.245.146.64:27000/api/v1/search/domain?page=1&rows=10", headers=headers, json={"keyword": "*"})
        #print(res.text)

    # 3. wide_table search detail
    def wide_table_search_detail():
        res = requests.post("http://10.245.146.64:27000/api/v1/search/organization/stats?page=1&rows=10", headers=headers, json={"keyword": "*"})
        print(res.text)
        res = requests.post("http://10.245.146.64:27000/api/v1/search/ip/stats?page=1&rows=10", headers=headers, json={"keyword": "*"})
        print(res.text)
        res = requests.post("http://10.245.146.64:27000/api/v1/search/domain/stats?page=1&rows=10", headers=headers, json={"keyword": "*"})
        print(res.text)

    # 4. trend
    def squint_trend():
        res = requests.get("http://10.245.146.64:27000/api/v1/trend/active_ip?scale=daily", headers=headers)
        print(res.text)
        res = requests.get("http://10.245.146.64:27000/api/v1/trend/asset?scale=daily", headers=headers)
        print(res.text)
        res = requests.get("http://10.245.146.64:27000/api/v1/trend/icp?scale=monthly", headers=headers)
        print(res.text)
        res = requests.get("http://10.245.146.64:27000/api/v1/trend/psr?scale=monthly", headers=headers)
        print(res.text)
        res = requests.get("http://10.245.146.64:27000/api/v1/trend/dns?scale=monthly", headers=headers)
        print(res.text)
        res = requests.get("http://10.245.146.64:27000/api/v1/trend/router?scale=monthly", headers=headers)
        print(res.text)
    
    # 5. state
    def squint_state():
        res = requests.get("http://10.245.146.64:27000/api/v1/state/port?size=5", headers=headers)
        print(res.text)
        res = requests.get("http://10.245.146.64:27000/api/v1/state/protocol?size=10", headers=headers)
        print(res.text)
        res = requests.get("http://10.245.146.64:27000/api/v1/state/http_server?size=20", headers=headers)
        print(res.text)


    wide_table_search()
    #squint_trend()
    #squint_state()