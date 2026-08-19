"""Dane bloku "Regeneracja" (Upper/Lower/FBW, dodane 2026-08-20) + skrypt
wysylajacy je do API.

Kontekst: Pawel ma bol plecow (przysiad 2026-08-17, nie ustapil po kilku
dniach) i wstrzymal trojboj (przysiad ze sztanga / martwy ciag / RDL ciezkie)
na ok. 2 miesiace (do ok. 2026-10-19). Ten plik to ZUPELNIE ODDZIELNY,
tymczasowy plan na ten okres - zero cwiczen obciazajacych ledzwia. Pelne
uzasadnienie decyzji: core/decyzje.md (wpis 2026-08-19) w repo mozgu Pawla.

Izolacja od planu trojboju (patrz backend/seed_data.py, backend/models.py):
kazdy wiersz ma plan_group="regeneracja" - main.py scope'uje WSZYSTKIE
upserty/kasowania/snapshoty po (day, exercise_key/name, plan_group), wiec ten
skrypt nigdy nie dotyka wierszy plan_group="trojboj", nawet jesli dzien
("Poniedzialek" itd.) sie powtarza.

Uzycie (identyczne jak seed_data.py, tylko inny plik):
    API_BASE=http://127.0.0.1:8000 APP_SECRET=PlanTreningowy python seed_data_regen.py
    API_BASE=https://plan.136-113-151-64.sslip.io APP_SECRET=PlanTreningowy python seed_data_regen.py

WAZNE: samo "git push" NIE aktualizuje zakladki Regeneracja na stronie - trzeba
faktycznie URUCHOMIC ten skrypt przeciwko dzialajacemu API.
"""

import os

import requests

API_BASE = os.environ.get("API_BASE", "http://127.0.0.1:8000")
APP_SECRET = os.environ.get("APP_SECRET", "PlanTreningowy")

PLAN_GROUP = "regeneracja"

EXERCISES = [
    # PONIEDZIALEK - LOWER + Core
    dict(
        day="Poniedziałek", day_order=0, position=0,
        name="Przysiad z kettlem/hantlą (goblet squat)",
        exercise_key="regen-pon-goblet-squat",
        sets_reps="3 x 10",
        tm_info="Start: 16 kg",
    ),
    dict(
        day="Poniedziałek", day_order=0, position=1,
        name="Prostowanie nóg (maszyna)",
        exercise_key="regen-pon-prostowanie-nog",
        sets_reps="3 x 12",
        tm_info="Sesja testowa — dobierz ciężar na miejscu",
    ),
    dict(
        day="Poniedziałek", day_order=0, position=2,
        name="Zginanie nóg (maszyna)",
        exercise_key="regen-pon-zginanie-nog",
        sets_reps="3 x 10",
        tm_info="Sesja testowa",
    ),
    dict(
        day="Poniedziałek", day_order=0, position=3,
        name="Przysiad bułgarski",
        exercise_key="regen-pon-bulgarski",
        sets_reps="3 x 8 / noga",
        tm_info="Start: 16 kg",
    ),
    dict(
        day="Poniedziałek", day_order=0, position=4,
        name="Nordic Curls",
        exercise_key="regen-pon-nordic-curls",
        sets_reps="3 x 6",
        tm_info="Bodyweight",
    ),
    dict(
        day="Poniedziałek", day_order=0, position=5,
        name="Wspięcia na palce",
        exercise_key="regen-pon-wspiecia-palce",
        sets_reps="3 x 15",
        tm_info="Sesja testowa",
    ),
    dict(
        day="Poniedziałek", day_order=0, position=6,
        name="Pallof Press",
        exercise_key="regen-pon-pallof-press",
        sets_reps="3 x 12 / stronę",
    ),
    dict(
        day="Poniedziałek", day_order=0, position=7,
        name="Dead Bug",
        exercise_key="regen-pon-dead-bug",
        sets_reps="3 x 10 / stronę",
    ),

    # WTOREK - UPPER + Core
    dict(
        day="Wtorek", day_order=1, position=0,
        name="Wyciskanie płaskie",
        exercise_key="regen-wt-wyciskanie-plaskie",
        sets_reps="3 x 6",
        tm_info="Start: 70 kg",
    ),
    dict(
        day="Wtorek", day_order=1, position=1,
        name="Podciąganie na drążku",
        exercise_key="regen-wt-podciaganie",
        sets_reps="3 x 6",
        tm_info="Bodyweight (dociążenie, jeśli za łatwe)",
    ),
    dict(
        day="Wtorek", day_order=1, position=2,
        name="Wyciskanie hantli skos górny",
        exercise_key="regen-wt-wyciskanie-hantle-skos",
        sets_reps="3 x 8",
        tm_info="Sesja testowa",
    ),
    dict(
        day="Wtorek", day_order=1, position=3,
        name="Wiosłowanie hantlą jednorącz w podparciu",
        exercise_key="regen-wt-wioslowanie-jednoracz",
        sets_reps="3 x 10 / rękę",
        tm_info="Sesja testowa",
    ),
    dict(
        day="Wtorek", day_order=1, position=4,
        name="Wyciskanie hantli nad głowę siedząc",
        exercise_key="regen-wt-wyciskanie-nad-glowe",
        sets_reps="3 x 8",
        tm_info="Sesja testowa",
    ),
    dict(
        day="Wtorek", day_order=1, position=5,
        name="Uginanie ramion (hantle)",
        exercise_key="regen-wt-uginanie-ramion",
        sets_reps="3 x 10",
        tm_info="Start: 12 kg",
    ),
    dict(
        day="Wtorek", day_order=1, position=6,
        name="Prostowanie ramion na wyciągu",
        exercise_key="regen-wt-prostowanie-ramion",
        sets_reps="3 x 12",
        tm_info="Start: 40 kg",
    ),
    dict(
        day="Wtorek", day_order=1, position=7,
        name="Hollow Hold",
        exercise_key="regen-wt-hollow-hold",
        sets_reps="3 x 45 sek",
    ),

    # CZWARTEK - dom, kalistenika core & stabilizacja
    dict(
        day="Czwartek", day_order=3, position=0,
        name="Dragon Flag + Hollow Body Rocks",
        exercise_key="regen-cz-dragon-flag-hollow",
        sets_reps="4 serie",
    ),
    dict(
        day="Czwartek", day_order=3, position=1,
        name="Wznosy nóg/kolan w zwisie",
        exercise_key="regen-cz-wznosy-nog-kolan",
        sets_reps="3-4 x 10-12",
    ),
    dict(
        day="Czwartek", day_order=3, position=2,
        name="Shoulder Taps",
        exercise_key="regen-cz-shoulder-taps",
        sets_reps="3 x 20",
    ),
    dict(
        day="Czwartek", day_order=3, position=3,
        name="Bird Dog",
        exercise_key="regen-cz-bird-dog",
        sets_reps="3 x 10 / stronę",
    ),
    dict(
        day="Czwartek", day_order=3, position=4,
        name="Plank",
        exercise_key="regen-cz-plank",
        sets_reps="3 x 60 sek",
    ),

    # PIATEK - FBW + Core
    dict(
        day="Piątek", day_order=4, position=0,
        name="Leg Press (stopy wysoko i szeroko)",
        exercise_key="regen-pt-leg-press",
        sets_reps="3 x 10",
        tm_info="Sesja testowa",
    ),
    dict(
        day="Piątek", day_order=4, position=1,
        name="Dipy",
        exercise_key="regen-pt-dipy",
        sets_reps="3 x 8",
        tm_info="Bodyweight — bez dociążenia (ból nadgarstka, priorytet brak bólu)",
    ),
    dict(
        day="Piątek", day_order=4, position=2,
        name="Wiosłowanie na maszynie (wąski chwyt)",
        exercise_key="regen-pt-wioslowanie-waskie",
        sets_reps="3 x 10",
        tm_info="Start: 45 kg",
    ),
    dict(
        day="Piątek", day_order=4, position=3,
        name="Rozpiętki hantle w opadzie",
        exercise_key="regen-pt-rozpietki-hantle",
        sets_reps="3 x 12",
        tm_info="Sesja testowa",
    ),
    dict(
        day="Piątek", day_order=4, position=4,
        name="Spacer farmera",
        exercise_key="regen-pt-spacer-farmera",
        sets_reps="3 x 40 sek",
    ),
    dict(
        day="Piątek", day_order=4, position=5,
        name="Plank / Side Plank",
        exercise_key="regen-pt-plank-side-plank",
        sets_reps="3 x 45 sek",
    ),

    # NIEDZIELA - dom, kalistenika vertical push
    dict(
        day="Niedziela", day_order=6, position=0,
        name="HSPU przy ścianie",
        exercise_key="regen-ndz-hspu",
        sets_reps="4 x 5-8",
    ),
    dict(
        day="Niedziela", day_order=6, position=1,
        name="Frog Stand",
        exercise_key="regen-ndz-frog-stand",
        sets_reps="4 serie",
    ),
    dict(
        day="Niedziela", day_order=6, position=2,
        name="Pike Push-ups",
        exercise_key="regen-ndz-pike-pushups",
        sets_reps="3 x 10-12",
    ),
    dict(
        day="Niedziela", day_order=6, position=3,
        name="Toes to Bar",
        exercise_key="regen-ndz-toes-to-bar",
        sets_reps="3 x 10",
    ),
]

for _item in EXERCISES:
    _item.setdefault("tm_info", None)
    _item.setdefault("is_main_lift", False)
    _item["plan_group"] = PLAN_GROUP


def main():
    # 1. Upsert wszystkiego, co jest na liscie EXERCISES (scope: plan_group=regeneracja).
    resp = requests.post(
        f"{API_BASE}/api/admin/seed",
        json={"exercises": EXERCISES},
        headers={"X-Auth-Secret": APP_SECRET},
        timeout=30,
    )
    resp.raise_for_status()
    print("seed (regeneracja):", resp.json())

    # 2. Usun "osierocone" wiersze - identyczna logika jak seed_data.py, ale
    # cala scope'owana do plan_group=regeneracja (przez ?plan_group= na
    # GET /api/plan i plan_group w kazdym payloadzie DELETE), wiec NIGDY nie
    # dotyka wierszy trojboju.
    days_in_file = {item["day"] for item in EXERCISES}
    keys_in_file = {
        (item["day"], item["exercise_key"]) for item in EXERCISES if item.get("exercise_key")
    }
    names_in_file = {(item["day"], item["name"]) for item in EXERCISES}

    plan_resp = requests.get(f"{API_BASE}/api/plan", params={"plan_group": PLAN_GROUP}, timeout=30)
    plan_resp.raise_for_status()
    current_plan = plan_resp.json()

    def is_orphaned(ex):
        if ex["day"] not in days_in_file:
            return False
        if ex.get("exercise_key"):
            return (ex["day"], ex["exercise_key"]) not in keys_in_file
        return (ex["day"], ex["name"]) not in names_in_file

    orphaned = [
        {
            "day": ex["day"],
            "name": ex["name"],
            "exercise_key": ex.get("exercise_key"),
            "plan_group": PLAN_GROUP,
        }
        for ex in current_plan
        if is_orphaned(ex)
    ]

    if not orphaned:
        print("brak osieroconych wierszy (regeneracja) do usuniecia")
        return

    print("usuwam osierocone wiersze (regeneracja):", orphaned)
    del_resp = requests.delete(
        f"{API_BASE}/api/admin/exercises",
        json={"exercises": orphaned},
        headers={"X-Auth-Secret": APP_SECRET},
        timeout=30,
    )
    del_resp.raise_for_status()
    print("delete:", del_resp.json())


def sync_trend_identity():
    # 3. Utworz/zsynchronizuj tozsamosc BIEZACEGO tygodnia zakladki Trend
    # (Regeneracja) z planem, ktory wlasnie zseedowalismy - identyczny wzorzec
    # jak seed_data.py, tylko z plan_group=regeneracja. Bezpiecznie wywolac
    # wielokrotnie (upsert po week_start+day+exercise_key+plan_group).
    snap_resp = requests.post(
        f"{API_BASE}/api/admin/weekly-trend-snapshot",
        params={"plan_group": PLAN_GROUP},
        headers={"X-Auth-Secret": APP_SECRET},
        timeout=30,
    )
    snap_resp.raise_for_status()
    print("trend snapshot sync (regeneracja):", snap_resp.json())


if __name__ == "__main__":
    main()
    sync_trend_identity()
