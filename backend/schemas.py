from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class EntryCreate(BaseModel):
    exercise_id: int
    zapas: Optional[str] = None
    seria_plus: Optional[str] = None
    uwagi: Optional[str] = None
    entry_date: Optional[date] = None


class EntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    exercise_id: int
    entry_date: date
    zapas: Optional[str]
    seria_plus: Optional[str]
    uwagi: Optional[str]
    created_at: datetime


class ExerciseOut(BaseModel):
    id: int
    day: str
    day_order: int
    position: int
    name: str
    exercise_key: Optional[str] = None
    sets_reps: str
    tm_info: Optional[str]
    is_main_lift: bool
    latest_zapas: Optional[str] = None
    latest_seria_plus: Optional[str] = None
    latest_uwagi: Optional[str] = None
    latest_entry_date: Optional[date] = None


class ExerciseSeed(BaseModel):
    day: str
    day_order: int
    position: int
    name: str
    # Staly identyfikator cwiczenia (patrz models.Exercise.exercise_key) -
    # opcjonalny na razie (wiersze sprzed migracji go nie maja), ale
    # seed_data.py od 2026-07-14 wysyla go dla kazdego cwiczenia. Gdy podany,
    # main.py.seed_plan() upsertuje po (day, exercise_key) zamiast (day, name),
    # wiec zmiana "name" przy tym samym kluczu to rename, nie nowy wiersz.
    exercise_key: Optional[str] = None
    sets_reps: str
    tm_info: Optional[str] = None
    is_main_lift: bool = False


class SeedPayload(BaseModel):
    exercises: List[ExerciseSeed]


class ExerciseRef(BaseModel):
    day: str
    name: str
    # Opcjonalny - gdy podany, delete_exercises w main.py dopasowuje po
    # (day, exercise_key) zamiast (day, name), spojnie z seed_plan().
    exercise_key: Optional[str] = None


class DeletePayload(BaseModel):
    exercises: List[ExerciseRef]


class WeeklyTrendSnapshotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    week_start: date
    week_end: date
    day: str
    day_order: int
    position: int
    name: str
    exercise_key: Optional[str] = None
    sets_reps: str
    tm_info: Optional[str]
    is_main_lift: bool
    created_at: datetime


class WeeklyTrendRow(BaseModel):
    day: str
    day_order: int
    position: int
    name: str
    exercise_key: Optional[str] = None
    sets_reps: str
    tm_info: Optional[str] = None
    is_main_lift: bool = False


class WeeklyTrendManualPayload(BaseModel):
    """Body dla POST /api/admin/weekly-trend-snapshot/manual - reczne
    wpisanie/korekta zrzutu trendu dla DOWOLNEGO (najczesciej przeszlego)
    tygodnia, patrz backend/seed_trend.py."""

    week_start: date
    week_end: date
    exercises: List[WeeklyTrendRow]


class WeeklyTrendPatch(BaseModel):
    """Body dla PATCH /api/admin/weekly-trend-snapshot/{id} - edycja
    pojedynczego wiersza 'weekly_trend_snapshots'. Dwa pierwsze pola
    (sets_reps/tm_info) to komorki wypelniane z telefonu (Obciazenie/Serie x
    powtorzenia); reszta (name/day/day_order/position/exercise_key) to reczna
    korekta TOZSAMOSCI wiersza (literowka w nazwie, zla kolejnosc, recznie
    dopisany staly klucz cwiczenia) - name/day/day_order/position dodane
    2026-07-13, exercise_key dodane 2026-07-14 (patrz
    backend/migrate_exercise_keys.py), zeby nie trzeba bylo uzywac pelnego
    resetu tygodnia (POST .../manual) tylko po to, zeby poprawic jedna nazwe
    albo dopisac klucz recznie. Wszystkie pola opcjonalne - wysylamy tylko to,
    co sie zmienilo; None = nie dotykaj tego pola (odroznione od pustego
    stringa, ktory swiadomie czysci pole)."""

    sets_reps: Optional[str] = None
    tm_info: Optional[str] = None
    name: Optional[str] = None
    day: Optional[str] = None
    day_order: Optional[int] = None
    position: Optional[int] = None
    exercise_key: Optional[str] = None
