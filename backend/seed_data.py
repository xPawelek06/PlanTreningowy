"""Dane planu (Tydzien 1 cyklu, 2026-07-05) + skrypt wysylajacy je do API.

Uzycie:
    API_BASE=http://127.0.0.1:8000 APP_SECRET=PlanTreningowy python seed_data.py
    API_BASE=https://<twoj-render-url> APP_SECRET=PlanTreningowy python seed_data.py

Ten plik jest tez "zrodlem prawdy" do reczszej edycji, gdy trener-personalny
aktualizuje TM/plan po nowym cyklu - edytuj liste EXERCISES i uruchom ponownie
skrypt przeciwko produkcyjnemu API_BASE (seed_plan robi upsert po day+name,
wiec bezpiecznie nadpisuje tylko zmienione pola).

WAZNE: samo "git push" NIE aktualizuje zakladki Plan/Trend na stronie - ten
plik to tylko dane w repo, trzeba go faktycznie URUCHOMIC (jak wyzej) przeciwko
dzialajacemu API, zeby zmiany trafily do bazy (Neon). Backend na Renderze sam
w sobie nic z tego pliku nie czyta przy starcie/deployu.

Rename cwiczenia (zmiana "name" przy tym samym exercise_key, 2026-07-16): od
tego dnia main() ponizej, oprocz upsertu planu, wywoluje tez POST
/api/admin/weekly-trend-snapshot - to synchronizuje tozsamosc (name/day_order/
position) wiersza w BIEZACYM (jeszcze niearchiwizowanym) tygodniu zakladki
Trend z dopasowaniem po exercise_key, wiec zmiana nazwy tutaj + jedno
uruchomienie tego skryptu wystarcza, zeby rename byl widoczny wszedzie (Plan
i biezacy tydzien Trendu) - bez recznej edycji Neon. Historyczne (juz
zarchiwizowane) tygodnie Trendu NIE sa tym ruszane (to swiadomie zamrozniete
zapisy przeszlosci) - do korekty starej nazwy w danym tygodniu sluzy
backend/patch_trend_row.py.
"""

import os

import requests

API_BASE = os.environ.get("API_BASE", "http://127.0.0.1:8000")
APP_SECRET = os.environ.get("APP_SECRET", "PlanTreningowy")

EXERCISES = [
    # PONIEDZIALEK - Przysiad
    # Kolumny sets_reps / tm_info moga zawierac znaki nowej linii (\n) - frontend
    # renderuje kazdy fragment jako osobna linie (czytelny breakdown per seria).
    #
    # exercise_key (dodane 2026-07-14): staly identyfikator cwiczenia,
    # niezalezny od "name" - dzieki niemu zmiana "name" ponizej to zwykly
    # rename (main.py.seed_plan robi upsert po day+exercise_key), a nie nowy
    # wiersz, wiec historia w zakladce Trend sie nie urywa. Nadawany recznie -
    # przy DODAWANIU nowego cwiczenia wymysl nowy, nigdy niepowtarzajacy sie
    # klucz (np. "pon-nazwa-cwiczenia"); NIE zmieniaj juz istniejacego klucza
    # przy zwyklym rename nazwy (o to wlasnie chodzi).
    dict(
        day="Poniedziałek", day_order=0, position=0,
        name="Przysiad ze sztangą",
        exercise_key="pon-przysiad",
        sets_reps="Tydz. 3/4: 5/3/1+ (S3 = seria PR, max powt.)",
        tm_info=(
            # Tydzien cyklu 3/4 (2026-07-20), TM 105 kg (bez zmian), schemat 75/85/95% TM
            "Rozgrzewka: pusta sztanga x5, 60 kg x5\n"
            "S1: 80 kg x5\n"
            "S2: 90 kg x3\n"
            "S3: 100 kg x1+ (PR seria)"
        ),
        is_main_lift=False,  # Pawel poprosil o zwykly tekst bez pogrubienia (2026-07-05)
    ),
    dict(
        day="Poniedziałek", day_order=0, position=1,
        name="Bułgary", exercise_key="pon-bulgary", sets_reps="3 x 10 / noga",
        tm_info="24kg",
    ),
    dict(
        day="Poniedziałek", day_order=0, position=2,
        name="RDL (lekko)", exercise_key="pon-rdl", sets_reps="3 x 5",
        tm_info=(
            # Podniesione 2026-07-20 - 2. tydzien z rzedu "duzy zapas"
            "Rozgrzewka: pusta sztanga x5, 40 kg x5\n"
            "S1: 65 kg x5\n"
            "S2: 75 kg x5\n"
            "S3: 85 kg x5"
        ),
    ),
    dict(day="Poniedziałek", day_order=0, position=3, name="Pallof Press", exercise_key="pon-pallof-press", sets_reps="3 x 60 sek",
         tm_info=("Duże napięcie na gumie"
                  )
         ),
    dict(day="Poniedziałek", day_order=0, position=4, name="Hollow Hold", exercise_key="pon-hollow-hold", sets_reps="3 x 40 sek",
         tm_info=("Pełny wyprost"
                  )
         ),
    dict(
        day="Poniedziałek", day_order=0, position=5,
        name="Uginanie ramion ze sztangą/hantlami", exercise_key="pon-uginanie-ramion", sets_reps="3 x 10",
        tm_info=(
                 "30kg")
    ),  # Dodane 2026-07-07 - propozycja kolegi Pawla, dzien z najmniejsza liczba cwiczen

    # WTOREK - Wyciskanie plaskie
    dict(
        day="Wtorek", day_order=1, position=0,
        name="Wyciskanie płaskie",
        exercise_key="wt-wyciskanie-plaskie",
        sets_reps="Tydz. 3/4: 5/3/1+ (S3 = seria PR, max powt.)",
        tm_info=(
            # Tydzien cyklu 3/4 (2026-07-20), TM 80 kg (bez zmian), schemat 75/85/95% TM
            "Rozgrzewka: pusta sztanga x5, 40 kg x5\n"
            "S1: 60 kg x5\n"
            "S2: 67,5 kg x3\n"
            "S3: 75 kg x1+ (PR seria)"
        ),
        is_main_lift=False,  # Pawel poprosil o zwykly tekst bez pogrubienia (jak Przysiad w Pon.)
    ),
    dict(
        day="Wtorek", day_order=1, position=1,
        name="Wyciskanie sztangi skos górny", exercise_key="wt-wyciskanie-sztangi-skos", sets_reps="3 x 8",
        tm_info=(
            "50kg\n"
        ),
    ),
    dict(
        day="Wtorek", day_order=1, position=2,
        name="Wiosłowanie wąskie na maszynie", exercise_key="wt-wioslowanie-waskie", sets_reps="3 x 10",
        tm_info=(
            "40 kg\n"
        ),
    ),  # Doprecyzowany chwyt 2026-07-07 (drugie wioslowanie w piatek - waskie)
    dict(day="Wtorek", day_order=1, position=3, name="Prostowanie ramion wyciąg", exercise_key="wt-prostowanie-ramion", sets_reps="3 x 10", tm_info="40 kg"),  # Podniesione 2026-07-20 - komfortowy zapas, Pawel sam zapowiedzial ten skok
    dict(day="Wtorek", day_order=1, position=4, name="Rozpiętki hantle w opadzie", exercise_key="wt-rozpietki-hantle", sets_reps="3 x 10", tm_info="8 kg"),

    # SRODA - Bieg 10 km
    dict(day="Środa", day_order=2, position=0, name="Bieg 10 km", exercise_key="sr-bieg-10km", sets_reps="~50 min (cel 40 min)"),
    dict(day="Środa", day_order=2, position=1, name="Mobilność bioder / kostek", exercise_key="sr-mobilnosc-bioder-kostek", sets_reps="10–15 min"),
    dict(day="Środa", day_order=2, position=2, name="Superman Hold", exercise_key="sr-superman-hold", sets_reps="3 x 45 sek"),

    # CZWARTEK - Kalistenika core
    dict(
        day="Czwartek", day_order=3, position=0,
        name="Dragon Flag + Hollow Body Rocks", exercise_key="cz-dragon-flag-hollow-body", sets_reps="4 serie",
        tm_info=(
            "Dragon Flag: 4 x 3\n"
            "Hollow Body Rocks: 4 x 30 sek\n"
        ),
    ),
    dict(day="Czwartek", day_order=3, position=1, name="Wznosy kolan w zwisie", exercise_key="cz-wznosy-kolan", sets_reps="3 x 10"),
    dict(day="Czwartek", day_order=3, position=2, name="Shoulder Taps", exercise_key="cz-shoulder-taps", sets_reps="3 x 30"),
    dict(day="Czwartek", day_order=3, position=3, name="Plank", exercise_key="cz-plank", sets_reps="3 x 60 sek"),
    dict(day="Czwartek", day_order=3, position=4, name="Mobilność bioder + lędźwie", exercise_key="cz-mobilnosc-bioder-ledzwie", sets_reps="10–15 min"),

    # PIATEK - Martwy ciag
    # Kolejnosc cwiczen zmieniona 2026-07-05: Nordic Curls (hamstringi, mala
    # obciazenie ledzwi) wstawione MIEDZY Martwy a RDL, zeby dac ledzwiom bufor
    # zanim przyjdzie druga praca w zawiasie biodrowym - patrz uzasadnienie
    # w wiadomosci do Pawla (historia kontuzji + swiezy powrot do martwego).
    dict(
        day="Piątek", day_order=4, position=0,
        name="Martwy ciąg",
        exercise_key="pt-martwy-ciag",
        sets_reps="Tydz. 3/4: 5/3/1+ (S3 = seria PR, max powt.)",
        tm_info=(
            # Tydzien cyklu 3/4 (2026-07-20), TM 125 kg (bez zmian teraz), schemat 75/85/95% TM
            "Rozgrzewka: pusta sztanga x5, 75 kg x5\n"
            "S1: 95 kg x5\n"
            "S2: 107,5 kg x3\n"
            "S3: 120 kg x1+ (PR seria - sprawdz zaciski/rozwaz pasy, limiter zeszly tydzien byl chwyt)"
        ),
        is_main_lift=False,  # Pawel poprosil o zwykly tekst bez pogrubienia (jak inne glowne boje)
    ),
    dict(
        day="Piątek", day_order=4, position=1,
        name="Dipy",
        exercise_key="pt-dipy",
        sets_reps="3 serie",
        tm_info=(
            # Obnizone 2026-07-20 - 2. tydzien z rzedu tylko 2 powt. na +40 kg (Pawel sam to zaproponowal)
            "Rozgrzewka: pusto, 15kg x5\n"
            "S1: +30 kg x5\n"
            "S2: +35 kg x5\n"
            "S3: +35 kg x3"
        ),
    ),  # TM=45 kg dociazenia; zaokraglenie w gore co 2,5 kg (najmniejszy talerz na pas do dipow), wartosci S1/S2/S3 podane przez Pawla
    dict(
        day="Piątek", day_order=4, position=2,
        name="Superseria:\n"
             "Podciąganie na drążku\n"
             "Nordic Curls",
        exercise_key="pt-superseria-podciaganie-nordic",
        sets_reps="Podciąganie: 3 x 12\n"
                  "Nordic Curls: 3 x 6",
        tm_info="Bez dociążenia — 3x12: cel\n"
                "Nordic - 3x6 pełny wyprost: cel",
    ),
    dict(
        day="Piątek", day_order=4, position=3,
        name="Wiosłowanie szerokie", exercise_key="pt-wioslowanie-szerokie", sets_reps="3 x 10",
        tm_info=("50kg")
    ),
    dict(
        day="Piątek", day_order=4, position=4,
        name="Superseria:\n"
             "Spacer farmera\n"
             "Zginanie nadgarstków",
        exercise_key="pt-superseria-spacer-zginanie",
        sets_reps="Spacer: 3 x 20 sek\n"
                  "Zginanie: 3 x 15",
        tm_info="Spacer: 15 kg / ręka\n"
                "Zginanie: 30kg",
    ),

    # SOBOTA - Bieg latwy
    dict(day="Sobota", day_order=5, position=0, name="Bieg łatwy", exercise_key="sob-bieg-latwy", sets_reps="30–40 min"),
    dict(day="Sobota", day_order=5, position=2, name="Chest-to-wall Handstand Hold", exercise_key="sob-handstand-hold", sets_reps="3 x 30 sek"),
    dict(day="Sobota", day_order=5, position=1, name="Rozciąganie całego ciała", exercise_key="sob-rozciaganie", sets_reps="20–30 min"),

    # NIEDZIELA - Kalistenika vertical push
    dict(day="Niedziela", day_order=6, position=0, name="HSPU przy ścianie", exercise_key="ndz-hspu", sets_reps="4 x 4"),
    dict(day="Niedziela", day_order=6, position=1, name="Frog Stand", exercise_key="ndz-frog-stand", sets_reps="4 x 60 sek"),
    dict(day="Niedziela", day_order=6, position=2, name="Pike Push-ups", exercise_key="ndz-pike-pushups", sets_reps="3 x 10"),
    dict(day="Niedziela", day_order=6, position=3, name="Toes to Bar", exercise_key="ndz-toes-to-bar", sets_reps="3 x 10"),
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
    #
    # Dopasowanie po (day, exercise_key) gdy baza juz ma klucz wypelniony
    # (patrz backend/migrate_exercise_keys.py) - dzieki temu rename w pliku nie
    # jest mylnie brany za "usuniecie starej nazwy + dodanie nowej". Dla
    # wierszy bez klucza (przed zatwierdzeniem migracji) spada z powrotem na
    # dopasowanie po (day, name), jak dotychczas.
    days_in_file = {item["day"] for item in EXERCISES}
    keys_in_file = {
        (item["day"], item["exercise_key"]) for item in EXERCISES if item.get("exercise_key")
    }
    names_in_file = {(item["day"], item["name"]) for item in EXERCISES}

    plan_resp = requests.get(f"{API_BASE}/api/plan", timeout=30)
    plan_resp.raise_for_status()
    current_plan = plan_resp.json()

    def is_orphaned(ex):
        if ex["day"] not in days_in_file:
            return False
        if ex.get("exercise_key"):
            return (ex["day"], ex["exercise_key"]) not in keys_in_file
        return (ex["day"], ex["name"]) not in names_in_file

    orphaned = [
        {"day": ex["day"], "name": ex["name"], "exercise_key": ex.get("exercise_key")}
        for ex in current_plan
        if is_orphaned(ex)
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


def sync_trend_identity():
    # 3. Zsynchronizuj tozsamosc (name/day_order/position) BIEZACEGO tygodnia
    # zakladki Trend z planem, ktory wlasnie zseedowalismy - dzieki upsertowi
    # po exercise_key (main.py.create_weekly_trend_snapshot) to bezpieczne
    # wywolac za kazdym razem: nie dubluje wierszy, nie kasuje juz recznie
    # wpisanych sets_reps/tm_info, tylko aktualizuje name/day_order/position
    # tam, gdzie exercise_key sie zgadza. To domyka petle "zmien nazwe w
    # seed_data.py -> uruchom skrypt -> gotowe" takze dla Trendu, bez potrzeby
    # recznej edycji Neon.
    snap_resp = requests.post(
        f"{API_BASE}/api/admin/weekly-trend-snapshot",
        headers={"X-Auth-Secret": APP_SECRET},
        timeout=30,
    )
    snap_resp.raise_for_status()
    print("trend snapshot sync:", snap_resp.json())


if __name__ == "__main__":
    main()
    sync_trend_identity()
