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
    # Kolumny sets_reps / tm_info moga zawierac znaki nowej linii (\n) - frontend
    # renderuje kazdy fragment jako osobna linie (czytelny breakdown per seria).
    dict(
        day="Poniedziałek", day_order=0, position=0,
        name="Przysiad ze sztangą",
        sets_reps="3 x 5 (S3 = AMRAP, min. 5)",
        tm_info=(
            "Rozgrzewka: pusta sztanga x5, 40 kg x5, 57,5 kg x5\n"
            "S1: 62,5 kg x5\n"
            "S2: 72,5 kg x5\n"
            "S3: 82,5 kg x5+"
        ),
        is_main_lift=False,  # Pawel poprosil o zwykly tekst bez pogrubienia (2026-07-05)
    ),
    dict(
        day="Poniedziałek", day_order=0, position=1,
        name="Bułgary", sets_reps="3 x 8–10 / nogę",
        tm_info="S1: 24 kg x8 / nogę\nS2: 24 kg x9 / nogę\nS3: 24 kg x10 / nogę",
    ),
    dict(
        day="Poniedziałek", day_order=0, position=2,
        name="RDL (lekko)", sets_reps="3 x 10",
        tm_info=(
            "Pierwszy raz z tym ćwiczeniem — dobierz S3 wg samopoczucia po S2\n"
            "Rozgrzewka: pusta sztanga x5, 40 kg x5\n"
            "S1: 60 kg x10\n"
            "S2: 70 kg x10\n"
            "S3: 80 kg x10 (jeśli S2 lekko) / 70 kg x10 (jeśli S2 ciężko)"
        ),
    ),
    dict(day="Poniedziałek", day_order=0, position=3, name="Pallof Press", sets_reps="3 x 45–60 sek", tm_info="S1: 45 sek\nS2: 50 sek\nS3: 60 sek"),
    dict(day="Poniedziałek", day_order=0, position=4, name="Hollow Hold", sets_reps="3 x 45–60 sek", tm_info="S1: 45 sek\nS2: 50 sek\nS3: 60 sek"),

    # WTOREK - Wyciskanie plaskie
    dict(
        day="Wtorek", day_order=1, position=0,
        name="Wyciskanie płaskie",
        sets_reps="3 x 5 (S3 = AMRAP, min. 5)",
        tm_info=(
            "Rozgrzewka: pusta sztanga x5, 32,5 kg x5, 47,5 kg x5\n"
            "S1: 52,5 kg x5\n"
            "S2: 60 kg x5\n"
            "S3: 67,5 kg x5+"
        ),
        is_main_lift=False,  # Pawel poprosil o zwykly tekst bez pogrubienia (jak Przysiad w Pon.)
    ),
    dict(
        day="Wtorek", day_order=1, position=1,
        name="Wyciskanie hantli skos górny", sets_reps="3 x 8–10",
        tm_info=(
            "Punkt startowy (dawno nie robione) — do korekty po 1. podejściu\n"
            "20 kg / hantla x8–10\n"
            "Priorytet: kontrola łokci (patrz Wiosłowanie), nie ciężar"
        ),
    ),
    dict(
        day="Wtorek", day_order=1, position=2,
        name="Wiosłowanie sztangą", sets_reps="3 x 8–10",
        tm_info=(
            "Punkt startowy (pierwszy powrót po długiej przerwie) — do korekty po 1. podejściu\n"
            "40 kg x8–10\n"
            "Priorytet: neutralny kręgosłup / technika, nie ciężar"
        ),
    ),
    dict(
        day="Wtorek", day_order=1, position=3,
        name="Dipy (dociążone)",
        sets_reps="3 x 5 (S3 = AMRAP, min. 5)",
        tm_info=(
            "Rozgrzewka: dociążenie +17,5 kg x5, +27,5 kg x5\n"
            "S1: +28,75 kg x5\n"
            "S2: +33,75 kg x5\n"
            "S3: +38,75 kg x5+"
        ),
    ),  # TM=45 kg dociazenia (max +50 kg x 0,9), formalny wave potwierdzony przez Pawla
    dict(day="Wtorek", day_order=1, position=4, name="Prostowanie ramion wyciąg", sets_reps="3 x 12–15", tm_info="40 kg"),
    dict(day="Wtorek", day_order=1, position=5, name="Rozpiętki hantle w opadzie", sets_reps="3 x 10", tm_info="8 kg"),

    # SRODA - Bieg 10 km
    dict(day="Środa", day_order=2, position=0, name="Bieg 10 km", sets_reps="~50 min (cel 40 min)"),
    dict(day="Środa", day_order=2, position=1, name="Mobilność bioder / kostek / Th", sets_reps="10–15 min"),
    dict(day="Środa", day_order=2, position=2, name="Superman Hold", sets_reps="3 x 45 sek"),

    # CZWARTEK - Kalistenika core
    dict(
        day="Czwartek", day_order=3, position=0,
        name="Dragon Flag + Hollow Body Rocks", sets_reps="4 serie",
        tm_info=(
            "Dragon Flag: 3 powt. (pełny wyprost i powrót) / serię\n"
            "Hollow Body Rocks: 30 sek / serię\n"
            "Utrwalamy ten sam poziom co ostatnio (już blisko granicy) — progres przy kolejnym powrocie"
        ),
    ),
    dict(day="Czwartek", day_order=3, position=1, name="Wznosy nóg/kolan w zwisie", sets_reps="3 x 10"),
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
