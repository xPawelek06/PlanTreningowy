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
        sets_reps="3 x 3 (S3 = AMRAP, min. 3)",
        tm_info=(
            # Tydzien cyklu 2/4 (2026-07-13), TM 105 kg, schemat 70/80/90% TM
            "Rozgrzewka: pusta sztanga x5, 60 kg x5\n"
            "S1: 72,5 kg x3\n"
            "S2: 85 kg x3\n"
            "S3: 95 kg x3+"
        ),
        is_main_lift=False,  # Pawel poprosil o zwykly tekst bez pogrubienia (2026-07-05)
    ),
    dict(
        day="Poniedziałek", day_order=0, position=1,
        name="Bułgary", sets_reps="3 x 10 / noga",
        tm_info="24kg",
    ),
    dict(
        day="Poniedziałek", day_order=0, position=2,
        name="RDL (lekko)", sets_reps="3 x 10",
        tm_info=(
            "Rozgrzewka: pusta sztanga x5, 40 kg x5\n"
            "S1: 60 kg x10\n"
            "S2: 70 kg x10\n"
            "S3: 80 kg x10"
        ),
    ),
    dict(day="Poniedziałek", day_order=0, position=3, name="Pallof Press", sets_reps="3 x 60 sek"),
    dict(day="Poniedziałek", day_order=0, position=4, name="Hollow Hold", sets_reps="3 x 60 sek"),
    dict(
        day="Poniedziałek", day_order=0, position=5,
        name="Uginanie ramion ze sztangą/hantlami", sets_reps="3 x 10",
        tm_info=(
                 "S1: 30kg\n"
                 "S2: 40kg\n"
                 "S3: 45kg\n")
    ),  # Dodane 2026-07-07 - propozycja kolegi Pawla, dzien z najmniejsza liczba cwiczen

    # WTOREK - Wyciskanie plaskie
    dict(
        day="Wtorek", day_order=1, position=0,
        name="Wyciskanie płaskie",
        sets_reps="3 x 3 (S3 = AMRAP, min. 3)",
        tm_info=(
            # Tydzien cyklu 2/4 (2026-07-13), TM 80 kg (bez zmian), schemat 70/80/90% TM
            "Rozgrzewka: pusta sztanga x5, 40 kg x5\n"
            "S1: 56,25 kg x3\n"
            "S2: 63,75 kg x3\n"
            "S3: 72,5 kg x3+"
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
        name="Wiosłowanie wąskie na maszynie", sets_reps="3 x 10",
        tm_info=(
            "40 kg\n"
        ),
    ),  # Doprecyzowany chwyt 2026-07-07 (drugie wioslowanie w piatek - waskie)
    dict(day="Wtorek", day_order=1, position=3, name="Prostowanie ramion wyciąg", sets_reps="3 x 10", tm_info="35 kg"),
    dict(day="Wtorek", day_order=1, position=4, name="Rozpiętki hantle w opadzie", sets_reps="3 x 10", tm_info="8 kg"),

    # SRODA - Bieg 10 km
    dict(day="Środa", day_order=2, position=0, name="Bieg 10 km", sets_reps="~50 min (cel 40 min)"),
    dict(day="Środa", day_order=2, position=1, name="Mobilność bioder / kostek", sets_reps="10–15 min"),
    dict(day="Środa", day_order=2, position=2, name="Superman Hold", sets_reps="3 x 45 sek"),

    # CZWARTEK - Kalistenika core
    dict(
        day="Czwartek", day_order=3, position=0,
        name="Dragon Flag + Hollow Body Rocks", sets_reps="4 serie",
        tm_info=(
            "Dragon Flag: 4 x 3\n"
            "Hollow Body Rocks: 4 x 30 sek\n"
        ),
    ),
    dict(day="Czwartek", day_order=3, position=1, name="Wznosy kolan w zwisie", sets_reps="3 x 10"),
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
        sets_reps="3 x 3 (S3 = AMRAP, min. 3)",
        tm_info=(
            # Tydzien cyklu 2/4 (2026-07-13), TM 125 kg, schemat 70/80/90% TM
            "Rozgrzewka: pusta sztanga x5, 75 kg x5\n"
            "S1: 87,5 kg x3\n"
            "S2: 100 kg x3\n"
            "S3: 112,5 kg x3+"
        ),
        is_main_lift=False,  # Pawel poprosil o zwykly tekst bez pogrubienia (jak inne glowne boje)
    ),
    dict(
        day="Piątek", day_order=4, position=1,
        name="Dipy",
        sets_reps="3 serie",
        tm_info=(
            "Rozgrzewka: pusto, 15kg x5\n"
            "S1: +30 kg x5\n"
            "S2: +35 kg x5\n"
            "S3: +40 kg x3"
        ),
    ),  # TM=45 kg dociazenia; zaokraglenie w gore co 2,5 kg (najmniejszy talerz na pas do dipow), wartosci S1/S2/S3 podane przez Pawla
    dict(
        day="Piątek", day_order=4, position=2,
        name="Superseria:\n"
             "Podciąganie na drążku\n"
             "Nordic Curls",
        sets_reps="Podciąganie: 3 x 12\n"
                  "Nordic Curls: 3 x 6",
        tm_info="Bez dociążenia — 3x12: cel\n"
                "Nordic - 3x6 pełny wyprost: cel",
    ),
    dict(
        day="Piątek", day_order=4, position=3,
        name="Wiosłowanie szerokie", sets_reps="3 x 10",
        tm_info=("50kg")
    ),
    dict(
        day="Piątek", day_order=4, position=4,
        name="Superseria:\n"
             "Spacer farmera\n"
             "Zginanie nadgarstków",
        sets_reps="Spacer: 3 x 20 sek\n"
                  "Zginanie: 3 x 15",
        tm_info="Spacer: 15 kg / ręka\n"
                "Zginanie: 30kg",
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
