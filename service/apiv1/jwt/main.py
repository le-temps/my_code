from service.apiv1.jwt.my_auth import Auth
from service.apiv1.jwt.user_model import AuthModel
from fastapi import Security,APIRouter
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from service.db.elasticsearch import es
import datetime

router = APIRouter()#定义router
security = HTTPBearer()
auth_handler = Auth()

@router.post('/api/v1/signup')
def signup(user_details: AuthModel):
    if es.search_by_query_string(index="squint_user",query_string=f"user_name:{user_details.user_name}")["hits"]["hits"] != []:
        return {
            "state": 800, 
        "meta": { 
            "total": 1,
        },
        "payload": "Account already exist"
        }
    try:
        time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        hashed_password = auth_handler.encode_password(user_details.password)
        user = {
                "user_name": user_details.user_name, 
                "password": hashed_password,
                "crated_time":time
                }
        
        es.insert("squint_user", user_details.user_name, user)
        return {
            "state": 800, 
            "meta": { 
                "total": 1,
            },
            "payload": 
                "successfully signup"
        }
    except Exception as e:
        print(e)
        error_msg = 'Failed to signup user'
        return error_msg

@router.post('/api/v1/login')
def login(user_details: AuthModel):
    user = es.search_by_query_string(index="squint_user",query_string=f"user_name:{user_details.user_name}")
    if (user["hits"]["hits"] == []):
        return {
            "statusCode": 400, 
            "data": {
                "state": 901,
                "msg": "Invalid username" 
            }
        }

    real_password = user["hits"]["hits"][0]["_source"]["password"]

    if (auth_handler.verify_password(user_details.password, real_password)== False):
        return {
            "statusCode": 400, 
            "data": {
                "state": 901,
                "msg": "Invalid password" 
            }
        }

    access_token = auth_handler.encode_token(user_details.user_name)
    refresh_token = auth_handler.encode_refresh_token(user_details.user_name)
    time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    body={"access_token":access_token,
          "refresh_token":refresh_token,
          "last_login":time}
    es.update("squint_user", user_details.user_name, body)
    return {
            "state": 800, 
            "meta": { 
                "total": 2,
            },
            "payload": 
                {'access_token': access_token, 'refresh_token': refresh_token} 
        }
    
        
@router.post('/api/v1/secret')
def secret_data(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    if(auth_handler.decode_token(token)):
        return 'Top Secret data only authorized users can access this info'

@router.get('/api/v1/notsecret')
def not_secret_data():
    return 'Not secret data'

@router.get('/api/v1/refresh_token')
def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    refresh_token = credentials.credentials
    new_token = auth_handler.refresh_token(refresh_token)
    return {'access_token': new_token}    
