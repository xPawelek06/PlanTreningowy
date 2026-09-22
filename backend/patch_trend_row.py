"""Reczna korekta POJEDYNCZEGO wiersza zakladki 'Trend' po id (literowka w
nazwie, zla kolejnosc/dzien) - bez ryzyka utraty danych innych wierszy, w
odroznieniu od seed_trend.py (ktory robi PELNY reset calego tygodnia).

Wywoluje PATCH /api/admin/weekly-trend-snapshot/{id} - patrz docstring tego
endpointu w main.py i schemas.WeeklyTrendPatch. Wszystkie pola opcjonalne;
podajesz tylko to, co chcesz zmienic (None/brak = bez zmian).

Zeby znalezc {id} wiersza - zobacz GET /api/weekly-trend (kazdy wiersz ma
"id").

Uzycie:
    1. Ustaw SNAPSHOT_ID i pola do zmiany w PATCH_FIELDS ponizej.
    2. Uruchom:
        API_BASE=http://127.0.0.1:8000 APP_SECRET=PlanTreningowy python patch_trend_row.py
        API_BASE=https://plan-treningowy-api.onrender.com APP_SECRET=PlanTreningowy python patch_trend_row.py
"""

import os

import requests

API_BASE = os.environ.get("API_BASE", "http://127.0.0.1:8000")
APP_SECRET = os.environ.get("APP_SECRET", "PlanTreningowy")

SNAPSHOT_ID = 0  # <- podmien na id wiersza z GET /api/weekly-trend

# Podaj tylko pola, ktore chcesz zmienic - reszta zostanie nietknieta.
PATCH_FIELDS = {
    # "name": "Poprawiona nazwa cwiczenia",
    # "day": "Poniedziałek",
    # "day_order": 0,
    # "position": 2,
    # "postep": "+7,5 kg, 4x7 (zapas 1 powt.)",  # 2026-09-22: jedno wolne pole (dawniej sets_reps/tm_info)
    # "exercise_key": "pon-przysiad",  # dodane 2026-07-14, patrz migrate_exercise_keys.py
}


def main():
    if not SNAPSHOT_ID:
        raise SystemExit("Ustaw SNAPSHOT_ID w patch_trend_row.py przed uruchomieniem")
    resp = requests.patch(
        f"{API_BASE}/api/admin/weekly-trend-snapshot/{SNAPSHOT_ID}",
        json=PATCH_FIELDS,
        headers={"X-Auth-Secret": APP_SECRET},
        timeout=30,
    )
    resp.raise_for_status()
    print(f"wiersz {SNAPSHOT_ID}:", resp.json())


if __name__ == "__main__":
    main()
