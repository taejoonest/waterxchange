"""
WaterXchange Backend API
FastAPI server for water trading platform with SGMA compliance
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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


# Old interactive pages (Mapbox monitoring dashboard, transfer form)
@app.get("/monitor-dashboard")
async def monitor_dashboard():
    return FileResponse(WEBSITE_DIR / "monitoring.html")


@app.get("/transfer-tool")
async def transfer_tool():
    return FileResponse(WEBSITE_DIR / "transfer.html")


# Serve old static assets (images referenced by old HTML pages)
app.mount("/static", StaticFiles(directory=str(WEBSITE_DIR)), name="static")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Next.js static pages
def _serve_next(page: str):
    """Serve a Next.js static export page."""
    # Try /page.html first, then /page/index.html
    for candidate in [FRONTEND_DIR / f"{page}.html", FRONTEND_DIR / page / "index.html"]:
        if candidate.exists():
            return FileResponse(candidate)
    # Fallback to old website
    return FileResponse(WEBSITE_DIR / "index.html")


@app.get("/")
async def root():
    if (FRONTEND_DIR / "index.html").exists():
        return FileResponse(FRONTEND_DIR / "index.html")
    if (WEBSITE_DIR / "index.html").exists():
        return FileResponse(WEBSITE_DIR / "index.html")
    return {"name": "WaterXchange API", "version": "1.0.0", "status": "running"}


@app.get("/hardware")
async def hardware_page():
    return _serve_next("hardware")


@app.get("/monitoring")
async def monitoring_page():
    return _serve_next("monitoring")


@app.get("/transfer")
async def transfer_page():
    return _serve_next("transfer")


# Serve Next.js static assets (_next/*, images, etc.)
if FRONTEND_DIR.exists():
    app.mount("/_next", StaticFiles(directory=str(FRONTEND_DIR / "_next")), name="next-static")
    app.mount("/next-assets", StaticFiles(directory=str(FRONTEND_DIR)), name="next-root")
