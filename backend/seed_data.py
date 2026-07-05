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
        name="Bułgary", sets_reps="3 x 8–10 / noga",
        tm_info="S1: 24 kg x8 / noga\nS2: 24 kg x9 / noga\nS3: 24 kg x10 / noga",
    ),
    dict(
        day="Poniedziałek", day_order=0, position=2,
        name="RDL (lekko)", sets_reps="3 x 10",
        tm_info=(
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
        name="Wyciskanie hantli skos górny", sets_reps="3 x 8",
        tm_info=(
            "20 kg / hantla\n"
        ),
    ),
    dict(
        day="Wtorek", day_order=1, position=2,
        name="Wiosłowanie sztangą", sets_reps="3 x 8",
        tm_info=(
            "40 kg\n"
        ),
    ),
    dict(
        day="Wtorek", day_order=1, position=3,
        name="Dipy (dociążone)",
        sets_reps="3 x 5 (S3 = AMRAP, min. 5)",
        tm_info=(
            "Rozgrzewka: dociążenie +20 kg x5, +27,5 kg x5\n"
            "S1: +30 kg x5\n"
            "S2: +35 kg x5\n"
            "S3: +40 kg x5+"
        ),
    ),  # TM=45 kg dociazenia; zaokraglenie w gore co 2,5 kg (najmniejszy talerz na pas do dipow), wartosci S1/S2/S3 podane przez Pawla
    dict(day="Wtorek", day_order=1, position=4, name="Prostowanie ramion wyciąg", sets_reps="3 x 12", tm_info="40 kg"),
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
        ),
    ),
    dict(day="Czwartek", day_order=3, position=1, name="Wznosy nóg/kolan w zwisie", sets_reps="3 x 10"),
    dict(day="Czwartek", day_order=3, position=2, name="Shoulder Taps", sets_reps="3 x 20"),
    dict(day="Czwartek", day_order=3, position=3, name="Plank", sets_reps="3 x 60 sek"),
    dict(day="Czwartek", day_order=3, position=4, name="Mobilność bioder + lędźwie", sets_reps="10–15 min"),

    # PIATEK - Martwy ciag
    # Kolejnosc cwiczen zmieniona 2026-07-05: Nordic Curls (hamstringi, mala
    # obciazenie ledzwi) wstawione MIEDZY Martwy a RDL, zeby dac ledzwiom bufor
    # zanim przyjdzie druga praca w zawiasie biodrowym - patrz uzasadnienie
    # w wiadomosci do Pawla (historia kontuzji + swiezy powrot do martwego).
    dict(
        day="Piątek", day_order=4, position=0,
        name="Martwy ciąg",
        sets_reps="3 x 5 (S3 = AMRAP, min. 5)",
        tm_info=(
            "Rozgrzewka: pusta sztanga x5, 47,5 kg x5, 70 kg x5\n"
            "S1: 77,5 kg x5\n"
            "S2: 87,5 kg x5\n"
            "S3: 100 kg x5+"
        ),
        is_main_lift=False,  # Pawel poprosil o zwykly tekst bez pogrubienia (jak inne glowne boje)
    ),
    dict(day="Piątek", day_order=4, position=1, name="Nordic Curls", sets_reps="3 x 6"),
    dict(
        day="Piątek", day_order=4, position=3,
        name="Spacer farmera", sets_reps="3 x 20 sek",
        tm_info="15 kg / ręka",
    ),
    dict(
        day="Piątek", day_order=4, position=4,
        name="Podciąganie na drążku", sets_reps="3 x 12",
        tm_info="Bez dociążenia — pod ilość",
    ),
    dict(
        day="Piątek", day_order=4, position=5,
        name="Zginanie nadgarstków za plecami", sets_reps="3 x 15",
        tm_info="30 kg",
    ),

    # SOBOTA - Bieg latwy
    dict(day="Sobota", day_order=5, position=0, name="Bieg łatwy", sets_reps="30–40 min"),
    dict(day="Sobota", day_order=5, position=2, name="Chest-to-wall Handstand Hold", sets_reps="3 x 30 sek"),
    dict(day="Sobota", day_order=5, position=1, name="Rozciąganie całego ciała", sets_reps="20–30 min"),

    # NIEDZIELA - Kalistenika vertical push
    dict(day="Niedziela", day_order=6, position=0, name="HSPU przy ścianie", sets_reps="4 x 4"),
    dict(day="Niedziela", day_order=6, position=1, name="Frog Stand", sets_reps="4 x 60 sek"),
    dict(day="Niedziela", day_order=6, position=2, name="Pike Push-ups", sets_reps="3 x 10"),
    dict(day="Niedziela", day_order=6, position=3, name="Toes to Bar", sets_reps="3 x 10"),
]


def main():
    # 1. Upsert wszystkiego, co jest na liscie EXERCISES (jak dotychczas).
    resp = requests.post(
        f"{API_BASE}/api/admin/seed",
        json={"exercises": EXERCISES},
        headers={"X-Auth-Secret": APP_SECRET},
        timeout=30,
    )
    resp.raise_for_status()
    print("seed:", resp.json())

    # 2. Usun "osierocone" wiersze: te, ktore sa w bazie dla dni obecnych w
    # EXERCISES, ale nie ma ich juz na liscie (np. Pawel usunal linie z pliku).
    # Celowo NIE ruszamy dni, ktorych w tym przebiegu w ogole nie ma na liscie -
    # zeby niepelny plik nie skasowal calych dni przez pomylke.
    days_in_file = {item["day"] for item in EXERCISES}
    names_in_file = {(item["day"], item["name"]) for item in EXERCISES}

    plan_resp = requests.get(f"{API_BASE}/api/plan", timeout=30)
    plan_resp.raise_for_status()
    current_plan = plan_resp.json()

    orphaned = [
        {"day": ex["day"], "name": ex["name"]}
        for ex in current_plan
        if ex["day"] in days_in_file and (ex["day"], ex["name"]) not in names_in_file
    ]

    if not orphaned:
        print("brak osieroconych wierszy do usuniecia")
        return

    print("usuwam osierocone wiersze:", orphaned)
    del_resp = requests.delete(
        f"{API_BASE}/api/admin/exercises",
        json={"exercises": orphaned},
        headers={"X-Auth-Secret": APP_SECRET},
        timeout=30,
    )
    del_resp.raise_for_status()
    print("delete:", del_resp.json())


if __name__ == "__main__":
    main()
