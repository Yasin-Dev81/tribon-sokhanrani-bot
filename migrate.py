from sqlalchemy import create_engine

from db.models import Base
from config import SQLALCHEMY_DATABASE_URL


def create_database():
    # Connect to SQLite database (or create it if it doesn't exist)
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

    # Create all tables
    Base.metadata.create_all(engine)

    print("Database and tables created successfully.")


if __name__ == "__main__":
    create_database()
