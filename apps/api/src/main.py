import os

import sentry_sdk

# Sentry 在创建 app 之前初始化；DSN 走 env，未配置则不启用（无副作用）。
_dsn = os.getenv("SENTRY_DSN", "")
if _dsn:
    sentry_sdk.init(dsn=_dsn, traces_sample_rate=0.1)

from collections.abc import AsyncIterator  # noqa: E402
from contextlib import asynccontextmanager  # noqa: E402

from fastapi import FastAPI  # noqa: E402

from src.jobs.scheduler import shutdown_scheduler, start_scheduler  # noqa: E402
from src.routers import (  # noqa: E402
    application,
    auth,
    coach,
    health,
    investment,
    master_resume,
    me,
    resource,
    resume_branch,
    weekly,
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(title="Job Companion API", version="0.0.0", lifespan=lifespan)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(me.router)
app.include_router(master_resume.router)
app.include_router(application.router)
app.include_router(resume_branch.router)
app.include_router(resource.router)
app.include_router(investment.router)
app.include_router(weekly.router)
app.include_router(coach.router)
