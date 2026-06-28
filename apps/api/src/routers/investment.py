from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.core.deps import current_user
from src.models import Application, ResumeBranch, User
from src.models.investment import Investment
from src.schemas.investment import (
    CreateInvestmentIn,
    InvestmentOut,
    UpdateInvestmentIn,
)

router = APIRouter(
    prefix="/api/v1/applications/{app_id}/investments", tags=["investment"]
)


def _check_app(app_id: UUID, user: User, db: Session) -> Application:
    a = (
        db.query(Application)
        .filter(Application.id == app_id, Application.user_id == user.id)
        .first()
    )
    if not a:
        raise HTTPException(404, "application not found")
    return a


def _label(db: Session, branch_id: UUID | None) -> str | None:
    if not branch_id:
        return None
    b = db.get(ResumeBranch, branch_id)
    if not b:
        return None
    return b.version_label + (f" · {b.match_score}" if b.match_score is not None else "")


def _ser(db: Session, iv: Investment) -> InvestmentOut:
    return InvestmentOut(
        id=iv.id,
        action_type=iv.action_type,
        action_at=iv.action_at,
        channel=iv.channel,
        notes=iv.notes,
        used_resume_branch_id=iv.used_resume_branch_id,
        used_branch_label=_label(db, iv.used_resume_branch_id),
    )


def _get_iv(db: Session, app_id: UUID, iv_id: UUID) -> Investment:
    iv = (
        db.query(Investment)
        .filter(Investment.id == iv_id, Investment.application_id == app_id)
        .first()
    )
    if not iv:
        raise HTTPException(404)
    return iv


@router.post("", response_model=InvestmentOut, status_code=201)
def create_investment(
    app_id: UUID,
    body: CreateInvestmentIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> InvestmentOut:
    _check_app(app_id, user, db)
    iv = Investment(application_id=app_id, **body.model_dump())
    db.add(iv)
    db.commit()
    db.refresh(iv)
    return _ser(db, iv)


@router.get("", response_model=list[InvestmentOut])
def list_investments(
    app_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> list[InvestmentOut]:
    _check_app(app_id, user, db)
    rows = (
        db.query(Investment)
        .filter(Investment.application_id == app_id)
        .order_by(Investment.action_at.desc())
        .all()
    )
    return [_ser(db, iv) for iv in rows]


@router.patch("/{iv_id}", response_model=InvestmentOut)
def update_investment(
    app_id: UUID,
    iv_id: UUID,
    body: UpdateInvestmentIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> InvestmentOut:
    _check_app(app_id, user, db)
    iv = _get_iv(db, app_id, iv_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(iv, k, v)
    db.commit()
    db.refresh(iv)
    return _ser(db, iv)


@router.delete("/{iv_id}", status_code=204)
def delete_investment(
    app_id: UUID,
    iv_id: UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> None:
    _check_app(app_id, user, db)
    iv = _get_iv(db, app_id, iv_id)
    db.delete(iv)
    db.commit()
