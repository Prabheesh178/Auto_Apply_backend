import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.candidate import Candidate
from app.schemas.candidate import CandidateResponse, CandidateUpdate
from app.modules.resume.parser import resume_parser
from app.services.activity_service import activity_service
from app.config import settings

router = APIRouter(prefix="/candidate", tags=["Candidate"])

@router.get("/profile", response_model=CandidateResponse)
async def get_candidate_profile(db: AsyncSession = Depends(get_db)):
    stmt = select(Candidate)
    result = await db.execute(stmt)
    candidate = result.scalars().first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found")
    return candidate

@router.put("/profile", response_model=CandidateResponse)
async def update_candidate_profile(update_data: CandidateUpdate, db: AsyncSession = Depends(get_db)):
    stmt = select(Candidate)
    result = await db.execute(stmt)
    candidate = result.scalars().first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found")

    update_dict = update_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(candidate, key, value)

    await db.commit()
    await db.refresh(candidate)
    await activity_service.log("INFO", "Candidate", f"Candidate profile '{candidate.full_name}' updated.")
    return candidate

@router.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename.lower().endswith((".pdf", ".docx", ".txt", ".md")):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF, DOCX, TXT, or MD file.")

    file_path = os.path.join(settings.STORAGE_DIR, "resumes", f"master_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Ingest and parse with Gemini
    parsed_data = await resume_parser.parse_and_update(file_path)

    # Update or create candidate in database
    stmt = select(Candidate)
    result = await db.execute(stmt)
    candidate = result.scalars().first()
    if not candidate:
        candidate = Candidate(**parsed_data)
        db.add(candidate)
    else:
        for key, value in parsed_data.items():
            setattr(candidate, key, value)

    await db.commit()
    await db.refresh(candidate)

    return {
        "message": "Resume uploaded and parsed successfully",
        "candidate": {
            "id": candidate.id,
            "full_name": candidate.full_name,
            "email": candidate.email,
            "skills": candidate.structured_profile.get("skills", {}),
            "projects_count": len(candidate.structured_profile.get("projects", []))
        }
    }
