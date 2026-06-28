from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.core.deps import current_user
from src.core.security import decrypt_field, encrypt_field
from src.models import AbilityCard, ExperienceCard, MasterResume, ProjectCard, User
from src.schemas.master_resume import (
    AbilityCardOut,
    ExperienceCardOut,
    MasterResumeOut,
    ParseIn,
    ProjectCardOut,
    UploadInitIn,
    UploadInitOut,
)
from src.services.quality_diagnoser import diagnose as diagnose_svc
from src.services.resume_parser import parse_resume_text
from src.services.storage import download_bytes, presign_put
from src.services.text_extractor import extract_text

router = APIRouter(prefix="/api/v1/master-resume", tags=["master-resume"])


def _serialize(r: MasterResume) -> MasterResumeOut:
    return MasterResumeOut(
        id=r.id,
        basic_info=r.basic_info or {},
        quality_score=r.quality_score,
        ability_cards=[AbilityCardOut.model_validate(c) for c in r.ability_cards],
        project_cards=[ProjectCardOut.model_validate(c) for c in r.project_cards],
        experience_cards=[
            ExperienceCardOut(
                id=c.id,
                company=decrypt_field(c.company_encrypted) if c.company_encrypted else "",
                period=c.period,
                title=c.title,
                scope=c.scope,
                achievements=c.achievements,
                industry=c.industry,
                is_current=c.is_current,
            )
            for c in r.experience_cards
        ],
    )


@router.post("/upload-init", response_model=UploadInitOut)
def upload_init(body: UploadInitIn, user: User = Depends(current_user)) -> UploadInitOut:
    key = f"users/{user.id}/resumes/{uuid4()}-{body.filename}"
    url = presign_put(key, body.content_type)
    return UploadInitOut(upload_url=url, s3_key=key)


@router.post("/parse", response_model=MasterResumeOut)
async def parse(
    body: ParseIn, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> MasterResumeOut:
    blob = download_bytes(body.s3_key)
    text = extract_text(body.s3_key.split("/")[-1], blob)
    parsed = await parse_resume_text(text, user.persona_type, user.id)

    r = db.query(MasterResume).filter(MasterResume.user_id == user.id).first()
    if r is None:
        r = MasterResume(user_id=user.id)
        db.add(r)
        db.flush()
    else:
        for c in [*r.ability_cards, *r.project_cards, *r.experience_cards]:
            db.delete(c)
        db.flush()

    r.basic_info = parsed.basic_info
    r.parsed_from_file_url = body.s3_key
    for a in parsed.ability_cards:
        r.ability_cards.append(AbilityCard(**a.model_dump()))
    for p in parsed.project_cards:
        r.project_cards.append(ProjectCard(**p.model_dump()))
    for e in parsed.experience_cards:
        data = e.model_dump()
        company_raw = str(data.pop("company") or "—")
        r.experience_cards.append(
            ExperienceCard(company_encrypted=encrypt_field(company_raw), **data)
        )
    db.commit()
    db.refresh(r)
    return _serialize(r)


@router.get("", response_model=MasterResumeOut | None)
def get_mine(
    user: User = Depends(current_user), db: Session = Depends(get_db)
) -> MasterResumeOut | None:
    r = db.query(MasterResume).filter(MasterResume.user_id == user.id).first()
    return _serialize(r) if r else None


_CARD_MODELS: dict[str, type[AbilityCard] | type[ProjectCard] | type[ExperienceCard]] = {
    "ability": AbilityCard,
    "project": ProjectCard,
    "experience": ExperienceCard,
}


def _resolve_model(
    card_type: str,
) -> type[AbilityCard] | type[ProjectCard] | type[ExperienceCard]:
    model = _CARD_MODELS.get(card_type)
    if model is None:
        raise HTTPException(status_code=400, detail="invalid card type")
    return model


def _get_resume(user: User, db: Session) -> MasterResume:
    r = db.query(MasterResume).filter(MasterResume.user_id == user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="master resume not found; upload first")
    return r


@router.post("/cards/{card_type}", status_code=status.HTTP_201_CREATED)
def create_card(
    card_type: str,
    body: dict[str, object],
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    model = _resolve_model(card_type)
    r = _get_resume(user, db)
    if card_type == "experience" and "company" in body:
        body["company_encrypted"] = encrypt_field(str(body.pop("company")))
    obj = model(master_resume_id=r.id, **body)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return {"id": str(obj.id)}


@router.patch("/cards/{card_type}/{card_id}")
def update_card(
    card_type: str,
    card_id: str,
    body: dict[str, object],
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    model = _resolve_model(card_type)
    r = _get_resume(user, db)
    obj = (
        db.query(model)
        .filter(model.id == card_id, model.master_resume_id == r.id)
        .first()
    )
    if not obj:
        raise HTTPException(status_code=404, detail="card not found")
    if card_type == "experience" and "company" in body:
        body["company_encrypted"] = encrypt_field(str(body.pop("company")))
    for k, v in body.items():
        if hasattr(obj, k):
            setattr(obj, k, v)
    db.commit()
    return {"ok": True}


@router.delete("/cards/{card_type}/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(
    card_type: str,
    card_id: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> None:
    model = _resolve_model(card_type)
    r = _get_resume(user, db)
    obj = (
        db.query(model)
        .filter(model.id == card_id, model.master_resume_id == r.id)
        .first()
    )
    if not obj:
        raise HTTPException(status_code=404, detail="card not found")
    db.delete(obj)
    db.commit()


@router.post("/diagnose")
async def diagnose(
    user: User = Depends(current_user), db: Session = Depends(get_db)
) -> dict[str, object]:
    r = _get_resume(user, db)
    return await diagnose_svc(db, r.id, user.id)
