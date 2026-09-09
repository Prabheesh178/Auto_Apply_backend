from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.settings import SystemSettings
from app.schemas.settings import SettingsResponse, SettingsUpdate
from app.services.activity_service import activity_service

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("", response_model=SettingsResponse)
async def get_settings(db: AsyncSession = Depends(get_db)):
    stmt = select(SystemSettings).where(SystemSettings.id == 1)
    result = await db.execute(stmt)
    settings = result.scalar_one_or_none()
    if not settings:
        settings = SystemSettings(id=1)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return settings

@router.put("", response_model=SettingsResponse)
async def update_settings(update_data: SettingsUpdate, db: AsyncSession = Depends(get_db)):
    stmt = select(SystemSettings).where(SystemSettings.id == 1)
    result = await db.execute(stmt)
    settings = result.scalar_one_or_none()
    if not settings:
        settings = SystemSettings(id=1)
        db.add(settings)

    update_dict = update_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(settings, key, value)

    await db.commit()
    await db.refresh(settings)

    # Activity log
    changes_str = ", ".join([f"{k}={v}" for k, v in update_dict.items()])
    await activity_service.log("INFO", "Settings", f"System settings updated: {changes_str}")

    return settings
