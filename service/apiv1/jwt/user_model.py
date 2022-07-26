from pydantic import BaseModel

class AuthModel(BaseModel):
    user_name: str
    password: str