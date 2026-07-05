"""Dane planu (Tydzien 1 cyklu, 2026-07-05) + skrypt wysylajacy je do API.

Uzycie:
    API_BASE=http://127.0.0.1:8000 APP_SECRET=PlanTreningowy python seed_data.py
    API_BASE=https://<twoj-render-url> APP_SECRET=PlanTreningowy python seed_data.py

Ten plik jest tez "zrodlem prawdy" do reczszej edycji, gdy trener-personalny
aktualizuje TM/plan po nowym cyklu - edytuj liste EXERCISES i uruchom ponownie
skrypt przeciwko produkcyjnemu API_BASE (seed_plan robi upsert po day+name,
wiec bezpiecznie nadpisuje tylko zmienione pola).
"""

import os

import requests

API_BASE = os.environ.get("API_BASE", "http://127.0.0.1:8000")
APP_SECRET = os.environ.get("APP_SECRET", "PlanTreningowy")

EXERCISES = [
    # PONIEDZIALEK - Przysiad
    dict(
        day="Poniedziałek", day_order=0, position=0,
        name="Przysiad ze sztangą (główny bój)",
        sets_reps="3 x 5 (S3 = AMRAP, min. 5)",
        tm_info=(
            "Rozgrzewka: pusta sztanga x5, 40 kg x5, 57,5 kg x5 → "
            "S1: 62,5 kg x5, S2: 72,5 kg x5, S3: 82,5 kg x5+"
        ),
        is_main_lift=True,
    ),
    dict(day="Poniedziałek", day_order=0, position=1, name="Przysiad przedni LUB bułgarski", sets_reps="3 x 8–10 / nogę"),
    dict(day="Poniedziałek", day_order=0, position=2, name="RDL / Good Morning (lekko)", sets_reps="3 x 10"),
    dict(day="Poniedziałek", day_order=0, position=3, name="Pallof Press", sets_reps="3 x 45–60 sek"),
    dict(day="Poniedziałek", day_order=0, position=4, name="Hollow Hold", sets_reps="3 x 45–60 sek"),

    # WTOREK - Wyciskanie plaskie
    dict(
        day="Wtorek", day_order=1, position=0,
        name="Wyciskanie płaskie (główny bój)",
        sets_reps="3 x 5 (S3 = AMRAP, min. 5)",
        tm_info=(
            "Rozgrzewka: pusta sztanga x5, 32,5 kg x5, 48,75 kg x5 → "
            "S1: 52,5 kg x5, S2: 61,25 kg x5, S3: 68,75 kg x5+"
        ),
        is_main_lift=True,
    ),
    dict(day="Wtorek", day_order=1, position=1, name="Wyciskanie hantli skos górny", sets_reps="3 x 8–10"),
    dict(day="Wtorek", day_order=1, position=2, name="Wiosłowanie sztangą / hantlami", sets_reps="3 x 8–10"),
    dict(day="Wtorek", day_order=1, position=3, name="Dipy (dociążone)", sets_reps="3 x 8–10"),
    dict(day="Wtorek", day_order=1, position=4, name="Prostowanie ramion wyciąg", sets_reps="3 x 12–15"),
    dict(day="Wtorek", day_order=1, position=5, name="Rozpiętki hantle w opadzie", sets_reps="3 x 10"),

    # SRODA - Bieg 10 km
    dict(day="Środa", day_order=2, position=0, name="Bieg 10 km", sets_reps="~50 min (cel 40 min)"),
    dict(day="Środa", day_order=2, position=1, name="Mobilność bioder / kostek / Th", sets_reps="10–15 min"),
    dict(day="Środa", day_order=2, position=2, name="Superman Hold", sets_reps="3 x 45 sek"),

    # CZWARTEK - Kalistenika core
    dict(day="Czwartek", day_order=3, position=0, name="Dragon Flag + Hollow Body Rocks", sets_reps="4 serie"),
    dict(day="Czwartek", day_order=3, position=1, name="Wznosy nóg/kolan w zwisie", sets_reps="3–4 x 10–12"),
    dict(day="Czwartek", day_order=3, position=2, name="Shoulder Taps", sets_reps="3 x 20"),
    dict(day="Czwartek", day_order=3, position=3, name="Plank", sets_reps="3 x 60 sek"),
    dict(day="Czwartek", day_order=3, position=4, name="Mobilność bioder + lędźwie", sets_reps="10–15 min"),

    # PIATEK - Martwy ciag
    dict(
        day="Piątek", day_order=4, position=0,
        name="Martwy ciąg (główny bój)",
        sets_reps="3 x 5 (S3 = AMRAP, min. 5)",
        tm_info=(
            "Rozgrzewka: pusta sztanga x5, 47,5 kg x5, 70 kg x5 → "
            "S1: 77,5 kg x5, S2: 87,5 kg x5, S3: 100 kg x5+"
        ),
        is_main_lift=True,
    ),
    dict(day="Piątek", day_order=4, position=1, name="Rumuński martwy ciąg (lekko)", sets_reps="3 x 8–10"),
    dict(day="Piątek", day_order=4, position=2, name="Nordic Curls", sets_reps="3 x 6"),
    dict(day="Piątek", day_order=4, position=3, name="Spacer farmera", sets_reps="3 x 40–45 sek"),
    dict(day="Piątek", day_order=4, position=4, name="Podciąganie na drążku", sets_reps="3 x 8–10"),
    dict(day="Piątek", day_order=4, position=5, name="Przedramiona / chwyt", sets_reps="3 x 8 / stronę"),

    # SOBOTA - Bieg latwy
    dict(day="Sobota", day_order=5, position=0, name="Bieg łatwy", sets_reps="30–40 min"),
    dict(day="Sobota", day_order=5, position=1, name="Rozciąganie całego ciała", sets_reps="20–30 min"),
    dict(day="Sobota", day_order=5, position=2, name="Chest-to-wall Handstand Hold", sets_reps="3 x 30 sek"),

    # NIEDZIELA - Kalistenika vertical push
    dict(day="Niedziela", day_order=6, position=0, name="HSPU przy ścianie", sets_reps="4 x 5–8"),
    dict(day="Niedziela", day_order=6, position=1, name="Frog Stand", sets_reps="4 serie"),
    dict(day="Niedziela", day_order=6, position=2, name="Pike Push-ups", sets_reps="3 x 10–12"),
    dict(day="Niedziela", day_order=6, position=3, name="Toes to Bar", sets_reps="3 x 10"),
]


def main():
    resp = requests.post(
        f"{API_BASE}/api/admin/seed",
        json={"exercises": EXERCISES},
        headers={"X-Auth-Secret": APP_SECRET},
        timeout=30,
    )
    resp.raise_for_status()
    print(resp.json())


if __name__ == "__main__":
    main()
