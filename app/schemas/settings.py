from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class SettingsUpdate(BaseModel):
    review_before_submit: Optional[bool] = None
    is_agent_paused: Optional[bool] = None
    target_roles: Optional[List[str]] = None
    target_locations: Optional[List[str]] = None
    min_match_score: Optional[int] = None
    max_daily_applications: Optional[int] = None
    monitored_companies: Optional[List[Dict[str, Any]]] = None

class SettingsResponse(BaseModel):
    id: int
    review_before_submit: bool
    is_agent_paused: bool
    target_roles: List[str]
    target_locations: List[str]
    min_match_score: int
    max_daily_applications: int
    monitored_companies: List[Dict[str, Any]]
    updated_at: datetime

    class Config:
        from_attributes = True
