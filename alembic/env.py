"""Alembic migration environment.

Reads the database URL and the target metadata from the application's
own configuration so migrations and runtime always agree on what the
schema should be.
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.core.config import get_settings
from app.core.database import Base

# Alembic Config object: provides access to alembic.ini values.
config = context.config

# Inject the database URL from application settings.
config.set_main_option("sqlalchemy.url", get_settings().database_url)

# Configure logging from alembic.ini if a file is configured.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata: drives autogenerate by comparing models to DB.
# Domain modules are imported here so their models are registered on
# Base.metadata before autogeneration runs. (Imports are placed at
# function scope in run_migrations_* to avoid side effects at module
# import time.)
target_metadata = Base.metadata


def _import_models() -> None:
    """Import all modules that define ORM models.

    Add new imports here when a new domain module introduces models.
    """
    # Future imports go here, e.g.:
    # from app.transactions import models
    # from app.categories import models


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the context with just a URL and not an Engine, useful
    for generating SQL scripts without a live database.
    """
    _import_models()
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using a live Engine."""
    _import_models()
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
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
