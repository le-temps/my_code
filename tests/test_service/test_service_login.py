import requests
import json

from utils.config import settings
def test_service_login():
   headers = {"token": settings.service_auth.token}
   res = requests.post("http://10.245.146.64:27001/api/v1/signup", headers=headers, data=json.dumps({"user_name": "letemps", "password": "123456"}))
   print(res.text)
   res = requests.post("http://10.245.146.64:27001/api/v1/login", headers=headers, data=json.dumps({"user_name": "ltemps", "password": "123456"}))
   print(res.text)
   res = requests.post("http://10.245.146.64:27001/api/v1/login", headers=headers, data=json.dumps({"user_name": "letemps", "password": "12345"}))
   print(res.text)
   res = requests.post("http://10.245.146.64:27001/api/v1/login", headers=headers, data=json.dumps({"user_name": "letemps", "password": "123456"}))
   print(res.text)