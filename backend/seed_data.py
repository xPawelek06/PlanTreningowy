"""Dane planu (kalistenika, od 2026-09-22) + skrypt wysylajacy je do API.

Uzycie:
    API_BASE=http://127.0.0.1:8000 APP_SECRET=PlanTreningowy python seed_data.py
    API_BASE=https://plan.130-61-86-177.sslip.io APP_SECRET=PlanTreningowy python seed_data.py

Ten plik jest tez "zrodlem prawdy" do reczszej edycji, gdy trener-personalny
aktualizuje plan po tygodniu progresji - edytuj liste EXERCISES i uruchom
ponownie skrypt przeciwko produkcyjnemu API_BASE (seed_plan robi upsert po
day+exercise_key, wiec bezpiecznie nadpisuje tylko zmienione pola).

WAZNE: samo "git push" NIE aktualizuje zakladki Plan/Trend na stronie - ten
plik to tylko dane w repo, trzeba go faktycznie URUCHOMIC (jak wyzej) przeciwko
dzialajacemu API, zeby zmiany trafily do bazy (Neon). Backend na Oracle VM sam
w sobie nic z tego pliku nie czyta przy starcie/deployu.

ZMIANA 2026-09-22 (pivot z trojboju na kalistenike): Pawel wstrzymal trojboj
19.08 (bol plecow) i zdecydowal sie na kalistenike domowa jako NOWY, staly
kierunek (nie tymczasowy blok) - patrz core/decyzje.md i gym/progresja.md
("Blok Kalistenika") w repo mozgu. Cala 31-cwiczeniowa lista trojboju + Trend
zostaly zarchiwizowane w gym/archiwum/trojboj-plan-i-trend-2026-09-22.md i
skasowane z appki PRZED wdrozeniem tego pliku. Zakladka "Regeneracja"
(plan_group="regeneracja", blok Upper/Lower/FBW na czas bolu plecow) zostala
CALKOWICIE usunieta (dane, UI, backend/seed_data_regen.py) - plan_group tego
(jedynego juz) planu zostaje technicznie "trojboj" (nazwa historyczna, patrz
models.py), zeby nie trzeba bylo przepisywac wszystkich domyslnych wartosci
w schemas.py/main.py bez realnej korzysci (nigdzie nie jest pokazywana w UI).

Rename cwiczenia (zmiana "name" przy tym samym exercise_key): main() ponizej,
oprocz upsertu planu, wywoluje tez POST /api/admin/weekly-trend-snapshot - to
synchronizuje tozsamosc (name/day_order/position) wiersza w BIEZACYM (jeszcze
niearchiwizowanym) tygodniu zakladki Trend z dopasowaniem po exercise_key,
wiec zmiana nazwy tutaj + jedno uruchomienie tego skryptu wystarcza, zeby
rename byl widoczny wszedzie (Plan i biezacy tydzien Trendu) - bez recznej
edycji Neon. Historyczne (juz zarchiwizowane) tygodnie Trendu NIE sa tym
ruszane (to swiadomie zamrozniete zapisy przeszlosci) - do korekty starej
nazwy w danym tygodniu sluzy backend/patch_trend_row.py.
"""

import os

import requests

API_BASE = os.environ.get("API_BASE", "http://127.0.0.1:8000")
APP_SECRET = os.environ.get("APP_SECRET", "PlanTreningowy")

EXERCISES = [
    # BLOK ROZLUZNIAJACY DNO MIEDNICY od 2026-11-18 (4-6 tyg.), zrodlo:
    # gym/plan-tygodniowy.md w repo mozgu. Pelny plan kalisteniki sprzed bloku:
    # gym/archiwum/plan-kalistenika-2026-11-przed-blokiem-rozluzniajacym.md
    # (oraz historia git tego pliku, commit 3123db2).
    #
    # exercise_key: staly identyfikator cwiczenia, niezalezny od "name"
    # (upsert po day+exercise_key). Cwiczenie zostajace w tym samym dniu
    # zachowuje stary klucz (ciaglosc Trendu); przeniesione na inny dzien
    # lub nowe dostaje nowy klucz. Kolumny sets_reps / tm_info moga zawierac znak nowej linii.

    # PONIEDZIALEK - Gora ciala (A)
    dict(
        day="Poniedziałek", day_order=0, position=0,
        name="Podciąganie",
        exercise_key="pon-podciaganie-dociazone",
        sets_reps='4 x 6-8 powt.',
        tm_info='Blok rozluźniający od 2026-11-18: bez plecaka, 2-3 powt. zapasu, wydech w fazie wysiłku',
    ),
    dict(
        day="Poniedziałek", day_order=0, position=1,
        name="Pompki z nogami na podwyższeniu",
        exercise_key="pon-pompki-nogi-podwyzszenie",
        sets_reps='3 x 10-12 powt.',
        tm_info='Bez plecaka',
    ),
    dict(
        day="Poniedziałek", day_order=0, position=2,
        name="Pike Push-ups",
        exercise_key="pon-pike-pushups",
        sets_reps='3 x 8 powt.',
        tm_info='Nogi na podwyższeniu, bez uchwytów',
    ),
    dict(
        day="Poniedziałek", day_order=0, position=3,
        name="Podciąganie australijskie (niski drążek)",
        exercise_key="pon-podciaganie-australijskie",
        sets_reps='3 x 10-12 powt.',
        tm_info='Bez pauzy przy drążku. Uwaga na lewy nadgarstek',
    ),
    dict(
        day="Poniedziałek", day_order=0, position=4,
        name="Odwrotne rozpiętki w leżeniu na brzuchu (Y-T)",
        exercise_key="pon-odwrotne-rozpietki-lezenie",
        sets_reps='3 x 12-15 powt.',
        tm_info='Butelki 1 l, kciuki w górę, bez szarpania',
    ),
    dict(
        day="Poniedziałek", day_order=0, position=5,
        name="Zestaw rozluźniający (po treningu)",
        exercise_key="pon-rozluznianie",
        sets_reps='Nogi na kanapie/łóżku (90/90, kolana lekko na boki) 4-5 min\nMotyl leżący, kolana na poduszkach 3 min\nPozycja dziecka z poduszką pod pośladkami 1,5-3 min',
        tm_info='Oddech przeponowy: wdech nosem 4 s do brzucha, wydech ustami 6-8 s, krocze opada i puszcza. Bez parcia, bez Kegla',
    ),

    # WTOREK - Dol ciala (A)
    dict(
        day="Wtorek", day_order=1, position=0,
        name="Zakroki w tył",
        exercise_key="wt-zakroki-w-tyl",
        sets_reps='3 x 10 / nogę',
        tm_info='Bez plecaka, kontrolowane',
    ),
    dict(
        day="Wtorek", day_order=1, position=1,
        name="Step-upy na podwyższenie",
        exercise_key="wt-step-upy",
        sets_reps='3 x 10-12 / nogę',
        tm_info='Bez plecaka',
    ),
    dict(
        day="Wtorek", day_order=1, position=2,
        name="Glute Bridge obunóż",
        exercise_key="wt-glute-bridge",
        sets_reps='3 x 12 powt.',
        tm_info='Bez ściskania pośladków na górze',
    ),
    dict(
        day="Wtorek", day_order=1, position=3,
        name="Wspięcia na palce na jednej nodze",
        exercise_key="wt-wspiecia-jedna-noga",
        sets_reps='3 x 15-20 powt.',
        tm_info='Bez plecaka',
    ),
    dict(
        day="Wtorek", day_order=1, position=4,
        name="Dead Bug",
        exercise_key="wt-dead-bug",
        sets_reps='3 x 8 / stronę',
        tm_info='Mały zakres nóg, swobodny oddech',
    ),
    dict(
        day="Wtorek", day_order=1, position=5,
        name="Zestaw rozluźniający (po treningu)",
        exercise_key="wt-rozluznianie",
        sets_reps='Nogi na kanapie/łóżku (90/90, kolana lekko na boki) 4-5 min\nMotyl leżący, kolana na poduszkach 3 min\nPozycja dziecka z poduszką pod pośladkami 1,5-3 min',
        tm_info='Oddech przeponowy: wdech nosem 4 s do brzucha, wydech ustami 6-8 s, krocze opada i puszcza. Bez parcia, bez Kegla',
    ),

    # SRODA - Marszobieg + mobilnosc
    dict(
        day="Środa", day_order=2, position=0,
        name="Marszobieg",
        exercise_key="sr-marszobieg",
        sets_reps='25-30 min: 4 min wolnego truchtu + 1 min marszu',
        tm_info='Pierwsze 2 tyg. Brak pogorszenia wieczorem → ciągły łatwy bieg. Pogorszenie → 2 tyg. samych szybkich marszów',
    ),
    dict(
        day="Środa", day_order=2, position=1,
        name="Mobilność bioder",
        exercise_key="sr-mobilnosc-bioder-kostek",
        sets_reps='10 min',
    ),
    dict(
        day="Środa", day_order=2, position=2,
        name="Zestaw rozluźniający (po treningu)",
        exercise_key="sr-rozluznianie",
        sets_reps='Nogi na kanapie/łóżku (90/90, kolana lekko na boki) 4-5 min\nMotyl leżący, kolana na poduszkach 3 min\nPozycja dziecka z poduszką pod pośladkami 1,5-3 min',
        tm_info='Oddech przeponowy: wdech nosem 4 s do brzucha, wydech ustami 6-8 s, krocze opada i puszcza. Bez parcia, bez Kegla',
    ),

    # CZWARTEK - Gora ciala (B)
    dict(
        day="Czwartek", day_order=3, position=0,
        name="Podciąganie podchwytem",
        exercise_key="cz-podciaganie-podchwyt",
        sets_reps='3 x 6-8 powt.',
        tm_info='Bez plecaka',
    ),
    dict(
        day="Czwartek", day_order=3, position=1,
        name="Pompki Archer na uchwytach",
        exercise_key="cz-pompki-archer",
        sets_reps='3 x 6 / stronę',
    ),
    dict(
        day="Czwartek", day_order=3, position=2,
        name="Pompki diamentowe",
        exercise_key="cz-pompki-diamentowe",
        sets_reps='3 x 10 powt.',
        tm_info='Bez plecaka, łokcie przy tułowiu',
    ),
    dict(
        day="Czwartek", day_order=3, position=3,
        name="Podciąganie powolne",
        exercise_key="cz-podciaganie-powolne",
        sets_reps='3 x 5 powt.',
        tm_info='Bez pauzy u góry',
    ),
    dict(
        day="Czwartek", day_order=3, position=4,
        name="Zestaw rozluźniający (po treningu)",
        exercise_key="cz-rozluznianie",
        sets_reps='Nogi na kanapie/łóżku (90/90, kolana lekko na boki) 4-5 min\nMotyl leżący, kolana na poduszkach 3 min\nPozycja dziecka z poduszką pod pośladkami 1,5-3 min',
        tm_info='Oddech przeponowy: wdech nosem 4 s do brzucha, wydech ustami 6-8 s, krocze opada i puszcza. Bez parcia, bez Kegla',
    ),

    # PIATEK - Dol ciala (B)
    dict(
        day="Piątek", day_order=4, position=0,
        name="Przysiady z masą ciała",
        exercise_key="pt-przysiady-bw",
        sets_reps='3 x 15 powt.',
        tm_info='Płynny ruch',
    ),
    dict(
        day="Piątek", day_order=4, position=1,
        name="Single-leg Hip Thrust",
        exercise_key="pt-single-leg-hip-thrust",
        sets_reps='3 x 10 / nogę',
        tm_info='Bez pauzy na górze',
    ),
    dict(
        day="Piątek", day_order=4, position=2,
        name="Uginanie nóg w leżeniu (ślizg stopami)",
        exercise_key="pt-uginanie-nog-slizg",
        sets_reps='3 x 10 powt.',
    ),
    dict(
        day="Piątek", day_order=4, position=3,
        name="Wspięcia na palce na jednej nodze",
        exercise_key="pt-wspiecia-jedna-noga",
        sets_reps='3 x 15 powt.',
        tm_info='Bez plecaka',
    ),
    dict(
        day="Piątek", day_order=4, position=4,
        name="Bird Dog",
        exercise_key="pt-bird-dog",
        sets_reps='3 x 8 / stronę',
        tm_info='Swobodny oddech',
    ),
    dict(
        day="Piątek", day_order=4, position=5,
        name="Zestaw rozluźniający (po treningu)",
        exercise_key="pt-rozluznianie",
        sets_reps='Nogi na kanapie/łóżku (90/90, kolana lekko na boki) 4-5 min\nMotyl leżący, kolana na poduszkach 3 min\nPozycja dziecka z poduszką pod pośladkami 1,5-3 min',
        tm_info='Oddech przeponowy: wdech nosem 4 s do brzucha, wydech ustami 6-8 s, krocze opada i puszcza. Bez parcia, bez Kegla',
    ),

    # SOBOTA - Bieg latwy
    dict(
        day="Sobota", day_order=5, position=0,
        name="Bieg łatwy",
        exercise_key="sob-bieg-latwy",
        sets_reps='25-30 min (marszobieg albo łatwy trucht)',
        tm_info='Tempo konwersacyjne, zasady jak w środę',
    ),
    dict(
        day="Sobota", day_order=5, position=1,
        name="Zestaw rozluźniający (po treningu)",
        exercise_key="sob-rozluznianie",
        sets_reps='Nogi na kanapie/łóżku (90/90, kolana lekko na boki) 4-5 min\nMotyl leżący, kolana na poduszkach 3 min\nPozycja dziecka z poduszką pod pośladkami 1,5-3 min',
        tm_info='Oddech przeponowy: wdech nosem 4 s do brzucha, wydech ustami 6-8 s, krocze opada i puszcza. Bez parcia, bez Kegla',
    ),

    # NIEDZIELA - Odpoczynek: brak wierszy (zestaw rozluzniajacy wieczorem
    # opisany statycznie w index.html).
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
    # zeby niepelny plik nie skasowal calych dni przez pomylke. Niedziela
    # (rest day, brak cwiczen) jest wiec swiadomie NIETKNIETA tym krokiem -
    # ewentualne stare wiersze Niedzieli trzeba usunac recznie (przez
    # DELETE /api/admin/exercises), tak jak zrobiono to jednorazowo przy
    # wdrozeniu kalisteniki 2026-09-22.
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
    # wpisanego postepu, tylko aktualizuje name/day_order/position tam, gdzie
    # exercise_key sie zgadza. To domyka petle "zmien nazwe w seed_data.py ->
    # uruchom skrypt -> gotowe" takze dla Trendu, bez potrzeby recznej edycji
    # Neon.
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
