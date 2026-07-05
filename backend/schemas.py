from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class EntryCreate(BaseModel):
    exercise_id: int
    zapas: Optional[str] = None
    uwagi: Optional[str] = None
    entry_date: Optional[date] = None


class EntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    exercise_id: int
    entry_date: date
    zapas: Optional[str]
    uwagi: Optional[str]
    created_at: datetime


class ExerciseOut(BaseModel):
    id: int
    day: str
    day_order: int
    position: int
    name: str
    sets_reps: str
    tm_info: Optional[str]
    is_main_lift: bool
    latest_zapas: Optional[str] = None
    latest_uwagi: Optional[str] = None
    latest_entry_date: Optional[date] = None


class ExerciseSeed(BaseModel):
    day: str
    day_order: int
    position: int
    name: str
    sets_reps: str
    tm_info: Optional[str] = None
    is_main_lift: bool = False


class SeedPayload(BaseModel):
    exercises: List[ExerciseSeed]


class ExerciseRef(BaseModel):
    day: str
    name: str


class DeletePayload(BaseModel):
    exercises: List[ExerciseRef]
