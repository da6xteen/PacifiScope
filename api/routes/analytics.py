from fastapi import APIRouter

router = APIRouter()

@router.get("/imbalance")
async def get_imbalance():
    return {"imbalance": 0.5}
