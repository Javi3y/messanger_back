from fastapi import APIRouter
from app.v1.messaging.routes.endpoints import router as messaging_router
from app.v1.messaging.routes.sessions import router as sessions_router
from app.v1.users.routes.endpoints import router as users_router
from app.v1.files.routes.endpoints import router as files_router

router = APIRouter(prefix="/v1")

router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(files_router, prefix="/files", tags=["files"])
router.include_router(messaging_router, prefix="/messaging", tags=["messaging"])
router.include_router(sessions_router, prefix="/messaging", tags=["messaging"])
