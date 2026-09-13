"""CLI dla przebiegów sieciowych i bezsieciowego demo."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from importlib.resources import files
from pathlib import Path

import httpx

from packages.crawler.adaptery import rejestr_produkcyjny
from packages.crawler.adaptery.demo import URL_DEMO, AdapterDemo
from packages.crawler.fetch import Fetch
from packages.crawler.runner import uruchom


def transport_demo() -> httpx.MockTransport:
    html = files("packages.crawler").joinpath("dane_demo/oferty.html").read_text(encoding="utf-8")

    def odpowiedz(request: httpx.Request) -> httpx.Response:
        if str(request.url) == "https://sanatorium.example/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        if str(request.url) == URL_DEMO:
            return httpx.Response(
                200, text=html, headers={"content-type": "text/html; charset=utf-8"}
            )
        raise AssertionError(f"Demo nie obsługuje URL: {request.url}")

    return httpx.MockTransport(odpowiedz)


async def _run(args: argparse.Namespace) -> int:
    if args.polecenie == "demo":
        adapter = AdapterDemo()
        agent = "SanatoriaBot/1.0 (+https://sanatorium.example/bot; kontakt@sanatorium.example)"
        transport = transport_demo()
    else:
        adapter = rejestr_produkcyjny().pobierz(args.adapter)
        agent = args.user_agent or os.environ.get("SANATORIA_USER_AGENT", "")
        transport = None
    async with Fetch(
        user_agent=agent,
        domeny=adapter.domeny,
        cache_dir=args.cache / adapter.nazwa,
        wspolbieznosc=args.wspolbieznosc,
        transport=transport,
    ) as fetch:
        raport = await uruchom(adapter, fetch, args.out, pracownicy=args.wspolbieznosc)
    print(json.dumps(raport, ensure_ascii=False, indent=2))
    return 0 if raport["kompletny"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Crawler ofert sanatoryjnych — ścieżka B")
    komendy = parser.add_subparsers(dest="polecenie", required=True)
    komendy.add_parser("list", help="Lista zweryfikowanych adapterów produkcyjnych")
    for nazwa in ("demo", "run"):
        komenda = komendy.add_parser(nazwa, help="Demo offline" if nazwa == "demo" else "Przebieg")
        komenda.add_argument("--out", type=Path, default=Path("out"))
        komenda.add_argument("--cache", type=Path, default=Path(".cache/crawler"))
        komenda.add_argument("--wspolbieznosc", type=int, default=4)
        if nazwa == "run":
            komenda.add_argument("adapter")
            komenda.add_argument("--user-agent")
    args = parser.parse_args()
    if args.polecenie == "list":
        nazwy = rejestr_produkcyjny().nazwy()
        print(
            "\n".join(nazwy) if nazwy else "Brak adapterów produkcyjnych. Dostępne: demo (offline)."
        )
        return 0
    try:
        return asyncio.run(_run(args))
    except (ValueError, RuntimeError, OSError, NotImplementedError) as exc:
        parser.exit(2, f"Błąd: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
