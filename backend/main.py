"""
WaterXchange Backend API
FastAPI server for water trading platform with SGMA compliance
"""

import os
from fastapi import FastAPI
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

BASE_DIR = Path(__file__).parent.parent
WEBSITE_DIR = BASE_DIR / "website"
FRONTEND_OUT = BASE_DIR / "frontend" / "out"
FRONTEND_PUBLIC = BASE_DIR / "frontend" / "public"


def _find_frontend():
    """Find the frontend build output or public directory."""
    for d in [FRONTEND_OUT, FRONTEND_PUBLIC, Path("/app/frontend/out"), Path("/app/frontend/public")]:
        if d.exists() and (d / "logo.png").exists():
            return d
    return None


FRONTEND_STATIC = _find_frontend()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    kg = SGMAKnowledgeGraph()
    kg.load_regulations()
    app.state.sgma_graph = kg
    create_tables()
    print(f"[startup] BASE_DIR={BASE_DIR}")
    print(f"[startup] FRONTEND_STATIC={FRONTEND_STATIC}")
    print(f"[startup] FRONTEND_OUT exists={FRONTEND_OUT.exists()}")
    print(f"[startup] FRONTEND_PUBLIC exists={FRONTEND_PUBLIC.exists()}")
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

# API routers
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
    return {
        "status": "healthy",
        "v": 3,
        "frontend_static": str(FRONTEND_STATIC),
        "frontend_out_exists": FRONTEND_OUT.exists(),
        "frontend_public_exists": FRONTEND_PUBLIC.exists(),
    }


# ── Page routes ──────────────────────────────────────────

def _next_page(name: str):
    if FRONTEND_OUT.exists():
        for candidate in [FRONTEND_OUT / f"{name}.html", FRONTEND_OUT / name / "index.html"]:
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
    return JSONResponse({"name": "WaterXchange API", "version": "1.0.0"})


@app.get("/hardware")
async def hardware_page():
    return _next_page("hardware") or FileResponse(WEBSITE_DIR / "hardware.html")


@app.get("/monitoring")
async def monitoring_page():
    return _next_page("monitoring") or FileResponse(WEBSITE_DIR / "index.html")


@app.get("/transfer")
async def transfer_page():
    return _next_page("transfer") or FileResponse(WEBSITE_DIR / "transfer.html")


@app.get("/monitor-dashboard")
async def monitor_dashboard():
    return FileResponse(WEBSITE_DIR / "monitoring.html")


@app.get("/transfer-tool")
async def transfer_tool():
    return FileResponse(WEBSITE_DIR / "transfer.html")


# ── Static file serving ──────────────────────────────────

if WEBSITE_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEBSITE_DIR)), name="old-static")

# Serve Next.js _next/ bundles from build output
if FRONTEND_OUT.exists() and (FRONTEND_OUT / "_next").exists():
    app.mount("/_next", StaticFiles(directory=str(FRONTEND_OUT / "_next")), name="next-bundles")

# Serve images/static files from frontend (try out/ first, then public/)
if FRONTEND_STATIC:
    app.mount("/", StaticFiles(directory=str(FRONTEND_STATIC)), name="frontend-files")
