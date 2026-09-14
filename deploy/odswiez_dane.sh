#!/usr/bin/env bash
# deploy/odswiez_dane.sh — Cykliczne odświeżanie danych i import do bazy
set -euo pipefail

KATALOG_PROJEKTU="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${KATALOG_PROJEKTU}"

echo "=== Rozpoczęcie cyklu odświeżania: $(date -u +"%Y-%m-%dT%H:%M:%SZ") ==="

# 1. Sprawdzenie osieroconych blokad
if find out/ -name ".run.lock" -mmin +60 2>/dev/null | grep -q .; then
    echo "UWAGA: Znaleziono blokadę .run.lock starszą niż 60 minut. Wymagana weryfikacja procesu."
fi

# Ładowanie zmiennych środowiskowych (.env)
if [ -f .env ]; then
    set -a; source .env; set +a
elif [ -f deploy/.env ]; then
    set -a; source deploy/.env; set +a
fi

export SANATORIA_USER_AGENT="${SANATORIA_USER_AGENT:-SanatoriaBot/0.1 (+https://thegame2026.art; kontakt@thegame2026.art)}"

# 2. Uruchomienie zarejestrowanych adapterów produkcyjnych (domyślnie: 3 produkcyjne ośrodki)
if [ "$#" -gt 0 ]; then
    ADAPTERY=("$@")
else
    ADAPTERY=("sanatorium_promien" "sanatorium_bristol" "sanatorium_znp")
fi

for adapter in "${ADAPTERY[@]}"; do
    echo "Uruchamianie crawlera: ${adapter}..."
    uv run sanatoria-crawler run "${adapter}" || echo "Crawler ${adapter} zgłosił błąd (kontynuacja)."
done

# 3. Bezpieczny import kompletnych paczek
echo "Importowanie danych do bazy SQLite..."
uv run sanatoria-importer --katalog out/ --baza dane/sanatoria.db

# 4. Kopia zapasowa bazy
"${KATALOG_PROJEKTU}/deploy/backup_bazy.sh"

echo "=== Cykl odświeżania zakończony pomyślnie: $(date -u +"%Y-%m-%dT%H:%M:%SZ") ==="
