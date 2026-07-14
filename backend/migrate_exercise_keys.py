"""JEDNORAZOWY skrypt migracji DANYCH: backfill kolumny exercise_key dla
istniejacych wierszy w tabelach 'exercises' i 'weekly_trend_snapshots'.

NIE URUCHAMIAJ TEGO SKRYPTU BEZ WYRAZNEJ ZGODY PAWLA/GLOWNEGO ASYSTENTA.

Kontekst (2026-07-14): dodalismy staly identyfikator cwiczenia
(exercise_key, patrz models.py) niezalezny od wyswietlanej nazwy, zeby rename
w seed_data.py przestal rwac historie w zakladce Trend. Kolumna juz istnieje
w schemacie (main.py.migrate_schema() dodaje ja automatycznie jako pusta,
nullable) - ten skrypt to OSOBNY, recznie odpalany krok, ktory wypelnia ja
dla wierszy, ktore juz sa w bazie (obecny tydzien w 'exercises' +
wszystkie dotychczasowe zrzuty w 'weekly_trend_snapshots').

Mapowanie NAME_KEY_MAP nizej jest wyliczane automatycznie z aktualnej
zawartosci backend/seed_data.py (EXERCISES) - zeby nie duplikowac/rozjezdzac
dwoch zrodel prawdy. Dopasowanie idzie po (day, name):
  - Dla tabeli 'exercises' to praktycznie pewne trafienie (aktualny plan i
    aktualny seed_data.py powinny miec te same nazwy - jesli nie, patrz
    "unmatched" w wyjsciu skryptu).
  - Dla 'weekly_trend_snapshots' to PRZYBLIZENIE: jesli cwiczenie bylo
    kiedys przemianowane W PRZESZLOSCI (przed wprowadzeniem exercise_key),
    starsze tygodnie z dawna nazwa NIE zostana polaczone z nowsza - to
    oczekiwane ograniczenie (nie da sie tego cofnac automatycznie, tylko
    reczna korekta przez PATCH /api/admin/weekly-trend-snapshot/{id}).
    Sprawdz liste "unmatched" w wyjsciu i zdecyduj, czy warto to recznie
    dopisac do NAME_KEY_MAP ponizej przed uruchomieniem (dodajac dawna nazwe
    jako dodatkowy klucz mapujacy na ten sam exercise_key).

PRZED URUCHOMIENIEM NA PRODUKCJI (Neon):
  1. Przejrzyj NAME_KEY_MAP (wydrukuje sie na starcie) i upewnij sie, ze
     wygenerowane klucze sa tym, czego chcesz - to JEDNORAZOWA operacja,
     pozniejsza zmiana klucza wymaga recznej korekty wierszy.
  2. Rozwaz backup / punkt przywracania w konsoli Neon (branch albo
     point-in-time restore) na wypadek pomylki.
  3. Najpierw przetestuj na lokalnym sqlite (bez ustawionego DATABASE_URL -
     patrz database.py, domyslnie "sqlite:///./local.db").

Uzycie (PO zatwierdzeniu):
    python migrate_exercise_keys.py              # lokalny sqlite, do testu
    DATABASE_URL=<connection string Neon> python migrate_exercise_keys.py
"""

import models
from database import SessionLocal
from seed_data import EXERCISES

# (day, name) -> exercise_key, wyliczone z aktualnego seed_data.py.
NAME_KEY_MAP = {
    (item["day"], item["name"]): item["exercise_key"]
    for item in EXERCISES
    if item.get("exercise_key")
}


def backfill(db, model, label):
    rows = db.query(model).filter(model.exercise_key.is_(None)).all()
    updated = 0
    unmatched = set()
    for row in rows:
        key = NAME_KEY_MAP.get((row.day, row.name))
        if key:
            row.exercise_key = key
            updated += 1
        else:
            unmatched.add((row.day, row.name))
    print(f"{label}: {updated} zaktualizowanych, {len(unmatched)} bez dopasowania")
    return unmatched


def main():
    print(f"NAME_KEY_MAP ({len(NAME_KEY_MAP)} wpisow):")
    for (day, name), key in sorted(NAME_KEY_MAP.items()):
        print(f"  ({day!r}, {name!r}) -> {key!r}")

    db = SessionLocal()
    try:
        unmatched_exercises = backfill(db, models.Exercise, "exercises")
        unmatched_snapshots = backfill(db, models.WeeklyTrendSnapshot, "weekly_trend_snapshots")
        db.commit()

        all_unmatched = unmatched_exercises | unmatched_snapshots
        if all_unmatched:
            print("\nUWAGA - brak dopasowania w NAME_KEY_MAP dla (day, name):")
            for day, name in sorted(all_unmatched):
                print(f"  {day!r}, {name!r}")
            print(
                "Te wiersze zostaly BEZ exercise_key (nullable) - dopisz je recznie "
                "do NAME_KEY_MAP i uruchom ponownie (idempotentne, filtruje po "
                "exercise_key IS NULL), albo popraw je pojedynczo przez "
                "PATCH /api/admin/weekly-trend-snapshot/{id} / ponowny seed_data.py."
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()
