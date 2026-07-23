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
    table_names = inspector.get_table_names()

    if "entries" in table_names:
        existing_cols = {col["name"] for col in inspector.get_columns("entries")}
        if "seria_plus" not in existing_cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE entries ADD COLUMN seria_plus VARCHAR"))

    # exercise_key (2026-07-14): tylko DODANIE pustej (nullable) kolumny w obu
    # tabelach - schemat, nie dane. Backfill istniejacych wierszy to OSOBNY,
    # recznie zatwierdzany krok - patrz backend/migrate_exercise_keys.py, NIE
    # uruchamiany automatycznie stad.
    for table_name in ("exercises", "weekly_trend_snapshots"):
        if table_name not in table_names:
            continue
        existing_cols = {col["name"] for col in inspector.get_columns(table_name)}
        if "exercise_key" not in existing_cols:
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN exercise_key VARCHAR"))


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
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def current_week_bounds(today: Optional[date] = None, week_offset: int = 0):
    """Poniedzialek..niedziela biezacego tygodnia - ten sam wzorzec co w
    appce Waga (main.py, current_week_bounds). week_offset=1 przesuwa wynik o
    jeden tydzien w przod (do reczneego tworzenia snapshotu NASTEPNEGO
    tygodnia z wyprzedzeniem, patrz create_weekly_trend_snapshot nizej) -
    domyslnie 0, czyli biezacy tydzien, bez zmiany zachowania dla
    dotychczasowych wywolan bez tego parametru."""
    today = (today or date.today()) + timedelta(weeks=week_offset)
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
                exercise_key=ex.exercise_key,
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
    """Upsert planu. Gdy item.exercise_key jest podany, dopasowanie do
    istniejacego wiersza idzie po (day, exercise_key) - wtedy zmiana 'name'
    przy tym samym kluczu to zwykly rename (UPDATE), nie nowy wiersz, i
    historia w zakladce Trend sie nie urywa (patrz models.Exercise.exercise_key).
    Gdy klucza brak (wiersz sprzed migracji, albo item bez klucza), spada z
    powrotem do starego dopasowania po (day, name) - jak dotychczas. W obu
    przypadkach nie kasuje istniejacych cwiczen/historii, zeby zmiana TM po
    nowym cyklu nie urwala powiazanych wpisow zapas/uwagi."""
    updated, created = 0, 0
    for item in payload.exercises:
        existing = None
        if item.exercise_key:
            existing = (
                db.query(models.Exercise)
                .filter(
                    models.Exercise.day == item.day,
                    models.Exercise.exercise_key == item.exercise_key,
                )
                .first()
            )
        if not existing:
            existing = (
                db.query(models.Exercise)
                .filter(models.Exercise.day == item.day, models.Exercise.name == item.name)
                .first()
            )
        if existing:
            existing.day_order = item.day_order
            existing.position = item.position
            existing.name = item.name
            if item.exercise_key:
                existing.exercise_key = item.exercise_key
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
def create_weekly_trend_snapshot(week_offset: int = 0, db: Session = Depends(get_db)):
    """Ustala TOZSAMOSC wierszy Trendu na biezacy tydzien (poniedzialek..
    niedziela) na podstawie AKTUALNEGO stanu tabeli 'exercises' - day/
    day_order/position/name/is_main_lift sa kopiowane z planu, zeby nie trzeba
    bylo recznie tworzyc wiersza dla kazdego cwiczenia. Wywoluj PRZED DELETE
    /api/admin/entries przy cotygodniowej archiwizacji - to jedyny sposob, w
    jaki appka moze pokazac historie mimo ze 'entries' jest co tydzien
    czyszczona (patrz docstring WeeklyTrendSnapshot w models.py).

    UWAGA (zmiana 2026-07-13): sets_reps/tm_info (kolumny "Serie x
    powtorzenia"/"Obciazenie" w Trendzie) to teraz REALNE dane wykonania
    treningu, wpisywane recznie przez Pawla z telefonu (patrz PATCH
    .../{snapshot_id} nizej) - NIE kopia zaplanowanego schematu z 'exercises'.
    Dlatego ten endpoint NIE kopiuje juz exercises.sets_reps/exercises.tm_info.

    Upsert po (week_start, day, exercise_key) gdy cwiczenie ma exercise_key
    wypelniony, w przeciwnym razie po (week_start, day, name) jak dotychczas
    (wiersze sprzed migracji, patrz backend/migrate_exercise_keys.py) - NIE po
    samym week_start: dla wiersza, ktory juz istnieje w tym tygodniu,
    aktualizujemy tylko tozsamosc (name/day_order/position/is_main_lift/
    exercise_key/week_end) i NIE ruszamy sets_reps/tm_info - zeby nie nadpisac
    tego, co Pawel juz recznie wpisal. 'name' jest teraz tez aktualizowane przy
    dopasowaniu po exercise_key, zeby rename w planie od razu byl widoczny w
    biezacym (jeszcze niearchiwizowanym) tygodniu Trendu. Dla NOWEGO wiersza
    (cwiczenie jeszcze nie mialo zrzutu w tym tygodniu) sets_reps/tm_info
    zaczynaja jako puste stringi, do uzupelnienia recznie.
    Bezpiecznie wywolac ponownie w tym samym tygodniu (np. po zmianie planu),
    nie dubluje wierszy i nie kasuje juz wpisanych danych wykonania.

    week_offset (dodane 2026-07-23): domyslnie 0 (biezacy tydzien - tak jak
    wywoluje to automatyczna cotygodniowa archiwizacja, Podczesc A kroku 4, bez
    zadnych parametrow). Frontend (przycisk "Dodaj kolejny tydzien" w zakladce
    Trend) woła ten sam endpoint z week_offset=1, zeby Pawel mogl zaczac
    wpisywac dane NASTEPNEGO tygodnia z wyprzedzeniem, zanim automatyczny
    snapshot poniedzialkowy go utworzy - upsert po (week_start, day,
    exercise_key/name) gwarantuje, ze gdy automatyczny snapshot faktycznie
    pozniej odpali sie dla tego samego tygodnia, nie nadpisze juz recznie
    wpisanych wartosci (patrz logika nizej), tylko zaktualizuje tozsamosc."""
    week_start, week_end = current_week_bounds(week_offset=week_offset)

    existing_rows = (
        db.query(models.WeeklyTrendSnapshot)
        .filter(models.WeeklyTrendSnapshot.week_start == week_start)
        .all()
    )
    existing_by_exercise_key = {
        (row.day, row.exercise_key): row for row in existing_rows if row.exercise_key
    }
    existing_by_name = {(row.day, row.name): row for row in existing_rows}

    exercises = db.query(models.Exercise).order_by(
        models.Exercise.day_order, models.Exercise.position
    ).all()

    created, updated = 0, 0
    for ex in exercises:
        row = None
        if ex.exercise_key:
            row = existing_by_exercise_key.get((ex.day, ex.exercise_key))
        if not row:
            row = existing_by_name.get((ex.day, ex.name))
        if row:
            row.day_order = ex.day_order
            row.position = ex.position
            row.name = ex.name
            row.exercise_key = ex.exercise_key
            row.is_main_lift = ex.is_main_lift
            row.week_end = week_end
            updated += 1
        else:
            db.add(
                models.WeeklyTrendSnapshot(
                    week_start=week_start,
                    week_end=week_end,
                    day=ex.day,
                    day_order=ex.day_order,
                    position=ex.position,
                    name=ex.name,
                    exercise_key=ex.exercise_key,
                    sets_reps="",
                    tm_info="",
                    is_main_lift=ex.is_main_lift,
                )
            )
            created += 1
    db.commit()
    return {
        "status": "ok",
        "week_start": week_start,
        "week_end": week_end,
        "created": created,
        "updated": updated,
    }


@app.patch(
    "/api/admin/weekly-trend-snapshot/{snapshot_id}",
    response_model=schemas.WeeklyTrendSnapshotOut,
    dependencies=[Depends(require_secret)],
)
def patch_weekly_trend_snapshot(
    snapshot_id: int, payload: schemas.WeeklyTrendPatch, db: Session = Depends(get_db)
):
    """Edycja pojedynczego wiersza 'weekly_trend_snapshots' - albo komorki
    wykonania (Obciazenie=tm_info i/lub Serie x powtorzenia=sets_reps,
    uzywane przez edytowalne pola w zakladce Trend, zapis on blur), albo
    tozsamosci wiersza (name/day/day_order/position - reczna korekta
    literowki/kolejnosci, dodane 2026-07-13, zeby nie trzeba bylo uzywac
    pelnego resetu tygodnia POST .../manual tylko po to, zeby poprawic jedna
    nazwe). Ten sam naglowek X-Auth-Secret co POST /api/entries. Wysylamy
    tylko pole, ktore sie zmienilo (None = bez zmian), zeby jeden zapis nie
    nadpisal reszty wiersza pustymi/domyslnymi wartosciami. Zmienia
    WYLACZNIE wskazany wiersz {snapshot_id} - inne wiersze/tygodnie
    nietkniete."""
    row = (
        db.query(models.WeeklyTrendSnapshot)
        .filter(models.WeeklyTrendSnapshot.id == snapshot_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Nie ma wiersza trendu o tym id")
    if payload.sets_reps is not None:
        row.sets_reps = payload.sets_reps
    if payload.tm_info is not None:
        row.tm_info = payload.tm_info
    if payload.name is not None:
        row.name = payload.name
    if payload.day is not None:
        row.day = payload.day
    if payload.day_order is not None:
        row.day_order = payload.day_order
    if payload.position is not None:
        row.position = payload.position
    if payload.exercise_key is not None:
        row.exercise_key = payload.exercise_key
    db.commit()
    db.refresh(row)
    return row


@app.delete(
    "/api/admin/weekly-trend-snapshot/{snapshot_id}",
    dependencies=[Depends(require_secret)],
)
def delete_weekly_trend_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    """Kasuje POJEDYNCZY wiersz 'weekly_trend_snapshots' po id - do sprzatania
    'osieroconych' wierszy sprzed wdrozenia exercise_key (2026-07-14): rename
    cwiczenia w seed_data.py PRZED ta migracja tworzyl NOWY wiersz zamiast
    aktualizowac stary (bo dopasowanie szlo po (week_start, day, name), a
    nazwa sie zmienila), wiec w historycznych tygodniach zostaly duplikaty -
    stara nazwa (bez exercise_key, dane juz przepisane recznie do nowego,
    kluczowanego wiersza) obok nowej. Nie rusza innych wierszy/tygodni.
    Uzyj GET /api/weekly-trend, zeby najpierw znalezc {id} do skasowania."""
    row = (
        db.query(models.WeeklyTrendSnapshot)
        .filter(models.WeeklyTrendSnapshot.id == snapshot_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Nie ma wiersza trendu o tym id")
    db.delete(row)
    db.commit()
    return {"status": "ok", "deleted_id": snapshot_id}


@app.post(
    "/api/admin/weekly-trend-snapshot/manual",
    dependencies=[Depends(require_secret)],
)
def create_weekly_trend_snapshot_manual(
    payload: schemas.WeeklyTrendManualPayload, db: Session = Depends(get_db)
):
    """Reczny odpowiednik POST /api/admin/weekly-trend-snapshot - zamiast
    kopiowac AKTUALNY stan tabeli 'exercises' (dziala tylko dla biezacego
    tygodnia), przyjmuje w body gotowy zestaw wierszy (day/name/sets_reps/
    tm_info/...) dla DOWOLNEGO week_start/week_end podanego przez wywolujacego.

    Uzywane przez backend/seed_trend.py, zeby Pawel mogl uzupelnic/skorygowac
    zakladke 'Trend' za tygodnie sprzed wdrozenia automatycznego zrzutu, albo
    poprawic tydzien, ktory z jakiegos powodu nie zostal zarchiwizowany na
    czas - dane przepisuje recznie z gym/logs/archiwum.md w repo mozgu.

    Upsert po week_start: kasuje istniejace wiersze tego tygodnia i wstawia
    nowe z payloadu (identyczna logika jak w automatycznym endpoincie) -
    bezpiecznie wywolac ponownie dla tego samego tygodnia, np. przy korekcie."""
    db.query(models.WeeklyTrendSnapshot).filter(
        models.WeeklyTrendSnapshot.week_start == payload.week_start
    ).delete()

    for row in payload.exercises:
        db.add(
            models.WeeklyTrendSnapshot(
                week_start=payload.week_start,
                week_end=payload.week_end,
                day=row.day,
                day_order=row.day_order,
                position=row.position,
                name=row.name,
                exercise_key=row.exercise_key,
                sets_reps=row.sets_reps,
                tm_info=row.tm_info,
                is_main_lift=row.is_main_lift,
            )
        )
    db.commit()
    return {
        "status": "ok",
        "week_start": payload.week_start,
        "week_end": payload.week_end,
        "count": len(payload.exercises),
    }


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
    """Kasuje cwiczenia - uzywane przez seed_data.py do usuwania wierszy,
    ktore zostaly wykreslone z listy EXERCISES. Gdy ref.exercise_key jest
    podany, dopasowanie idzie po (day, exercise_key) (spojnie z seed_plan()),
    w przeciwnym razie po (day, name) jak dotychczas. Kasuje tez powiazane
    wpisy Entry (historia zapas/uwagi tego cwiczenia znika razem z nim - to
    swiadome, "prawdziwe" kasowanie, nie tylko ukrycie wiersza)."""
    deleted, not_found = 0, []
    for ref in payload.exercises:
        exercise = None
        if ref.exercise_key:
            exercise = (
                db.query(models.Exercise)
                .filter(
                    models.Exercise.day == ref.day,
                    models.Exercise.exercise_key == ref.exercise_key,
                )
                .first()
            )
        if not exercise:
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
