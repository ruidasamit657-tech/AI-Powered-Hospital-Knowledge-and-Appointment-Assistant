from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import engine
from app.db.base import Base


setup_logging()

app = FastAPI(
    title="AI-Powered Hospital Knowledge and Appointment Assistant",
    description="A comprehensive hospital management system with AI chatbot",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
async def root():
    return {
        "message": "AI-Powered Hospital Knowledge and Appointment Assistant",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)
    print("Database tables created/verified")