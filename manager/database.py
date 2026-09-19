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
if not DATABASE_URL:
    raise RuntimeError("Falta DATABASE_URL en manager/.env; la aplicación requiere Supabase")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
if not DATABASE_URL.startswith("postgresql+psycopg2://"):
    raise RuntimeError("DATABASE_URL debe ser una URL PostgreSQL de Supabase")

engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"}, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()