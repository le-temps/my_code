from fastapi import FastAPI
  
from service.apiv1.router import router
from utils.config import settings

project_name = settings.basic.project_name

app = FastAPI(title=project_name)
app.include_router(router)