"""Reczne wpisywanie/korekta zakladki 'Trend' dla DOWOLNEGO (najczesciej
przeszlego) tygodnia - odpowiednik seed_data.py, ale zamiast planu wysyla
zrzut do tabeli weekly_trend_snapshots przez POST
/api/admin/weekly-trend-snapshot/manual.

Kiedy tego uzywac:
- Automatyczny mechanizm (POST /api/admin/weekly-trend-snapshot, bez /manual)
  dziala TYLKO dla biezacego tygodnia w momencie wywolania - kopiuje aktualny
  stan tabeli 'exercises'. Nie da sie nim uzupelnic historii wstecz.
- Ten skrypt pozwala Pawlowi recznie przepisac/skondensowac dane z
  gym/logs/archiwum.md (w repo mozgu) - surowe wpisy zapas/seria+/uwagi per
  cwiczenie/dzien - do zwiezlej postaci obciazenie/serie x powtorzenia za
  konkretny tydzien i wgrac je do appki, zeby Trend pokazywal pelniejsza
  historie postepu.

Uzycie:
    1. Zdefiniuj tydzien(-nie) w liscie TREND_WEEKS ponizej: week_start,
       week_end (poniedzialek..niedziela) i liste wierszy - kazdy wiersz to
       jedno cwiczenie z day/day_order/position/name/exercise_key/postep/
       is_main_lift. postep (2026-09-22, dawniej sets_reps+tm_info - patrz
       models.WeeklyTrendSnapshot) to jedno wolne pole tekstowe.
       exercise_key (dodany 2026-07-14) jest opcjonalny, ale zalecany - gdy
       podany, pozwala zakladce Trend dopasowac wiersz do tej samej pozycji w
       pivotcie nawet po zmianie nazwy cwiczenia w planie (patrz
       backend/migrate_exercise_keys.py za mapowanie nazwa->klucz).
    2. Uruchom:
        API_BASE=http://127.0.0.1:8000 APP_SECRET=PlanTreningowy python seed_trend.py
        API_BASE=https://plan-treningowy-api.onrender.com APP_SECRET=PlanTreningowy python seed_trend.py

Kazdy tydzien z TREND_WEEKS jest wyslany osobnym wywolaniem endpointu -
upsert po week_start (kasuje istniejace wiersze tego tygodnia w bazie i
wstawia te z listy), wiec bezpiecznie uruchomic ponownie, np. przy korekcie
literowki - nie zduplikuje wierszy i nie ruszy innych tygodni.

Zeby USUNAC (wyczyscic) caly zrzut jakiegos tygodnia - np. testowy wpis -
zostaw dla niego pusta liste "exercises": [] i uruchom skrypt ponownie:
upsert skasuje stare wiersze i nie wstawi nic w ich miejsce.
"""

import os
from datetime import date

import requests

API_BASE = os.environ.get("API_BASE", "http://127.0.0.1:8000")
APP_SECRET = os.environ.get("APP_SECRET", "PlanTreningowy")

TREND_WEEKS = [
    dict(
        week_start=date(2026, 6, 1),
        week_end=date(2026, 6, 7),
        exercises=[
            # Przyklad - podmien na prawdziwe dane skondensowane z
            # gym/logs/archiwum.md dla tego tygodnia. postep moze zawierac
            # \n - frontend renderuje kazdy fragment jako osobna linie.
            dict(
                day="Poniedziałek", day_order=0, position=0,
                name="Podciąganie z dociążeniem w plecaku",
                exercise_key="pon-podciaganie-dociazone",
                postep="+7,5 kg, 4x7 (zapas 1 powt.)",
                is_main_lift=False,
            ),
        ],
    ),
]


def main():
    for week in TREND_WEEKS:
        payload = {
            "week_start": week["week_start"].isoformat(),
            "week_end": week["week_end"].isoformat(),
            "exercises": week["exercises"],
        }
        resp = requests.post(
            f"{API_BASE}/api/admin/weekly-trend-snapshot/manual",
            json=payload,
            headers={"X-Auth-Secret": APP_SECRET},
            timeout=30,
        )
        resp.raise_for_status()
        print(f"tydzien {week['week_start']}..{week['week_end']}:", resp.json())


if __name__ == "__main__":
    main()
