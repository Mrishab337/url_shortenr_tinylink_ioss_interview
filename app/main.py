from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timedelta
import io
from typing import Optional

from .database import Base, engine, get_db
from .models import URLMap
from .schemas import ShortenRequest, ShortenResponse
from .config import settings
from .utils import gen_code

import qrcode

app = FastAPI(title="URL Shortener", version="1.0.0")
Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Web UI
@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    recent = db.execute(select(URLMap).order_by(URLMap.created_at.desc()).limit(10)).scalars().all()
    return templates.TemplateResponse("index.html", {"request": request, "recent": recent, "base_url": settings.APP_BASE_URL})

@app.get("/stats/{code}", response_class=HTMLResponse)
def stats_page(code: str, request: Request, db: Session = Depends(get_db)):
    url = db.execute(select(URLMap).where(URLMap.code == code)).scalar_one_or_none()
    if not url:
        return templates.TemplateResponse("not_found.html", {"request": request, "code": code}, status_code=404)
    return templates.TemplateResponse("stats.html", {"request": request, "item": url, "base_url": settings.APP_BASE_URL})

@app.post("/shorten", response_class=HTMLResponse)
def shorten_form(
    request: Request,
    url: str = Form(...),
    custom_alias: Optional[str] = Form(None),
    expires_in_days: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    payload = ShortenRequest(url=url, custom_alias=custom_alias or None, expires_in_days=expires_in_days or None)
    return _create_short_link(payload, db, request)

def _create_short_link(payload: ShortenRequest, db: Session, request: Optional[Request] = None):

    code = payload.custom_alias
    if code:
        # Ensure alias not taken
        existing = db.execute(select(URLMap).where(URLMap.code == code)).scalar_one_or_none()
        if existing:
            ctx = {"detail": "Alias already in use. Try another.", "recent": [], "request": request, "base_url": settings.APP_BASE_URL}
            if request:
                return templates.TemplateResponse("index.html", ctx, status_code=400)
            raise HTTPException(status_code=400, detail="Alias already in use.")
    else:
        # Generate unique code
        code = gen_code(length=settings.CODE_LENGTH)
        while db.execute(select(URLMap).where(URLMap.code == code)).scalar_one_or_none() is not None:
            code = gen_code(length=settings.CODE_LENGTH)

    expires_at = None
    if payload.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=payload.expires_in_days)

    item = URLMap(code=code, target_url=str(payload.url), expires_at=expires_at)
    db.add(item)
    db.commit()

    short_url = f"{settings.APP_BASE_URL.rstrip('/')}/{code}"
    if request:
        recent = db.execute(select(URLMap).order_by(URLMap.created_at.desc()).limit(10)).scalars().all()
        return templates.TemplateResponse("index.html", {"request": request, "recent": recent, "created_short_url": short_url, "code": code, "base_url": settings.APP_BASE_URL})
    return ShortenResponse(short_url=short_url, code=code)

# JSON API
@app.post("/api/shorten", response_model=ShortenResponse)
def api_shorten(payload: ShortenRequest, db: Session = Depends(get_db)):
    res = _create_short_link(payload, db)
    return res

@app.get("/api/{code}")
def api_get(code: str, db: Session = Depends(get_db)):
    item = db.execute(select(URLMap).where(URLMap.code == code)).scalar_one_or_none()
    if not item:
        raise HTTPException(404, detail="Not found")
    return {
        "code": item.code,
        "target_url": item.target_url,
        "created_at": item.created_at,
        "expires_at": item.expires_at,
        "is_active": item.is_active,
        "click_count": item.click_count,
        "last_accessed": item.last_accessed,
        "short_url": f"{settings.APP_BASE_URL.rstrip('/')}/{item.code}",
    }

# Redirect route
@app.get("/{code}")
def redirect(code: str, db: Session = Depends(get_db)):
    item = db.execute(select(URLMap).where(URLMap.code == code)).scalar_one_or_none()
    if not item or not item.is_active or item.is_expired():
        return templates.TemplateResponse("not_found.html", {"request": Request, "code": code}, status_code=404)
    item.click_count += 1
    item.last_accessed = datetime.utcnow()
    db.add(item)
    db.commit()
    return RedirectResponse(item.target_url, status_code=307)

# QR Code endpoint
@app.get("/qr/{code}")
def qr(code: str, db: Session = Depends(get_db)):
    item = db.execute(select(URLMap).where(URLMap.code == code)).scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Not found")
    img = qrcode.make(f"{settings.APP_BASE_URL.rstrip('/')}/{item.code}")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")
