"""Główna aplikacja FastAPI dla API Sanatoriów."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from packages.api.routes import router, sprawdz_zdrowie
from packages.api.zaleznosci import RepoDep

app = FastAPI(
    title="Sanatoria API",
    description="Wyszukiwarka komercyjnych pobytów sanatoryjnych w Polsce",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware dla aplikacji frontendowej (Vite, dev/prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Podpięcie tras API pod /api/v1
app.include_router(router, prefix="/api/v1")


# Alias dla systemów monitoringu (np. Docker healthcheck, Kubernetes)
@app.get("/healthz", include_in_schema=False)
def healthz_alias(repo: RepoDep):
    return sprawdz_zdrowie(repo)
