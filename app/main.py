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
from fastapi.responses import JSONResponse, HTMLResponse

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

# ── Health checks & Root ──────────────────────────────────────────────────────

@app.get("/", tags=["Health"], response_class=HTMLResponse, summary="Root welcome page")
async def root():
    return f"""
    <html>
        <head>
            <title>{settings.app_name}</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 40px 20px; color: #333; }}
                h1 {{ color: #FF4500; border-bottom: 2px solid #FF4500; padding-bottom: 10px; }}
                .btn {{ display: inline-block; background: #FF4500; color: white; text-decoration: none; padding: 10px 20px; border-radius: 5px; font-weight: bold; margin-top: 20px; }}
                .btn:hover {{ background: #e03d00; }}
                .card {{ background: #f9f9f9; border: 1px solid #ddd; padding: 20px; border-radius: 8px; margin-top: 30px; }}
                code {{ background: #eee; padding: 2px 5px; border-radius: 3px; font-family: monospace; }}
            </style>
        </head>
        <body>
            <h1>🤖 {settings.app_name}</h1>
            <p>Welcome! Your API is successfully deployed and running.</p>
            
            <p>To view the available endpoints, see requirements, and test the API interactively, please visit the developer documentation:</p>
            
            <a href="/docs" class="btn">View API Documentation (Swagger UI) →</a>
            
            <div class="card">
                <h3>🚀 Available Endpoints:</h3>
                <ul>
                    <li><code>POST /create-account</code> &mdash; Automates the Reddit signup flow</li>
                    <li><code>POST /join-subreddit</code> &mdash; Joins a community using a saved session</li>
                    <li><code>POST /create-post</code> &mdash; Creates a text post in a specified subreddit</li>
                    <li><code>GET /health</code> &mdash; Simple health check</li>
                </ul>
                <p><em>Note: This API uses Playwright to perform asynchronous browser automation.</em></p>
            </div>
        </body>
    </html>
    """


@app.get("/health", tags=["Health"], summary="Health check")
async def health():
    return {"status": "healthy"}
