from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def root():
    return {"status": "ok", "message": "Messenger API is running", "version": "1.0.0"}
