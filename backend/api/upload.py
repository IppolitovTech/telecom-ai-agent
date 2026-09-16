from fastapi import APIRouter, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from agent.documents import handle_upload
from models.upload import UploadResponse

router = APIRouter()


@router.post("/api/upload")
async def upload(file: UploadFile) -> UploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    content = await file.read()
    return await run_in_threadpool(handle_upload, file.filename, content)
