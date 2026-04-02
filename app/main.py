"""
Reddit Automation API — FastAPI application entry point.

Endpoints:
    POST /create-account   — automate Reddit signup
    POST /join-subreddit   — join a subreddit via stored session
    POST /create-post      — create a text post via stored session
    GET  /                 — health check
    GET  /health           — health check (alternate)
    GET  /docs             — Swagger UI (auto-generated)
    GET  /redoc            — ReDoc UI (auto-generated)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import account, subreddit, post
from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{settings.app_name} starting up...")
    yield
    logger.info(f"{settings.app_name} shutting down...")


app = FastAPI(
    title=settings.app_name,
    description=(
        "Production-ready Reddit automation API.\n\n"
        "Automates account creation, subreddit joining, and post creation "
        "using Playwright browser automation with anti-detection measures."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware ────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(account.router)
app.include_router(subreddit.router)
app.include_router(post.router)

# ── Global exception handler ──────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Check logs for details."},
    )

# ── Health checks ─────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"], summary="Root health check")
async def root():
    return {"status": "ok", "service": settings.app_name, "version": "1.0.0"}


@app.get("/health", tags=["Health"], summary="Health check")
async def health():
    return {"status": "healthy"}
