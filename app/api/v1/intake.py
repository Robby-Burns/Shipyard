from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.intake import (
    IntakeChatInput,
    IntakeSessionCreate,
    IntakeSessionResponse,
)
from app.services.auth import get_current_user
from app.services.intake import IntakeService

router = APIRouter(prefix="/api/v1/intake", tags=["Engineering Intake"])


@router.post(
    "", response_model=IntakeSessionResponse, status_code=status.HTTP_201_CREATED
)
async def create_intake_session(
    req: IntakeSessionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    service = IntakeService(db)
    return await service.create_session(
        req.title,
        owner_id=user.get("sub"),
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/{session_id}", response_model=IntakeSessionResponse)
async def get_intake_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    service = IntakeService(db)
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Intake session not found"
        )
    if session.owner_id != user.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden"
        )
    return session


@router.post("/{session_id}/chat", response_model=IntakeSessionResponse)
async def send_chat_message(
    session_id: uuid.UUID,
    chat_input: IntakeChatInput,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    service = IntakeService(db)
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Intake session not found"
        )
    if session.owner_id != user.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden"
        )
    try:
        return await service.send_chat_message(
            session_id,
            chat_input.message,
            request_id=getattr(request.state, "request_id", None),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{session_id}/upload", response_model=IntakeSessionResponse)
async def upload_intake_file(
    session_id: uuid.UUID,
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    service = IntakeService(db)
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Intake session not found"
        )
    if session.owner_id != user.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden"
        )
    
    try:
        # Check size before reading fully into memory to prevent OOM
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10MB
        if file_size > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Uploaded file exceeds maximum limit of {MAX_UPLOAD_BYTES / (1024 * 1024)}MB."
            )
            
        file_bytes = await file.read()
        from app.utils.file_parser import extract_text_from_file
        result = await extract_text_from_file(file.filename, file_bytes)
        
        if result.method == "failed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to extract text from file: {result.error_detail}"
            )
            
        if not result.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="The uploaded file contains no extractable text."
            )
            
        if result.method == "ocr":
            formatted_message = f"[Uploaded File: {file.filename} (OCR Extracted)]\n\n{result.text}"
        else:
            formatted_message = f"[Uploaded File: {file.filename}]\n\n{result.text}"
        
        return await service.send_chat_message(
            session_id,
            formatted_message,
            request_id=getattr(request.state, "request_id", None),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

