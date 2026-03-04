"""
WaterXchange Backend API
FastAPI server for water trading platform with SGMA compliance
"""

import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
from pathlib import Path

from api import auth, orders, market, chat, balance, monitoring, hardware
from api import transfers as transfers_api
from core.config import settings
from core.database import create_tables
from services.knowledge_graph import SGMAKnowledgeGraph

WEBSITE_DIR = Path(__file__).parent.parent / "website"
FRONTEND_DIR = Path(__file__).parent.parent / "frontend" / "out"

HAS_FRONTEND = FRONTEND_DIR.exists() and (FRONTEND_DIR / "index.html").exists()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    kg = SGMAKnowledgeGraph()
    kg.load_regulations()
    app.state.sgma_graph = kg
    create_tables()
    print(f"[startup] FRONTEND_DIR={FRONTEND_DIR}, exists={FRONTEND_DIR.exists()}, HAS_FRONTEND={HAS_FRONTEND}")
    if HAS_FRONTEND:
        print(f"[startup] Serving Next.js from {FRONTEND_DIR}")
        print(f"[startup] Files: {os.listdir(FRONTEND_DIR)[:15]}")
    else:
        print(f"[startup] Next.js build not found, falling back to old HTML")
    yield

app = FastAPI(
    title="WaterXchange API",
    description="Water trading platform for California farmers with SGMA compliance",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers (must come before static file mounts)
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(orders.router, prefix="/orders", tags=["Orders"])
app.include_router(market.router, prefix="/market", tags=["Market"])
app.include_router(chat.router, prefix="/chat", tags=["SGMA Chat"])
app.include_router(balance.router, prefix="/balance", tags=["Balance"])
app.include_router(monitoring.router, prefix="/monitoring", tags=["Monitoring"])
app.include_router(transfers_api.router, prefix="/transfers", tags=["Transfers"])
app.include_router(hardware.router, prefix="/hardware", tags=["Hardware"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "frontend": HAS_FRONTEND}


# ── Page routes ──────────────────────────────────────────

def _next_page(name: str):
    """Return a Next.js static page if available, else old HTML."""
    if HAS_FRONTEND:
        for candidate in [FRONTEND_DIR / f"{name}.html", FRONTEND_DIR / name / "index.html"]:
            if candidate.exists():
                return FileResponse(candidate)
    return None


@app.get("/")
async def root():
    resp = _next_page("index")
    if resp:
        return resp
    if (WEBSITE_DIR / "index.html").exists():
        return FileResponse(WEBSITE_DIR / "index.html")
    return JSONResponse({"name": "WaterXchange API", "version": "1.0.0", "status": "running"})


@app.get("/hardware")
async def hardware_page():
    return _next_page("hardware") or FileResponse(WEBSITE_DIR / "hardware.html")


@app.get("/monitoring")
async def monitoring_page():
    return _next_page("monitoring") or FileResponse(WEBSITE_DIR / "index.html")


@app.get("/transfer")
async def transfer_page():
    return _next_page("transfer") or FileResponse(WEBSITE_DIR / "transfer.html")


# Old interactive pages (Mapbox dashboard, transfer form)
@app.get("/monitor-dashboard")
async def monitor_dashboard():
    return FileResponse(WEBSITE_DIR / "monitoring.html")


@app.get("/transfer-tool")
async def transfer_tool():
    return FileResponse(WEBSITE_DIR / "transfer.html")


# ── Static file serving ──────────────────────────────────

# Next.js assets (JS/CSS bundles)
if HAS_FRONTEND and (FRONTEND_DIR / "_next").exists():
    app.mount("/_next", StaticFiles(directory=str(FRONTEND_DIR / "_next")), name="next-assets")

# Old website assets (images for old HTML pages)
if WEBSITE_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEBSITE_DIR)), name="old-static")


# Catch-all for Next.js root-level static files (logo.png, product images, etc.)
@app.get("/{filepath:path}")
async def serve_frontend_file(filepath: str):
    if HAS_FRONTEND:
        full = FRONTEND_DIR / filepath
        if full.exists() and full.is_file():
            return FileResponse(full)
    return JSONResponse({"detail": "Not found"}, status_code=404)
