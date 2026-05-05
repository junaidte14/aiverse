"""
Pydantic schemas for admin endpoints
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field


# ==================== USER SCHEMAS ====================


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    is_active: bool
    total_tokens_used: int
    total_cost: float
    monthly_cost: float
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = Field(default="user")
    is_active: bool = Field(default=True)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    role: Optional[str] = None
    is_active: Optional[bool] = None


# ==================== CONVERSATION SCHEMAS ====================


class ConversationResponse(BaseModel):
    conversation_id: str
    user_id: int
    model_name: str
    messages: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# ==================== ANALYTICS SCHEMAS ====================


class OverviewStats(BaseModel):
    total_users: int
    active_users: int
    total_conversations: int
    period_conversations: int
    total_tokens: int
    total_cost: float


class UserUsageStats(BaseModel):
    username: str
    total_tokens: int
    total_cost: float
    monthly_cost: float


class ModelPopularity(BaseModel):
    model: str
    count: int


class DailyUsage(BaseModel):
    date: str
    conversations: int


class AnalyticsDashboard(BaseModel):
    overview: OverviewStats
    top_users: List[UserUsageStats]
    model_popularity: List[ModelPopularity]
    daily_usage: List[DailyUsage]
    period_days: int
