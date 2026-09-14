# Dokumentacja API wyszukiwarki pobytów sanatoryjnych

Niniejszy katalog zawiera specyfikację techniczną API backendu dla zespołu frontendowego (`apps/web/`, Claude Code) oraz zespołu crawlerów (`packages/crawler/`, ChatGPT Work).

## Pliki:

- **[specyfikacja.md](specyfikacja.md)** — Pełny opis endpointów (`/api/v1/oferty`, `/api/v1/oferty/{id}`, `/api/v1/filtry`, `/api/v1/zdrowie`), parametrów wyszukiwania, kalkulacji kosztów, formatów odpowiedzi i kodów błędów HTTP.
- **[przyklady/oferty_lista.json](przyklady/oferty_lista.json)** — Przykładowy payload JSON zwracany przez endpoint `/api/v1/oferty` do natychmiastowego mockowania po stronie frontendu.
