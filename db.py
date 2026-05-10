from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# TiDB / MySQL connection string
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={
        "ssl": {}
    }
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()