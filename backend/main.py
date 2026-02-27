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

# CORS for iOS app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(orders.router, prefix="/orders", tags=["Orders"])
app.include_router(market.router, prefix="/market", tags=["Market"])
app.include_router(chat.router, prefix="/chat", tags=["SGMA Chat"])
app.include_router(balance.router, prefix="/balance", tags=["Balance"])
app.include_router(monitoring.router, prefix="/monitoring", tags=["Monitoring"])
app.include_router(transfers_api.router, prefix="/transfers", tags=["Transfers"])
app.include_router(hardware.router, prefix="/hardware", tags=["Hardware"])


@app.get("/")
async def root():
    if (WEBSITE_DIR / "index.html").exists():
        return FileResponse(WEBSITE_DIR / "index.html")
    return {"name": "WaterXchange API", "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/monitor")
async def monitor_page():
    return FileResponse(WEBSITE_DIR / "monitoring.html")


@app.get("/transfer")
async def transfer_page():
    return FileResponse(WEBSITE_DIR / "transfer.html")


@app.get("/hardware")
async def hardware_page():
    return FileResponse(WEBSITE_DIR / "hardware.html")
