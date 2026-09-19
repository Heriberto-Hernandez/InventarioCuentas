import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent

# Carga variables desde manager/.env si existe
load_dotenv(BASE_DIR / ".env")

# Supabase expone PostgreSQL. Se quitan comillas para aceptar DATABASE_URL="...".
DATABASE_URL = os.getenv("DATABASE_URL", "").strip().strip('"').strip("'")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
if DATABASE_URL and not DATABASE_URL.startswith("postgresql+psycopg2://"):
    raise RuntimeError("DATABASE_URL debe ser una URL PostgreSQL de Supabase")

engine = (create_engine(DATABASE_URL, connect_args={"sslmode": "require"}, pool_pre_ping=True)
          if DATABASE_URL else None)
SessionLocal = (sessionmaker(autocommit=False, autoflush=False, bind=engine)
                if engine else None)
Base = declarative_base()


def get_db():
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL no está configurada en Vercel Production")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()