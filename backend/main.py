import os
from datetime import date, timedelta
from typing import List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

import models
import schemas
from database import Base, SessionLocal, engine

Base.metadata.create_all(bind=engine)


def migrate_schema():
    """create_all() tworzy tylko brakujace tabele, nie dodaje kolumn do juz
    istniejacych (np. produkcyjna tabela 'entries' na Neon) - wiec nowe kolumny
    dopisujemy tu recznie, bez ruszania istniejacych danych."""
    inspector = inspect(engine)
    if "entries" not in inspector.get_table_names():
        return
    existing_cols = {col["name"] for col in inspector.get_columns("entries")}
    if "seria_plus" not in existing_cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE entries ADD COLUMN seria_plus VARCHAR"))


migrate_schema()

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
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def current_week_bounds(today: Optional[date] = None):
    """Poniedzialek..niedziela biezacego tygodnia - ten sam wzorzec co w
    appce Waga (main.py, current_week_bounds)."""
    today = today or date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


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
                latest_seria_plus=latest.seria_plus if latest else None,
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
        seria_plus=payload.seria_plus,
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


@app.delete("/api/admin/entries", dependencies=[Depends(require_secret)])
def delete_all_entries(db: Session = Depends(get_db)):
    """Kasuje WSZYSTKIE wpisy (tabela 'entries'), zostawiajac plan (tabela
    'exercises') nietkniety. Uzywane przez trenera-personalnego przy
    cotygodniowej analizie: NAJPIERW archiwizacja tygodnia do
    gym/logs/archiwum.md (GET /api/entries?since=...), DOPIERO POTEM to
    kasowanie - zeby appka wracala do pustych pol na nowy tydzien bez utraty
    historii (ktora zyje dalej w repo mozgu)."""
    deleted = db.query(models.Entry).delete()
    db.commit()
    return {"status": "ok", "deleted": deleted}


@app.post(
    "/api/admin/weekly-trend-snapshot",
    dependencies=[Depends(require_secret)],
)
def create_weekly_trend_snapshot(db: Session = Depends(get_db)):
    """Kopiuje AKTUALNY stan tabeli 'exercises' do 'weekly_trend_snapshots',
    otagowany biezacym tygodniem (poniedzialek..niedziela). Wywoluj PRZED
    DELETE /api/admin/entries przy cotygodniowej archiwizacji - to jedyny
    sposob, w jaki appka moze pokazac historie mimo ze 'entries' jest co
    tydzien czyszczona (patrz docstring WeeklyTrendSnapshot w models.py).

    Idempotentne: wywolanie drugi raz w tym samym tygodniu kasuje i zastepuje
    poprzedni zrzut tego tygodnia (po week_start), a nie dubluje wiersze -
    bezpiecznie wywolac ponownie, jesli plan zmienil sie tego samego dnia
    (np. po zatwierdzeniu progresji) albo cos nie wyszlo za pierwszym razem."""
    week_start, week_end = current_week_bounds()

    db.query(models.WeeklyTrendSnapshot).filter(
        models.WeeklyTrendSnapshot.week_start == week_start
    ).delete()

    exercises = db.query(models.Exercise).order_by(
        models.Exercise.day_order, models.Exercise.position
    ).all()
    for ex in exercises:
        db.add(
            models.WeeklyTrendSnapshot(
                week_start=week_start,
                week_end=week_end,
                day=ex.day,
                day_order=ex.day_order,
                position=ex.position,
                name=ex.name,
                sets_reps=ex.sets_reps,
                tm_info=ex.tm_info,
                is_main_lift=ex.is_main_lift,
            )
        )
    db.commit()
    return {"status": "ok", "week_start": week_start, "week_end": week_end, "count": len(exercises)}


@app.get(
    "/api/weekly-trend",
    response_model=List[schemas.WeeklyTrendSnapshotOut],
)
def list_weekly_trend(db: Session = Depends(get_db)):
    """Publiczny odczyt (bez sekretu, jak GET /api/weekly-summary w appce
    Waga) - frontend grupuje plaska liste po week_start w sekcje 'Tydzien'."""
    return (
        db.query(models.WeeklyTrendSnapshot)
        .order_by(
            models.WeeklyTrendSnapshot.week_start.desc(),
            models.WeeklyTrendSnapshot.day_order,
            models.WeeklyTrendSnapshot.position,
        )
        .all()
    )


@app.delete("/api/admin/exercises", dependencies=[Depends(require_secret)])
def delete_exercises(payload: schemas.DeletePayload, db: Session = Depends(get_db)):
    """Kasuje cwiczenia po (day, name) - uzywane przez seed_data.py do usuwania
    wierszy, ktore zostaly wykreslone z listy EXERCISES. Kasuje tez powiazane
    wpisy Entry (historia zapas/uwagi tego cwiczenia znika razem z nim - to
    swiadome, "prawdziwe" kasowanie, nie tylko ukrycie wiersza)."""
    deleted, not_found = 0, []
    for ref in payload.exercises:
        exercise = (
            db.query(models.Exercise)
            .filter(models.Exercise.day == ref.day, models.Exercise.name == ref.name)
            .first()
        )
        if not exercise:
            not_found.append({"day": ref.day, "name": ref.name})
            continue
        db.query(models.Entry).filter(models.Entry.exercise_id == exercise.id).delete()
        db.delete(exercise)
        deleted += 1
    db.commit()
    return {"status": "ok", "deleted": deleted, "not_found": not_found}
