# Reddit Automation API

A production-ready REST API that automates Reddit account creation, subreddit joining, and posting using **FastAPI** + **Playwright** browser automation.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/create-account` | Create a new Reddit account |
| `POST` | `/join-subreddit` | Join a subreddit using a stored session |
| `POST` | `/create-post` | Create a text post using a stored session |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/health` | Health check |

---

## Quick Start (Local)

### 1. Clone & configure

```bash
git clone <your-repo-url>
cd reddit-automation-api
cp .env.example .env
# Edit .env — set CAPTCHA_API_KEY if you have one
```

### 2. Create virtualenv & install

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate # Linux/macOS

pip install -r requirements.txt
playwright install chromium
```

### 3. Create required directories

```bash
mkdir -p data/sessions logs
```

### 4. Run the server

```bash
uvicorn app.main:app --reload
# API available at http://localhost:8000
# Swagger UI at http://localhost:8000/docs
```

---

## Docker (Recommended)

```bash
docker-compose up --build
```

---

## API Reference

### `POST /create-account`

```json
// Request
{
  "username": "my_reddit_user",
  "password": "SecurePass@123",
  "email": "user@example.com"
}

// Response (success)
{
  "success": true,
  "username": "my_reddit_user",
  "message": "Account created successfully"
}
```

> **CAPTCHA**: Reddit uses hCaptcha on signup. Set `CAPTCHA_API_KEY` in `.env` for automated solving via 2captcha or Anti-Captcha. Without it, the account creation step will require manual intervention.

---

### `POST /join-subreddit`

Requires a prior `/create-account` call (session must exist).

```json
// Request
{
  "username": "my_reddit_user",
  "subreddit": "r/learnpython"
}

// Response
{
  "joined": true,
  "subreddit": "learnpython",
  "reason": "success"   // or: "already_member" | "private" | "not_found"
}
```

---

### `POST /create-post`

Requires a prior `/create-account` call (session must exist).

```json
// Request
{
  "username": "my_reddit_user",
  "subreddit": "learnpython",
  "title": "Hello from the API!",
  "content": "This post was created automatically."
}

// Response
{
  "success": true,
  "post_url": "https://www.reddit.com/r/learnpython/comments/abc123/hello_from_the_api/",
  "post_id": "abc123",
  "status": "posted"
}
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HEADLESS` | `true` | Run browser headlessly |
| `SESSION_DIR` | `data/sessions` | Cookie storage directory |
| `CAPTCHA_API_KEY` | _(empty)_ | 2captcha / Anti-Captcha API key |
| `CAPTCHA_SERVICE` | `2captcha` | `2captcha` or `anticaptcha` |
| `PROXY_URL` | _(empty)_ | Optional proxy (`http://user:pass@host:port`) |
| `LOG_LEVEL` | `INFO` | Python log level |
| `MAX_RETRIES` | `3` | Max retry attempts |

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Deployment (Render)

1. Push your code to GitHub (ensure `.env` is git-ignored)
2. Create a new **Web Service** on [render.com](https://render.com)
3. Select **Docker** as the environment
4. Set environment variables in the Render dashboard
5. Deploy — Chromium is pre-installed in the Docker image

> Render free tier will spin down after inactivity; use paid tier for always-on.

---

## Anti-Detection Measures

- **Randomised user-agent** on every browser context
- **Human-like typing** — per-character delays (50–200 ms)
- **Random scroll** — simulates reading before actions
- **Random delays** between page interactions
- **Stealth JS patches** — removes `navigator.webdriver` fingerprint
- **Optional proxy** support for IP rotation

---

## CAPTCHA Strategy

Reddit's signup uses **hCaptcha**. This project handles it by:

1. Calling the 2captcha or Anti-Captcha REST API with the site key
2. Polling for the solved token (up to 2.5 minutes)
3. Injecting the token into the DOM via `page.evaluate()`

Without a CAPTCHA API key, account creation will work for:
- Reddit test environments
- Cases where CAPTCHA is occasionally skipped

---

## Project Structure

```
app/
├── main.py                  # FastAPI app
├── api/                     # Route handlers
├── services/                # Business logic (Playwright automation)
├── dependencies/            # Session manager
├── utils/                   # Logger, delay, captcha solver
├── models/                  # Pydantic schemas
└── config/                  # Settings
data/sessions/               # Cookie files (git-ignored)
logs/                        # Log files (git-ignored)
tests/                       # pytest test suite
```
