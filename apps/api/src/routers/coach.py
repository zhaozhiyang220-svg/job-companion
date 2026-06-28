import contextlib
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.core.deps import current_user
from src.models import User
from src.models.coach_inquiry import CoachInquiry, CoachInquiryStatus
from src.schemas.coach import CoachAvailability, CoachInquiryOut, CreateInquiryIn
from src.services.notifier import notify_pm
from src.services.time_helpers import BJT, monday_of, week_range

router = APIRouter(prefix="/api/v1/coach", tags=["coach"])

SLOTS_PER_WEEK = 5


def _taken_this_week(db: Session) -> int:
    m = monday_of(datetime.now(BJT))
    s, e = week_range(m)
    n = (
        db.query(func.count(CoachInquiry.id))
        .filter(
            CoachInquiry.created_at >= s,
            CoachInquiry.created_at <= e,
            CoachInquiry.status != CoachInquiryStatus.DROPPED,
        )
        .scalar()
        or 0
    )
    return n


@router.get("/availability", response_model=CoachAvailability)
def availability(db: Session = Depends(get_db)) -> CoachAvailability:
    m = monday_of(datetime.now(BJT))
    n = _taken_this_week(db)
    return CoachAvailability(
        week_of=m, slots_total=SLOTS_PER_WEEK, slots_taken=n, available=n < SLOTS_PER_WEEK
    )


@router.post("/inquiries", response_model=CoachInquiryOut, status_code=201)
async def create_inquiry(
    body: CreateInquiryIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> CoachInquiryOut:
    n = _taken_this_week(db)
    if n >= SLOTS_PER_WEEK:
        raise HTTPException(
            409, {"code": "coach_full", "message": "本周 Coach 名额已售罄，下周再约"}
        )
    ci = CoachInquiry(
        user_id=user.id,
        application_id=body.application_id,
        source_screen=body.source_screen,
        contact_method=body.contact_method,
        notes=body.notes,
    )
    db.add(ci)
    db.commit()
    db.refresh(ci)
    with contextlib.suppress(Exception):
        await notify_pm(
            f"Coach Inquiry\nuser={user.id}\ncontact={body.contact_method}\n"
            f"source={body.source_screen}\nnotes={body.notes}\napp_id={body.application_id}"
        )
    return CoachInquiryOut(id=ci.id, available_after_create=(n + 1 < SLOTS_PER_WEEK))
