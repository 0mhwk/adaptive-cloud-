"""
backend/app/api/v1/routes/incidents.py
API endpoints for managing and inspecting correlated security incidents.
- GET /incidents: List incidents with severity, status, and time filters.
- GET /incidents/{id}: Retrieve detailed incident data including linked events & detections.
"""
from __future__ import annotations

import math
import uuid
from datetime import datetime
from typing import Annotated, Any, Optional
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import require_role
from app.db.session import get_db
from app.models.incident import Incident, IncidentItem
from app.models.user import User
from app.schemas.common import PaginationEnvelope
from app.schemas.incident import IncidentDetailResponse, IncidentItemResponse, IncidentResponse

router = APIRouter(prefix="/incidents", tags=["incidents"])

_viewer = Depends(require_role("admin", "analyst", "viewer"))


@router.get(
    "",
    response_model=PaginationEnvelope[IncidentResponse],
    summary="List correlated security incidents with filters and pagination",
)
async def list_incidents(
    _user: Annotated[User, _viewer],
    db: Annotated[AsyncSession, Depends(get_db)],
    severity: Optional[str] = Query(None, description="Filter by severity: low | medium | high | critical"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: open | investigating | resolved"),
    from_dt: Optional[datetime] = Query(None, alias="from", description="Start timestamp (UTC)"),
    to_dt: Optional[datetime] = Query(None, alias="to", description="End timestamp (UTC)"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=200, description="Items per page"),
) -> PaginationEnvelope[IncidentResponse]:
    stmt = select(Incident)

    if severity:
        stmt = stmt.where(Incident.severity == severity)
    if status_filter:
        stmt = stmt.where(Incident.status == status_filter)
    if from_dt:
        stmt = stmt.where(Incident.created_at >= from_dt)
    if to_dt:
        stmt = stmt.where(Incident.created_at <= to_dt)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total: int = (await db.execute(count_stmt)).scalar_one()

    offset = (page - 1) * size
    stmt = stmt.order_by(Incident.created_at.desc()).offset(offset).limit(size)
    records = (await db.execute(stmt)).scalars().all()

    items = [IncidentResponse.model_validate(r) for r in records]
    pages = math.ceil(total / size) if size > 0 else 0

    return PaginationEnvelope[IncidentResponse](
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get(
    "/{incident_id}",
    response_model=IncidentDetailResponse,
    summary="Retrieve incident details and linked telemetry items",
)
async def get_incident(
    incident_id: uuid.UUID,
    _user: Annotated[User, _viewer],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> IncidentDetailResponse:
    stmt = select(Incident).where(Incident.id == incident_id)
    res = await db.execute(stmt)
    incident = res.scalar_one_or_none()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found",
        )

    # Fetch linked items
    items_stmt = select(IncidentItem).where(IncidentItem.incident_id == incident_id).order_by(IncidentItem.created_at.asc())
    items_res = await db.execute(items_stmt)
    items_records = items_res.scalars().all()

    items = [IncidentItemResponse.model_validate(it) for it in items_records]

    return IncidentDetailResponse(
        id=incident.id,
        title=incident.title,
        severity=incident.severity,
        status=incident.status,
        assigned_to=incident.assigned_to,
        description=incident.description,
        summary=incident.summary,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
        items=items,
    )


class ApprovalRequest(BaseModel):
    action_ids: Optional[list[str]] = None
    decided_by: Optional[str] = "Operator"
    comment: Optional[str] = ""
    dry_run: Optional[bool] = True


@router.post(
    "/{incident_id}/approve",
    summary="Operator approves proposed healing actions (Permission Gate)",
)
async def approve_incident_endpoint(
    incident_id: str,
    body: ApprovalRequest,
    _user: Annotated[User, Depends(require_role("admin", "analyst"))],
) -> dict[str, Any]:
    from core.incident_store import incident_store
    try:
        updated = incident_store.approve_and_execute(
            incident_id=incident_id,
            action_ids=body.action_ids,
            decided_by=body.decided_by or _user.username,
            comment=body.comment or "Approved via Admin Console",
            dry_run=body.dry_run if body.dry_run is not None else True,
        )
        return updated
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{incident_id}/reject",
    summary="Operator rejects proposed healing actions (Zero execution)",
)
async def reject_incident_endpoint(
    incident_id: str,
    body: ApprovalRequest,
    _user: Annotated[User, Depends(require_role("admin", "analyst"))],
) -> dict[str, Any]:
    from core.incident_store import incident_store
    try:
        updated = incident_store.reject_action(
            incident_id=incident_id,
            decided_by=body.decided_by or _user.username,
            comment=body.comment or "Rejected via Admin Console",
        )
        return updated
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{incident_id}/rollback",
    summary="Rollback executed countermeasures safely",
)
async def rollback_incident_endpoint(
    incident_id: str,
    body: ApprovalRequest,
    _user: Annotated[User, Depends(require_role("admin", "analyst"))],
) -> dict[str, Any]:
    from core.incident_store import incident_store
    try:
        updated = incident_store.rollback_action(
            incident_id=incident_id,
            decided_by=body.decided_by or _user.username,
            comment=body.comment or "Rollback via Admin Console",
            dry_run=body.dry_run if body.dry_run is not None else True,
        )
        return updated
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


