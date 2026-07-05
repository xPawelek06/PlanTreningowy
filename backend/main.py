import os
from datetime import date
from typing import List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import models
import schemas
from database import Base, SessionLocal, engine

Base.metadata.create_all(bind=engine)

# Sekret do zapisu (naglowek X-Auth-Secret) - w produkcji ustaw go jako zmienna
# srodowiskowa APP_SECRET w Renderze, zamiast polegac na tej wartosci domyslnej.
APP_SECRET = os.environ.get("APP_SECRET", "PlanTreningowy")

ALLOWED_ORIGINS = [
    "https://xpawelek06.github.io",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]

app = FastAPI(title="Plan Treningowy API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_secret(x_auth_secret: str = Header(default="")):
    if x_auth_secret != APP_SECRET:
        raise HTTPException(status_code=401, detail="Zly sekret (naglowek X-Auth-Secret)")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/plan", response_model=List[schemas.ExerciseOut])
def get_plan(db: Session = Depends(get_db)):
    exercises = (
        db.query(models.Exercise)
        .order_by(models.Exercise.day_order, models.Exercise.position)
        .all()
    )

    result = []
    for ex in exercises:
        latest = (
            db.query(models.Entry)
            .filter(models.Entry.exercise_id == ex.id)
            .order_by(models.Entry.created_at.desc())
            .first()
        )
        result.append(
            schemas.ExerciseOut(
                id=ex.id,
                day=ex.day,
                day_order=ex.day_order,
                position=ex.position,
                name=ex.name,
                sets_reps=ex.sets_reps,
                tm_info=ex.tm_info,
                is_main_lift=ex.is_main_lift,
                latest_zapas=latest.zapas if latest else None,
                latest_uwagi=latest.uwagi if latest else None,
                latest_entry_date=latest.entry_date if latest else None,
            )
        )
    return result


@app.post(
    "/api/entries",
    response_model=schemas.EntryOut,
    dependencies=[Depends(require_secret)],
)
def create_entry(payload: schemas.EntryCreate, db: Session = Depends(get_db)):
    exercise = (
        db.query(models.Exercise)
        .filter(models.Exercise.id == payload.exercise_id)
        .first()
    )
    if not exercise:
        raise HTTPException(status_code=404, detail="Nie ma cwiczenia o tym id")

    entry = models.Entry(
        exercise_id=payload.exercise_id,
        entry_date=payload.entry_date or date.today(),
        zapas=payload.zapas,
        uwagi=payload.uwagi,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@app.get(
    "/api/entries",
    response_model=List[schemas.EntryOut],
    dependencies=[Depends(require_secret)],
)
def list_entries(since: Optional[date] = None, db: Session = Depends(get_db)):
    """Do reczne synchronizacji przez trenera-personalnego do silownia/dziennik/."""
    q = db.query(models.Entry)
    if since:
        q = q.filter(models.Entry.entry_date >= since)
    return q.order_by(models.Entry.entry_date, models.Entry.id).all()


@app.post("/api/admin/seed", dependencies=[Depends(require_secret)])
def seed_plan(payload: schemas.SeedPayload, db: Session = Depends(get_db)):
    """Upsert planu po (day, name) - nie kasuje istniejacych cwiczen/historii,
    zeby zmiana TM po nowym cyklu nie urwala powiazanych wpisow zapas/uwagi."""
    updated, created = 0, 0
    for item in payload.exercises:
        existing = (
            db.query(models.Exercise)
            .filter(models.Exercise.day == item.day, models.Exercise.name == item.name)
            .first()
        )
        if existing:
            existing.day_order = item.day_order
            existing.position = item.position
            existing.sets_reps = item.sets_reps
            existing.tm_info = item.tm_info
            existing.is_main_lift = item.is_main_lift
            updated += 1
        else:
            db.add(models.Exercise(**item.model_dump()))
            created += 1
    db.commit()
    return {"status": "ok", "updated": updated, "created": created}
