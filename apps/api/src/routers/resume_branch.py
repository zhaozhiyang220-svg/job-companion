from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from src.core.db import get_db
from src.core.deps import current_user
from src.core.security import decrypt_field
from src.models import Application, MasterResume, ResumeBranch, User
from src.schemas.resume_branch import (
    BranchDetail,
    BranchSummary,
    CreateBranchIn,
    UpdateBranchIn,
)
from src.services.patch_generator import generate_patch
from src.services.patch_ops import RewriteTooLargeError, apply_operations
from src.services.resume_scorer import score_branch

router = APIRouter(
    prefix="/api/v1/applications/{app_id}/branches", tags=["resume-branch"]
)


def _serialize_master(r: MasterResume) -> dict[str, object]:
    return {
        "ability_cards": [
            {
                "id": str(c.id),
                "skill_name": c.skill_name,
                "evidence_text": c.evidence_text,
                "level": c.level,
                "last_used_year": c.last_used_year,
                "tags": c.tags,
            }
            for c in r.ability_cards
        ],
        "project_cards": [
            {
                "id": str(c.id),
                "project_name": c.project_name,
                "role": c.role,
                "period": c.period,
                "scale_data": c.scale_data,
                "star": c.star,
                "tech_stack": c.tech_stack,
                "domain_tags": c.domain_tags,
            }
            for c in r.project_cards
        ],
        "experience_cards": [
            {
                "id": str(c.id),
                "company": decrypt_field(c.company_encrypted) if c.company_encrypted else "",
                "period": c.period,
                "title": c.title,
                "scope": c.scope,
                "achievements": c.achievements,
                "industry": c.industry,
                "is_current": c.is_current,
            }
            for c in r.experience_cards
        ],
    }


def _serialize_jd(app: Application) -> dict[str, object]:
    jp = app.job_posting
    return {
        "company_name": jp.company_name,
        "job_title": jp.job_title,
        "salary_range": jp.salary_range,
        "location": jp.location,
        "language": jp.language,
        "requirements": jp.requirements_parsed,
        "hidden_preferences": jp.hidden_preferences,
    }


def _get_app(app_id: UUID, user: User, db: Session) -> Application:
    a = (
        db.query(Application)
        .filter(Application.id == app_id, Application.user_id == user.id)
        .options(selectinload(Application.job_posting))
        .first()
    )
    if not a:
        raise HTTPException(404, "application not found")
    return a


def _get_master(user: User, db: Session) -> MasterResume:
    r = db.query(MasterResume).filter(MasterResume.user_id == user.id).first()
    if not r:
        raise HTTPException(404, "master resume not found; upload first")
    return r


def _get_branch(db: Session, app_id: UUID, branch_id: UUID) -> ResumeBranch:
    b = (
        db.query(ResumeBranch)
        .filter(ResumeBranch.id == branch_id, ResumeBranch.application_id == app_id)
        .first()
    )
    if not b:
        raise HTTPException(404, "branch not found")
    return b


def _next_version(db: Session, app_id: UUID) -> str:
    n = db.query(ResumeBranch).filter(ResumeBranch.application_id == app_id).count()
    return f"v{n + 1}"


def _deactivate_others(db: Session, app_id: UUID) -> None:
    for old in (
        db.query(ResumeBranch)
        .filter(ResumeBranch.application_id == app_id, ResumeBranch.is_active.is_(True))
        .all()
    ):
        old.is_active = False


def _detail(
    b: ResumeBranch, rendered: dict[str, object], master: dict[str, object]
) -> BranchDetail:
    return BranchDetail(
        id=b.id,
        version_label=b.version_label,
        match_score=b.match_score,
        language=b.language,
        created_at=b.created_at,
        is_active=b.is_active,
        patch=b.patch,
        ai_reasoning=b.ai_reasoning,
        rendered_resume=rendered,
        master_snapshot=master,
    )


@router.post("", response_model=BranchDetail, status_code=201)
async def create_branch(
    app_id: UUID,
    body: CreateBranchIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> BranchDetail:
    app = _get_app(app_id, user, db)
    master = _serialize_master(_get_master(user, db))
    jd = _serialize_jd(app)
    lang = body.language or str(jd.get("language", "zh"))
    out = await generate_patch(master, jd, lang, user.id)
    patch_ops: list[dict[str, object]] = out["patch"]  # type: ignore[assignment]
    try:
        rendered = apply_operations(master, patch_ops)
    except RewriteTooLargeError as e:
        raise HTTPException(422, str(e)) from e
    score = await score_branch(rendered, jd, user.id)
    _deactivate_others(db, app_id)
    b = ResumeBranch(
        application_id=app_id,
        version_label=_next_version(db, app_id),
        patch=patch_ops,
        ai_reasoning=out["reasoning"],
        match_score=score,
        language=lang,
        is_active=True,
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return _detail(b, rendered, master)


@router.get("", response_model=list[BranchSummary])
def list_branches(
    app_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> list[BranchSummary]:
    _get_app(app_id, user, db)
    bs = (
        db.query(ResumeBranch)
        .filter(ResumeBranch.application_id == app_id)
        .order_by(ResumeBranch.created_at.desc())
        .all()
    )
    return [
        BranchSummary(
            id=b.id,
            version_label=b.version_label,
            match_score=b.match_score,
            language=b.language,
            created_at=b.created_at,
            is_active=b.is_active,
        )
        for b in bs
    ]


@router.get("/{branch_id}", response_model=BranchDetail)
def get_branch(
    app_id: UUID,
    branch_id: UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> BranchDetail:
    _get_app(app_id, user, db)
    b = _get_branch(db, app_id, branch_id)
    master = _serialize_master(_get_master(user, db))
    rendered = apply_operations(master, b.patch)
    return _detail(b, rendered, master)


@router.patch("/{branch_id}", response_model=BranchDetail)
def update_branch(
    app_id: UUID,
    branch_id: UUID,
    body: UpdateBranchIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> BranchDetail:
    _get_app(app_id, user, db)
    b = _get_branch(db, app_id, branch_id)
    master = _serialize_master(_get_master(user, db))
    try:
        rendered = apply_operations(master, body.patch)
    except RewriteTooLargeError as e:
        raise HTTPException(422, str(e)) from e
    b.patch = body.patch
    db.commit()
    db.refresh(b)
    return _detail(b, rendered, master)


@router.delete("/{branch_id}", status_code=204)
def delete_branch(
    app_id: UUID,
    branch_id: UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> None:
    _get_app(app_id, user, db)
    b = _get_branch(db, app_id, branch_id)
    db.delete(b)
    db.commit()


@router.post("/{branch_id}/rollback-to/{prev_id}", response_model=BranchDetail)
def rollback_to(
    app_id: UUID,
    branch_id: UUID,
    prev_id: UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> BranchDetail:
    _get_app(app_id, user, db)
    prev = _get_branch(db, app_id, prev_id)
    _deactivate_others(db, app_id)
    new = ResumeBranch(
        application_id=app_id,
        version_label=_next_version(db, app_id),
        patch=prev.patch,
        ai_reasoning=[{"op_index": -1, "reason": f"回滚自 {prev.version_label}"}],
        match_score=prev.match_score,
        language=prev.language,
        is_active=True,
    )
    db.add(new)
    db.commit()
    db.refresh(new)
    master = _serialize_master(_get_master(user, db))
    return _detail(new, apply_operations(master, new.patch), master)
