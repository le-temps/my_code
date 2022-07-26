import os
import jwt # used for encoding and decoding jwt tokens
from fastapi import HTTPException # used to handle error handling
from passlib.context import CryptContext # used for hashing the password 
from datetime import datetime, timedelta # used to handle expiry time for tokens

class Auth():
    # hasher= CryptContext()
    hasher= CryptContext(schemes=["sha512_crypt"])
    secret = "test"
    
 
    def encode_password(self, password):
        return self.hasher.hash(password)

    def verify_password(self, password, encoded_password):
        return self.hasher.verify(password, encoded_password)

    def encode_token(self, username):
        payload = {
            'exp' : datetime.utcnow() + timedelta(days=0, minutes=30),#设置读取世界标准时间
            'iat' : datetime.utcnow(),
            'scope': 'access_token',
            'sub' : username
        }
        return jwt.encode(
            payload, 
            self.secret,
            algorithm='HS256'
        )

    def decode_token(self, token):
        try:
            payload = jwt.decode(token, self.secret, algorithms=['HS256'])
            if (payload['scope'] == 'access_token'):
                return payload['sub']   
            raise {
                "statusCode": 401, 
                "data": {
                    "state": 900,
                    "msg": "No Token Exists" 
                }
            }
        except jwt.ExpiredSignatureError:
            raise {
                "statusCode": 401, 
                "data": {
                    "state": 902,
                    "msg": "Access Token Expired" 
                }
            }
        except jwt.InvalidTokenError:
            raise {
                "statusCode": 401, 
                "data": {
                    "state": 902,
                    "msg": "Access Token Expired" 
                }
            }

    def encode_refresh_token(self, username):
        payload = {
            'exp' : datetime.utcnow() + timedelta(days=0, hours=10),
            'iat' : datetime.utcnow(),
            'scope': 'refresh_token',
            'sub' : username
        }
        return jwt.encode(
            payload, 
            self.secret,
            algorithm='HS256'
        )
    def refresh_token(self, refresh_token):
        try:
            payload = jwt.decode(refresh_token, self.secret, algorithms=['HS256'])
            if (payload['scope'] == 'refresh_token'):
                username = payload['sub']
                new_token = self.encode_token(username)
                return new_token
            raise {
                    "statusCode": 401, 
                    "data": {
                        "state": 900,
                        "msg": "No Token Exists" 
                    }
                }
        except jwt.ExpiredSignatureError:
            raise {
                    "statusCode": 401, 
                    "data": {
                        "state": 903,
                        "msg": "Refresh Token Expired" 
                    }
                }
        except jwt.InvalidTokenError:
            raise {
                    "statusCode": 401, 
                    "data": {
                        "state": 903,
                        "msg": "Refresh Token Expired" 
                    }
                }