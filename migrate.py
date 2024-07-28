from sqlalchemy import create_engine
from alembic.config import Config
from alembic import command

from db.models import Base
from config import SQLALCHEMY_DATABASE_URL


def create_database():
    # Connect to SQLite database (or create it if it doesn't exist)
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

    # Create all tables
    Base.metadata.create_all(engine)

    print("Database and tables created successfully.")


def upgrade():
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)
    command.upgrade(alembic_cfg, "head")


def downgrade():
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)
    command.downgrade(alembic_cfg, "-1")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python migrate.py [upgrade|downgrade]")
        sys.exit(1)

    action = sys.argv[1].lower()
    if action == "upgrade":
        upgrade()
    elif action == "downgrade":
        downgrade()
    elif action == "sqlite":
        create_database()
    else:
        print("Unknown command:", action)
        print("Usage: python migrate.py [upgrade|downgrade]")
        sys.exit(1)
