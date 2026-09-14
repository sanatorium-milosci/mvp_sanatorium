# Wdrożenie i Eksploatacja (Deploy)

Niniejszy katalog zawiera konfigurację uruchomienia produkcyjnego, konfigurację HTTPS, mechanizmy odświeżania danych oraz tworzenia kopii zapasowych bazy danych.

## Architektura wdrożenia

- **Serwer API**: FastAPI działający na Uvicorn (port 8000), w kontenerze Docker lub bezpośrednio przez `uv`.
- **Baza danych**: SQLite z włączonym trybem WAL (`dane/sanatoria.db`), montowana jako wolumen.
- **Frontend**: Aplikacja SPA (React + TypeScript + Vite) zbudowana w `apps/web/dist`.
- **Reverse Proxy / HTTPS**: Caddy v2 z automatyczną obsługą darmowych certyfikatów SSL Let's Encrypt oraz kompresją Zstandard/Gzip.

---

## 1. Uruchomienie lokalne (Development)

### Krok 1: Instalacja zależności
```bash
uv sync
```

### Krok 2: Pozyskanie danych testowych / produkcyjnych
Można uruchomić crawler demonstracyjny lub adaptery produkcyjne:
```bash
uv run sanatoria-crawler demo
```

### Krok 3: Import danych do bazy
```bash
uv run sanatoria-importer --katalog out/ --baza dane/sanatoria.db
```

### Krok 4: Uruchomienie API
```bash
uv run sanatoria-api --host 127.0.0.1 --port 8000 --reload
```
API dostępne pod: `http://127.0.0.1:8000`
- Dokumentacja Swagger: `http://127.0.0.1:8000/docs`
- Healthcheck: `http://127.0.0.1:8000/healthz`
- Oferty: `http://127.0.0.1:8000/api/v1/oferty`

---

## 2. Wdrożenie produkcyjne z HTTPS (Docker Compose + Caddy)

### Wymagania:
- Docker i Docker Compose (lub Podman)
- Domena skierowana rekordem A na adres IP serwera (np. `thegame2026.art`)
- *(Opcjonalnie)* Node.js — nie jest wymagany na hoście, ponieważ `deploy/Dockerfile.caddy` buduje frontend automatycznie w kontenerze.

### Uruchomienie:
1. Ustaw domenę oraz kontakt dla crawlera w pliku `deploy/.env`:
   ```bash
   cat << 'EOF' > deploy/.env
   DOMAIN=thegame2026.art
   SANATORIA_USER_AGENT=SanatoriaBot/0.1 (+https://thegame2026.art; kontakt@thegame2026.art)
   EOF
   ```
2. Zbuduj i uruchom kontenery w tle:
   ```bash
   cd deploy
   docker compose up -d --build
   ```
Caddy automatycznie wygeneruje certyfikat SSL z Let's Encrypt i przekieruje ruch HTTP na HTTPS.

---

## 3. Cykliczne odświeżanie danych (Cron)

Skrypt `deploy/odswiez_dane.sh` wykonuje:
1. Ładowanie konfiguracji ze zmiennych środowiskowych i `.env`,
2. Uruchomienie produkcyjnych adapterów (`sanatorium_promien`, `sanatorium_bristol`, `sanatorium_znp`),
3. Weryfikację kompletności i bezpieczny import paczek do bazy SQLite,
4. Wykonanie atomowej kopii zapasowej bazy.

Przykładowy wpis w `crontab` (uruchamianie raz dziennie o 03:00 w nocy):
```crontab
0 3 * * * /sciezka/do/mvp_sanatorium/deploy/odswiez_dane.sh >> /var/log/sanatoria_odswiez.log 2>&1
```

---

## 4. Kopia zapasowa i odzyskiwanie bazy danych

### Wykonanie kopii zapasowej na żądanie:
```bash
./deploy/backup_bazy.sh
```
Skrypt tworzy atomową kopię pliku bazy w katalogu `kopie/sanatoria_YYYY-MM-DD_HHMMSS.db` i automatycznie zachowuje 14 ostatnich kopii zapasowych.

### Przywrócenie bazy z kopii:
W przypadku konieczności przywrócenia:
```bash
cp kopie/sanatoria_2026-09-14_150000.db dane/sanatoria.db
```
Baza jest natychmiast gotowa do odczytu przez API.
