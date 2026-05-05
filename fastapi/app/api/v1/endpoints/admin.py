"""
Admin endpoints for user management, analytics, and system administration
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.auth_dependencies import get_current_active_user, get_db, require_admin
from app.db.models.user import User
from app.db.models.conversation import Conversation
from app.schemas.admin import (
    UserResponse,
    UserUpdate,
    UserCreate,
    AnalyticsDashboard,
)

router = APIRouter(prefix="/admin", tags=["admin"])

# ==================== USER MANAGEMENT ====================


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List all users with filtering and pagination"""
    query = select(User)

    # Apply filters
    filters = []
    if search:
        search_term = f"%{search}%"
        filters.append(
            or_(User.username.ilike(search_term), User.email.ilike(search_term))
        )
    if role:
        filters.append(User.role == role)
    if is_active is not None:
        filters.append(User.is_active == is_active)

    if filters:
        query = query.where(and_(*filters))

    # Order and paginate
    query = query.order_by(desc(User.created_at)).offset(skip).limit(limit)

    result = await db.execute(query)
    users = result.scalars().all()

    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Get user details by ID"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create new user (admin only)"""
    from app.core.security import get_password_hash

    # Check if username exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")

    # Check if email exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already exists")

    # Create user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        role=user_data.role,
        is_active=user_data.is_active,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update user details"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent admin from demoting themselves
    if user.id == current_user.id and user_data.role and user_data.role != user.role:
        raise HTTPException(status_code=400, detail="Cannot change your own role")

    # Update fields
    update_data = user_data.model_dump(exclude_unset=True)

    # Handle password separately
    if "password" in update_data and update_data["password"]:
        from app.core.security import get_password_hash

        user.hashed_password = get_password_hash(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    return user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete user (soft delete - set is_active=False)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent self-deletion
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    user.is_active = False
    await db.commit()

    return {"message": "User deleted successfully"}


# ==================== ANALYTICS DASHBOARD ====================


@router.get("/analytics/dashboard", response_model=AnalyticsDashboard)
async def get_analytics_dashboard(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Get comprehensive analytics dashboard"""
    start_date = datetime.utcnow() - timedelta(days=days)

    # Total users
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar()

    # Active users (logged in last 30 days)
    active_users_result = await db.execute(
        select(func.count(User.id)).where(
            and_(User.is_active == True, User.last_login >= start_date)
        )
    )
    active_users = active_users_result.scalar() or 0

    # Total conversations
    total_convs_result = await db.execute(select(func.count(Conversation.id)))
    total_conversations = total_convs_result.scalar() or 0

    # Conversations in period
    period_convs_result = await db.execute(
        select(func.count(Conversation.id)).where(Conversation.created_at >= start_date)
    )
    period_conversations = period_convs_result.scalar() or 0

    # Total tokens and cost
    total_tokens_result = await db.execute(select(func.sum(User.total_tokens_used)))
    total_tokens = total_tokens_result.scalar() or 0

    total_cost_result = await db.execute(select(func.sum(User.total_cost)))
    total_cost = total_cost_result.scalar() or 0.0

    # Per-user usage stats
    user_stats_query = (
        select(
            User.username, User.total_tokens_used, User.total_cost, User.monthly_cost
        )
        .where(User.total_tokens_used > 0)
        .order_by(desc(User.total_cost))
        .limit(10)
    )

    user_stats_result = await db.execute(user_stats_query)
    top_users = [
        {
            "username": row[0],
            "total_tokens": row[1],
            "total_cost": row[2],
            "monthly_cost": row[3],
        }
        for row in user_stats_result.all()
    ]

    # Model popularity
    model_stats_query = (
        select(Conversation.model_name, func.count(Conversation.id).label("count"))
        .where(Conversation.created_at >= start_date)
        .group_by(Conversation.model_name)
        .order_by(desc("count"))
        .limit(10)
    )

    model_stats_result = await db.execute(model_stats_query)
    model_popularity = [
        {"model": row[0], "count": row[1]} for row in model_stats_result.all()
    ]

    # Daily usage trend
    daily_stats_query = (
        select(
            func.date(Conversation.created_at).label("date"),
            func.count(Conversation.id).label("conversations"),
        )
        .where(Conversation.created_at >= start_date)
        .group_by("date")
        .order_by("date")
    )

    daily_stats_result = await db.execute(daily_stats_query)
    daily_usage = [
        {"date": row[0].isoformat(), "conversations": row[1] or 0}
        for row in daily_stats_result.all()
    ]

    return {
        "overview": {
            "total_users": total_users,
            "active_users": active_users,
            "total_conversations": total_conversations,
            "period_conversations": period_conversations,
            "total_tokens": int(total_tokens),
            "total_cost": float(total_cost),
        },
        "top_users": top_users,
        "model_popularity": model_popularity,
        "daily_usage": daily_usage,
        "period_days": days,
    }


@router.get("/analytics/users/{user_id}/stats")
async def get_user_stats(
    user_id: int,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Get detailed stats for specific user"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    start_date = datetime.utcnow() - timedelta(days=days)

    # User's conversations
    conv_count_result = await db.execute(
        select(func.count(Conversation.id)).where(
            and_(Conversation.user_id == user_id, Conversation.created_at >= start_date)
        )
    )
    conversation_count = conv_count_result.scalar() or 0

    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.isoformat(),
        },
        "usage": {
            "total_tokens": user.total_tokens_used,
            "total_cost": user.total_cost,
            "monthly_cost": user.monthly_cost,
            "monthly_limit": 100.0,  # From config
            "conversation_count": conversation_count,
        },
    }


# ==================== CONVERSATION MANAGEMENT ====================


@router.get("/conversations")
async def admin_list_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[int] = None,
    model_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Admin only: List all system conversations with filtering"""
    query = select(Conversation)

    # Apply Admin Filters
    filters = []
    if user_id:
        filters.append(Conversation.user_id == user_id)
    if model_name:
        filters.append(Conversation.model_name == model_name)

    if filters:
        query = query.where(and_(*filters))

    # Order by most recent activity
    query = query.order_by(desc(Conversation.updated_at)).offset(skip).limit(limit)

    result = await db.execute(query)
    conversations = result.scalars().all()

    return conversations


@router.get("/conversations/{conversation_id}")
async def admin_get_conversation_detail(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Admin only: Get full conversation details and messages for support/audit[cite: 6, 7]"""
    # Use join to avoid lazy loading issues with messages
    from sqlalchemy.orm import selectinload

    query = (
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )

    result = await db.execute(query)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation
