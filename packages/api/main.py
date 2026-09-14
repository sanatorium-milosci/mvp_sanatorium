"""Punkt wejścia CLI do uruchamiania serwera API Sanatoriów."""

from __future__ import annotations

import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Serwer REST API dla ofert sanatoryjnych.")
    parser.add_argument("--host", default="0.0.0.0", help="Host nasłuchiwania (domyślnie: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port serwera (domyślnie: 8000)")
    parser.add_argument("--reload", action="store_true", help="Tryb automatycznego przeładowania")

    args = parser.parse_args()
    uvicorn.run("packages.api.app:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
