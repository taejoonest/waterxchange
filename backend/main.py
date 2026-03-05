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

WEBSITE_DIR = Path(__file__).parent.parent / "website"
FRONTEND_DIR = Path(__file__).parent.parent / "frontend" / "out"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    kg = SGMAKnowledgeGraph()
    kg.load_regulations()
    app.state.sgma_graph = kg
    create_tables()
    print(f"[startup] CWD={os.getcwd()}")
    print(f"[startup] __file__={__file__}")
    print(f"[startup] FRONTEND_DIR={FRONTEND_DIR} exists={FRONTEND_DIR.exists()}")
    print(f"[startup] WEBSITE_DIR={WEBSITE_DIR} exists={WEBSITE_DIR.exists()}")
    if FRONTEND_DIR.exists():
        print(f"[startup] frontend/out contents: {os.listdir(FRONTEND_DIR)[:20]}")
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
        "frontend_dir": str(FRONTEND_DIR),
        "frontend_exists": FRONTEND_DIR.exists(),
        "frontend_index": (FRONTEND_DIR / "index.html").exists(),
    }


# ── Page routes ──────────────────────────────────────────

def _next_page(name: str):
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

# Old website assets
if WEBSITE_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEBSITE_DIR)), name="old-static")

# Next.js static files — mount at root LAST so API routes take priority.
# We try multiple possible locations since Railway paths can differ.
_frontend_candidates = [
    FRONTEND_DIR,
    Path("/app/frontend/out"),
    Path(os.getcwd()).parent / "frontend" / "out",
    Path(os.getcwd()) / "frontend" / "out",
]

_mounted = False
for _candidate in _frontend_candidates:
    if _candidate.exists() and (_candidate / "index.html").exists():
        print(f"[mount] Serving frontend from {_candidate}")
        app.mount("/", StaticFiles(directory=str(_candidate), html=False), name="frontend-root")
        _mounted = True
        break

if not _mounted:
    print(f"[mount] WARNING: No frontend/out found. Tried: {[str(c) for c in _frontend_candidates]}")
