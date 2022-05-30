import requests
import json

from utils.config import settings

def test_service_task():
    headers = {"token": settings.service_auth.token}
    res = requests.post("http://10.245.146.64:27000/api/v1/task", headers=headers, data=json.dumps({"source_index_type": "ip_dns", "destination_index_type": "ip", "values": ["0.0.0.0"]}))
    
    print(res.text)