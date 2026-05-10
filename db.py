from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
import ssl

DATABASE_URL = os.getenv("DATABASE_URL")

ssl_ctx = ssl.create_default_context()

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"ssl": ssl_ctx}
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()