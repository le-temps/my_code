from fastapi import APIRouter
  
from service.apiv1.raw_table.raw_table import router as raw_table_router
from service.apiv1.wide_table.wide_table import router as wide_table_router
from service.apiv1.task.task import router as task_router

router = APIRouter()
router.include_router(raw_table_router)
router.include_router(wide_table_router)
router.include_router(task_router)