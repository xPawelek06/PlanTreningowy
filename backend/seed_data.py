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
    # PONIEDZIALEK - Gora ciala (A) - sila & handstand focus
    # Kolumny sets_reps / tm_info moga zawierac znaki nowej linii (\n) -
    # frontend renderuje kazdy fragment jako osobna linie (czytelny breakdown).
    #
    # exercise_key: staly identyfikator cwiczenia, niezalezny od "name" -
    # dzieki niemu zmiana "name" ponizej to zwykly rename (main.py.seed_plan
    # robi upsert po day+exercise_key), a nie nowy wiersz, wiec historia w
    # zakladce Trend sie nie urywa. Nadawany recznie - przy DODAWANIU nowego
    # cwiczenia wymysl nowy, nigdy niepowtarzajacy sie klucz (np.
    # "pon-nazwa-cwiczenia"); NIE zmieniaj juz istniejacego klucza przy
    # zwyklym rename nazwy (o to wlasnie chodzi).
    dict(
        day="Poniedziałek", day_order=0, position=0,
        name="Wall Handstand Hold",
        exercise_key="pon-handstand-hold",
        sets_reps="3 x 20-30 sek (10-12 min praktyki przed właściwym treningiem)",
        tm_info="Start: 20-30 sek, +5-10 sek/tydz. — kolejny etap: Free Handstand (czwartek)",
    ),
    dict(
        day="Poniedziałek", day_order=0, position=1,
        name="Negatywy HSPU przy ścianie",
        exercise_key="pon-hspu-negatywy",
        sets_reps="3 x 3-5 powt.",
        tm_info="Opuszczanie 4-5 sek. — etap przed pełnym HSPU",
    ),
    dict(
        day="Poniedziałek", day_order=0, position=2,
        name="Podciąganie z dociążeniem w plecaku",
        exercise_key="pon-podciaganie-dociazone",
        sets_reps="4 x 6-8 powt.",
        tm_info="Start: +5-10 kg w plecaku (baza: 10 czystych podciągnięć bez obciążenia)",
    ),
    dict(
        day="Poniedziałek", day_order=0, position=3,
        name="Pompki z nogami na podwyższeniu (dociążone)",
        exercise_key="pon-pompki-nogi-podwyzszenie",
        sets_reps="4 x 8-10 powt.",
        tm_info="Start: +10 kg w plecaku (na uchwytach)",
    ),
    dict(
        day="Poniedziałek", day_order=0, position=4,
        name="Pompki Pseudo Planche",
        exercise_key="pon-pompki-pseudo-planche",
        sets_reps="3 x 8-10 powt.",
        tm_info="Bez dociążenia — nowy wariant, najpierw technika (dłonie przy biodrach, ciało wychylone w przód)",
    ),
    dict(
        day="Poniedziałek", day_order=0, position=5,
        name="Dragon Flag",
        exercise_key="pon-dragon-flag",
        sets_reps="4 serie: 1-2 pełne powt. + 3-4 negatywy",
        tm_info="Ostrożnie — silnie angażuje lędźwie, przerwij przy jakimkolwiek bólu",
    ),

    # WTOREK - Dol ciala + Core (A)
    dict(
        day="Wtorek", day_order=1, position=0,
        name="Przysiady bułgarskie z dociążeniem",
        exercise_key="wt-bulgarskie-dociazone",
        sets_reps="4 x 8-10 / nogę",
        tm_info="Sesja testowa — dobierz ciężar w plecaku (zapas 2-3 powt. na ostatniej serii)",
    ),
    dict(
        day="Wtorek", day_order=1, position=1,
        name="Pistol Squats",
        exercise_key="wt-pistol-squats",
        sets_reps="3 x 5-8 / nogę",
        tm_info="Bodyweight — do potwierdzenia w 1. sesji, jeśli za łatwe: dociążenie plecakiem",
    ),
    dict(
        day="Wtorek", day_order=1, position=2,
        name="Single-leg Hip Thrust",
        exercise_key="wt-single-leg-hip-thrust",
        sets_reps="3 x 12 powt. (pauza 2 sek. na górze)",
        tm_info="Sesja testowa",
    ),
    dict(
        day="Wtorek", day_order=1, position=3,
        name="Wspięcia na palce na jednej nodze",
        exercise_key="wt-wspiecia-jedna-noga",
        sets_reps="4 x 15-20 powt.",
        tm_info="Sesja testowa",
    ),
    dict(
        day="Wtorek", day_order=1, position=4,
        name="Ab Wheel (kółko)",
        exercise_key="wt-ab-wheel",
        sets_reps="4 x 10-12 powt.",
        tm_info="Ostrożnie — silnie angażuje lędźwie, niepełny zakres na start",
    ),

    # SRODA - Bieg 10 km (twardy) + regeneracja
    dict(day="Środa", day_order=2, position=0, name="Bieg 10 km", exercise_key="sr-bieg-10km", sets_reps="~50 min (cel 40 min)"),
    dict(day="Środa", day_order=2, position=1, name="Mobilność bioder / kostek", exercise_key="sr-mobilnosc-bioder-kostek", sets_reps="10–15 min"),

    # CZWARTEK - Gora ciala (B) - objetosc & ruchy unilateralne
    dict(
        day="Czwartek", day_order=3, position=0,
        name="Free Handstand",
        exercise_key="cz-free-handstand",
        sets_reps="10 min praktyki",
        tm_info="Wolno, bez ściany — kolejny etap po Wall Handstand Hold (poniedziałek)",
    ),
    dict(
        day="Czwartek", day_order=3, position=1,
        name="Pike Push-ups na uchwytach",
        exercise_key="cz-pike-pushups",
        sets_reps="4 x 8-10 powt.",
        tm_info="Nogi na podwyższeniu — sesja testowa",
    ),
    dict(
        day="Czwartek", day_order=3, position=2,
        name="Podciąganie powolne",
        exercise_key="cz-podciaganie-powolne",
        sets_reps="4 x 8 powt.",
        tm_info="1 sek. góra / 2 sek. pauza / 3 sek. dół",
    ),
    dict(
        day="Czwartek", day_order=3, position=3,
        name="Pompki Archer na uchwytach",
        exercise_key="cz-pompki-archer",
        sets_reps="4 x 6-8 / stronę",
        tm_info="Bez dociążenia — wariant unilateralny",
    ),
    dict(
        day="Czwartek", day_order=3, position=4,
        name="Uginanie ramion w zwisie na drążku",
        exercise_key="cz-uginanie-ramion-zwis",
        sets_reps="3 x 8-10 powt.",
        tm_info="Uwaga na lewy nadgarstek — jeśli wróci ból, zamienić ćwiczenie",
    ),
    dict(
        day="Czwartek", day_order=3, position=5,
        name="Dragon Flag",
        exercise_key="cz-dragon-flag",
        sets_reps="3 serie x max negatywów kontrolowanych do dołu",
        tm_info="Ostrożnie — lędźwie, przerwij przy jakimkolwiek bólu",
    ),

    # PIATEK - Dol ciala + Core (B)
    dict(
        day="Piątek", day_order=4, position=0,
        name="Zakroki chodzone z dociążeniem",
        exercise_key="pt-zakroki-chodzone",
        sets_reps="4 x 10-12 / nogę",
        tm_info="Sesja testowa — dobierz ciężar w plecaku (zapas 2-3 powt.)",
    ),
    dict(
        day="Piątek", day_order=4, position=1,
        name="Cossack Squats",
        exercise_key="pt-cossack-squats",
        sets_reps="3 x 10 / stronę",
        tm_info="Sesja testowa",
    ),
    dict(
        day="Piątek", day_order=4, position=2,
        name="Uginanie nóg w leżeniu (ślizg stopami)",
        exercise_key="pt-uginanie-nog-slizg",
        sets_reps="3 x 10-12 powt.",
        tm_info="Sesja testowa — ręcznik/panele jako ślizg",
    ),
    dict(
        day="Piątek", day_order=4, position=3,
        name="Ab Wheel (kółko)",
        exercise_key="pt-ab-wheel",
        sets_reps="4 x 12-15 powt.",
        tm_info="Ostrożnie — lędźwie, niepełny zakres na start",
    ),

    # SOBOTA - Gora ciala (C, opcjonalnie/technika) + Bieg latwy
    dict(
        day="Sobota", day_order=5, position=0,
        name="Stanie na rękach — próby",
        exercise_key="sob-handstand-proby",
        sets_reps="15 min, wolna przestrzeń",
        tm_info="Opcjonalnie/technika",
    ),
    dict(
        day="Sobota", day_order=5, position=1,
        name="L-Sit na uchwytach",
        exercise_key="sob-l-sit",
        sets_reps="3 serie x max czas",
        tm_info="Sesja testowa (cel na start: 5-8 sek.)",
    ),
    dict(
        day="Sobota", day_order=5, position=2,
        name="Pompki klasyczne w wolnym tempie",
        exercise_key="sob-pompki-klasyczne",
        sets_reps="3 serie",
        tm_info="Sesja testowa",
    ),
    dict(
        day="Sobota", day_order=5, position=3,
        name="Bieg łatwy",
        exercise_key="sob-bieg-latwy",
        sets_reps="30–40 min (tempo konwersacyjne)",
    ),

    # NIEDZIELA - Regeneracja (Rest): pelny odpoczynek, brak cwiczen w planie.
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
