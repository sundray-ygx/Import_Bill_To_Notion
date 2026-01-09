"""FastAPI web service for bill import."""

import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from utils import setup_logging


# Setup
web_service_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv()

# Configure logging
log_dir = os.path.join(web_service_dir, "logs")
os.makedirs(log_dir, exist_ok=True)
setup_logging("INFO", os.path.join(log_dir, 'web_service.log'))

import logging
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Bill Import Service", description="Upload and sync bills to Notion", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
app.mount("/static", StaticFiles(directory=os.path.join(web_service_dir, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(web_service_dir, "templates"))

# Routes
from .routes import upload
app.include_router(upload.router, prefix="/api", tags=["upload"])


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/bill-management")
def bill_management(request: Request):
    return templates.TemplateResponse("bill_management.html", {"request": request})


@app.get("/service-management")
def service_management(request: Request):
    return templates.TemplateResponse("service_management.html", {"request": request})


@app.get("/log-management")
def log_management(request: Request):
    return templates.TemplateResponse("log_management.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web_service.main:app", host="0.0.0.0", port=8000, reload=True)
