#!/usr/bin/env bash
# deploy/backup_bazy.sh — Bezpieczna kopia zapasowa bazy danych SQLite
set -euo pipefail

KATALOG_PROJEKTU="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KATALOG_KOPII="${KATALOG_PROJEKTU}/kopie"
PLIK_BAZY="${KATALOG_PROJEKTU}/dane/sanatoria.db"
DATA="$(date -u +"%Y-%m-%d_%H%M%S")"
CEL="${KATALOG_KOPII}/sanatoria_${DATA}.db"

mkdir -p "${KATALOG_KOPII}"

if [ ! -f "${PLIK_BAZY}" ]; then
    echo "Baza danych ${PLIK_BAZY} jeszcze nie istnieje. Pomijam backup."
    exit 0
fi

echo "Tworzenie atomowej kopii zapasowej do: ${CEL}..."
uv run python -c "
from packages.storage.baza import BazaDanych
baza = BazaDanych('${PLIK_BAZY}')
baza.wykonaj_kopie_zapasowa('${CEL}')
"

echo "Kopia zapasowa gotowa: ${CEL} ($(stat -c%s "${CEL}") bajtów)"

# Zachowaj tylko 14 ostatnich kopii zapasowych
ls -1tr "${KATALOG_KOPII}"/sanatoria_*.db 2>/dev/null | head -n -14 | xargs -r rm -f
echo "Usunięto stare kopie powyżej limitu 14."
