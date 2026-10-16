from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import assessments, auth, dashboards, domains, handoff, questionnaires, users, workflow

app = FastAPI(title="DHL Hosting Decision Advisor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(questionnaires.router)
app.include_router(domains.router)
app.include_router(users.router)
app.include_router(assessments.router)
app.include_router(workflow.router)
app.include_router(dashboards.router)
app.include_router(handoff.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.on_event("startup")
def run_startup_seed():
    from app.db.session import SessionLocal
    from app.seed.seed import seed_if_empty

    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()
