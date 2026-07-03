import pyodbc
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={settings.db_server};"
    f"DATABASE={settings.db_name};"
    "Trusted_Connection=yes;"
)

engine = create_engine("mssql+pyodbc://", creator=lambda: pyodbc.connect(conn_str), echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()