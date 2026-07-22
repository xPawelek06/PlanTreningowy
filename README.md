Statyczna strona z podglądem planu treningowego

Statyczny frontend (GitHub Pages) + backend FastAPI/Postgres (Neon).

## Hosting backendu (2026-07-22: migracja z Render)

VM (GCP, `paw-projects`), Docker Compose — FastAPI + Caddy (reverse proxy,
HTTPS automatyczny przez Let's Encrypt/sslip.io), ten sam wzorzec co
`MeetingReminder`/`Waga`. Jeden wspólny Caddy na tej VM obsługuje wszystkie
trzy appki (różne subdomeny sslip.io) — konfiguracja Caddyfile mieszka w repo
`MeetingReminder` (`~/MeetingReminder/Caddyfile` na serwerze), bo tam był
uruchomiony jako pierwszy. Backend PlanTreningowy podłącza się do tej samej
sieci Dockera (`meetingreminder_default`, external w `docker-compose.yml`
tego repo), żeby Caddy mógł go zaadresować po nazwie kontenera
(`plantreningowy-backend`).

Tymczasowy (trial GCP, do 21.09.2026), docelowo migracja na wspólny VPS
(Plan B, Hetzner). Baza (Neon) zostaje bez zmian — connection string
identyczny jak wcześniej na Renderze. `render.yaml` zostaje jako gotowy
fallback, nieużywany.

Konfiguracja: `docker-compose.yml` w katalogu głównym, `backend/Dockerfile`.
Sekrety (`DATABASE_URL`, `APP_SECRET`) w `backend/.env` na serwerze
(gitignore, chmod 600) — nie w tym repo.
