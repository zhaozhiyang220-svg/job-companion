from fastapi import FastAPI

from src.routers import health

app = FastAPI(title="Job Companion API", version="0.0.0")
app.include_router(health.router)
