from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.observability.logging import configure_logging
from app.observability.metrics import metrics_router

from app.api import auth, workflows, jobs

settings = get_settings()
configure_logging()

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(workflows.router)
app.include_router(jobs.router)
app.include_router(metrics_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}