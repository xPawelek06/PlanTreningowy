import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Render (i wiekszosc hostow Postgres) podaje DATABASE_URL w formie "postgres://...".
# SQLAlchemy 1.4+ / psycopg2 wymaga prefiksu "postgresql://".
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./local.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
