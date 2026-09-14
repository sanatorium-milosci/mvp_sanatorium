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

# 2. Uruchomienie zarejestrowanych adapterów produkcyjnych (jeśli przekazano jako argumenty)
if [ "$#" -gt 0 ]; then
    for adapter in "$@"; do
        echo "Uruchamianie crawlera: ${adapter}..."
        uv run sanatoria-crawler run "${adapter}" || echo "Crawler ${adapter} zgłosił błąd (kontynuacja)."
    done
fi

# 3. Bezpieczny import kompletnych paczek
echo "Importowanie danych do bazy SQLite..."
uv run sanatoria-importer --katalog out/ --baza dane/sanatoria.db

# 4. Kopia zapasowa bazy
"${KATALOG_PROJEKTU}/deploy/backup_bazy.sh"

echo "=== Cykl odświeżania zakończony pomyślnie: $(date -u +"%Y-%m-%dT%H:%M:%SZ") ==="
