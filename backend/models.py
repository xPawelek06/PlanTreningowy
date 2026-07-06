from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class Exercise(Base):
    """Statyczna struktura planu: jeden wiersz = jedno cwiczenie w danym dniu.

    Aktualizowana przez POST /api/admin/seed, gdy trener zmienia plan/TM
    w silownia/plan-tygodniowy.md lub silownia/progresja.md.
    """

    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    day = Column(String, nullable=False)  # np. "Poniedziałek"
    day_order = Column(Integer, nullable=False)  # 0 = poniedzialek ... 6 = niedziela
    position = Column(Integer, nullable=False)  # kolejnosc cwiczenia w danym dniu
    name = Column(String, nullable=False)
    sets_reps = Column(String, nullable=False)
    tm_info = Column(String, nullable=True)  # None dla cwiczen pomocniczych bez TM
    is_main_lift = Column(Boolean, default=False, nullable=False)

    entries = relationship("Entry", back_populates="exercise")


class Entry(Base):
    """Wpis Pawla z telefonu po treningu: zapas + uwagi dla danego cwiczenia.

    Kazdy zapis to NOWY wiersz (historia zachowana) - do wyswietlania bierzemy
    najnowszy wpis per cwiczenie, a do synchronizacji z silownia/dziennik/
    trener czyta cala historie przez GET /api/entries.
    """

    __tablename__ = "entries"

    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    entry_date = Column(Date, nullable=False)
    zapas = Column(String, nullable=True)
    seria_plus = Column(String, nullable=True)  # powtorzenia w ostatniej serii AMRAP (5+/3+/1+)
    uwagi = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    exercise = relationship("Exercise", back_populates="entries")
