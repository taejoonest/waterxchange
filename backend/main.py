"""
WaterXchange Backend API
FastAPI server for water trading platform with SGMA compliance
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from api import auth, orders, market, chat, balance, monitoring
from core.config import settings
from core.database import create_tables
from services.knowledge_graph import SGMAKnowledgeGraph

# Initialize knowledge graph on startup
sgma_graph = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    global sgma_graph
    sgma_graph = SGMAKnowledgeGraph()
    sgma_graph.load_regulations()
    create_tables()
    yield
    # Cleanup on shutdown

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

WEBSITE_DIR = Path(__file__).resolve().parent.parent / "website"

@app.get("/", response_class=FileResponse)
async def root():
    return FileResponse(WEBSITE_DIR / "index.html")

@app.get("/monitor", response_class=FileResponse)
async def monitoring_page():
    return FileResponse(WEBSITE_DIR / "monitoring.html")

@app.get("/api")
async def api_info():
    return {
        "name": "WaterXchange API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if WEBSITE_DIR.exists():
    app.mount("/static", StaticFiles(directory=WEBSITE_DIR), name="website")
