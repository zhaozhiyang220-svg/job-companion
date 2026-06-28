import os

import sentry_sdk

# Sentry 在创建 app 之前初始化；DSN 走 env，未配置则不启用（无副作用）。
_dsn = os.getenv("SENTRY_DSN", "")
if _dsn:
    sentry_sdk.init(dsn=_dsn, traces_sample_rate=0.1)

from fastapi import FastAPI  # noqa: E402

from src.routers import (  # noqa: E402
    application,
    auth,
    health,
    master_resume,
    me,
    resource,
    resume_branch,
)

app = FastAPI(title="Job Companion API", version="0.0.0")
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(me.router)
app.include_router(master_resume.router)
app.include_router(application.router)
app.include_router(resume_branch.router)
app.include_router(resource.router)
