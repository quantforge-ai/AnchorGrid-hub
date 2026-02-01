"""
Alembic Environment Configuration - NeonDB

Handles core table migrations (tenants, users, api_keys) on NeonDB.
Uses SYNC connection for Alembic compatibility.
"""
import re
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Import models so Alembic can detect them
from anchorgrid.db.models import Base, Tenant, User, APIKey
from anchorgrid.core.config import settings

# Alembic Config object
config = context.config


def get_url() -> str:
    """Get database URL for migrations (sync driver)"""
    url = settings.DATABASE_URL or ""
    
    # Keep psycopg2 for sync operations (Alembic prefers sync)
    # If using asyncpg URL, convert back to psycopg2
    if "+asyncpg" in url:
        url = url.replace("+asyncpg", "+psycopg2")
    
    # Ensure we have psycopg2 driver
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    
    return url


# Set database URL from settings
config.set_main_option("sqlalchemy.url", get_url())

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData for autogenerate (exclude OHLCV - that's in TimescaleDB)
target_metadata = Base.metadata


def include_object(object, name, type_, reflected, compare_to):
    """Filter which tables to include in migrations"""
    # Exclude OHLCV table (managed by TimescaleDB migrations)
    if type_ == "table" and name == "ohlcv":
        return False
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with sync engine."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
