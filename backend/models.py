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
    # Staly identyfikator cwiczenia, niezalezny od wyswietlanej nazwy (np.
    # "pon-przysiad"), nadawany recznie przez Pawla w seed_data.py. Dodane
    # 2026-07-14, zeby rename nazwy w seed_data.py byl zwyklym UPDATE (upsert
    # po day+exercise_key), a historia w zakladce Trend (weekly_trend_snapshots)
    # sie nie urywala przy zmianie nazwy - patrz main.py seed_plan().
    # Nullable, bo istniejace wiersze nie maja go jeszcze wypelnionego (czeka
    # na zatwierdzona migracje danych, patrz backend/migrate_exercise_keys.py).
    exercise_key = Column(String, nullable=True, index=True)
    sets_reps = Column(String, nullable=False)
    tm_info = Column(String, nullable=True)  # None dla cwiczen pomocniczych bez TM
    is_main_lift = Column(Boolean, default=False, nullable=False)
    # Rozroznienie planow w tej samej tabeli (dodane 2026-08-20, blok
    # Upper/Lower/FBW na czas bolu plecow - patrz backend/seed_data_regen.py):
    # "trojboj" (domyslny, dotychczasowy plan) vs "regeneracja" (nowy,
    # tymczasowy blok). Wszystkie zapytania/upserty w main.py sa scope'owane
    # PO TEJ KOLUMNIE (day+exercise_key+plan_group / day+name+plan_group), wiec
    # dwa plany moga bezpiecznie uzywac tych samych nazw dni ("Poniedzialek"
    # itd.) bez ryzyka wzajemnego nadpisania/skasowania. Nullable, bo istniejace
    # (produkcyjne) wiersze go nie maja - migrate_schema() w main.py dodaje
    # kolumne i backfilluje NULL -> "trojboj" (wszystkie dotychczasowe wiersze
    # sa trojbojem), wiec efektywnie nigdy nie jest NULL po starcie backendu.
    plan_group = Column(String, nullable=True, index=True)

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


class WeeklyTrendSnapshot(Base):
    """Trwaly zrzut per tydzien: day/day_order/position/name/is_main_lift
    ustala TOZSAMOSC wiersza (kopiowane z 'exercises' przez POST
    /api/admin/weekly-trend-snapshot w main.py, PRZED cotygodniowym DELETE
    /api/admin/entries). Pole 'postep' to WOLNY tekst, ktory Pawel wpisuje
    recznie z telefonu (PATCH /api/admin/weekly-trend-snapshot/{id}) - NIE
    kopia zaplanowanego schematu z 'exercises'. Nowy wiersz startuje z
    pustym postep ("").

    ZMIANA 2026-09-22 (pivot z trojboju na kalistenike, patrz
    gym/progresja.md "Blok Kalistenika" w repo mozgu Pawla): dawniej byly tu
    DWIE kolumny (sets_reps="Serie x powtorzenia" / tm_info="Obciazenie"),
    sensowne przy trojboju (ciezar sztangi + schemat serii). Kalistenika nie
    ma jednego sztywnego wzorca postepu (czas, powtorzenia, wariant
    cwiczenia, dociazenie...), wiec Pawel chcial JEDNO wolne pole tekstowe
    zamiast wymuszonego podzialu - stad ta migracja scalila obie kolumny w
    'postep' (patrz main.py migrate_schema(), ktora przy tej okazji
    skasowala CALA dotychczasowa historie tabeli - byla juz zarchiwizowana
    w repo mozgu, gym/archiwum/trojboj-plan-i-trend-2026-09-22.md).

    Tabela 'exercises' trzyma tylko AKTUALNY plan (nadpisywany co cykl przez
    seed_data.py), a 'entries' jest czyszczona co tydzien - zadna z nich nie
    daje appce trwalej historii. Ten wzorzec jest analogiczny do WeeklySummary
    w appce Waga: zanim dane biezacego tygodnia znikna, kopiujemy ich zrzut
    tutaj, zeby zakladka "Trend" mogla pokazac historie mimo czyszczenia."""

    __tablename__ = "weekly_trend_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    week_start = Column(Date, nullable=False)  # poniedzialek
    week_end = Column(Date, nullable=False)  # niedziela
    day = Column(String, nullable=False)
    day_order = Column(Integer, nullable=False)
    position = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    # Ten sam staly identyfikator co Exercise.exercise_key (kopiowany z
    # 'exercises' przy tworzeniu snapshotu) - pozwala pivotowi w script.js
    # dopasowywac wiersze miedzy tygodniami po (day, exercise_key) zamiast po
    # (day, name), wiec rename nazwy w seed_data.py juz nie urywa historii.
    # Nullable z tych samych powodow co Exercise.exercise_key.
    exercise_key = Column(String, nullable=True, index=True)
    # Wolne pole tekstowe na postep (patrz docstring klasy wyzej) - zastapilo
    # 2026-09-22 dawne sets_reps/tm_info.
    postep = Column(String, nullable=False, default="")
    is_main_lift = Column(Boolean, default=False, nullable=False)
    # Dyskryminator planu (patrz Exercise.plan_group) - kopiowany z
    # 'exercises' przy tworzeniu snapshotu. Od 2026-09-22 istnieje w praktyce
    # tylko jedna wartosc ("trojboj" - nazwa historyczna, technicznie oznacza
    # teraz JEDYNY, aktualny plan kalisteniczny; zakladka "Regeneracja" i jej
    # plan_group="regeneracja" zostaly calkowicie usuniete). Kolumna zostaje
    # (nullable) na wypadek, gdyby w przyszlosci znow pojawil sie drugi,
    # rownolegly plan.
    plan_group = Column(String, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
