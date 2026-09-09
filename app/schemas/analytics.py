from pydantic import BaseModel
from typing import Dict, Any, List

class StatusCount(BaseModel):
    status: str
    count: int

class AnalyticsSummary(BaseModel):
    total_discovered: int
    total_applied: int
    pending_review: int
    interviews: int
    rejections: int
    no_response: int
    conversion_rate: float # interviews / total_applied percentage
    platform_breakdown: Dict[str, int]
    recent_activity: List[Dict[str, Any]]
