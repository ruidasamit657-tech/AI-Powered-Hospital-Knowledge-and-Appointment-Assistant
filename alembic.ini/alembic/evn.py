# pyright: reportAttributeAccessIssue=false
# pylint: disable=no-member

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add the project root to sys.path. This file is in <project>/alembic.ini/alembic.
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, os.fspath(project_root))

# Import your models and Base
# pylint: disable=wrong-import-position
from app.db.base import Base
import app.db.models.user as _user_model
import app.db.models.department as _department_model
import app.db.models.doctor as _doctor_model
import app.db.models.patient as _patient_model
import app.db.models.appointment as _appointment_model
import app.db.models.knowledge_document as _knowledge_document_model
import app.db.models.knowledge_chunk as _knowledge_chunk_model
from app.core.config import settings
# pylint: enable=wrong-import-position

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config  # pyright: ignore[reportAttributeAccessIssue]

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override the sqlalchemy.url with the one from settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(  # pyright: ignore[reportAttributeAccessIssue]
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():  # pyright: ignore[reportAttributeAccessIssue]
        context.run_migrations()  # pyright: ignore[reportAttributeAccessIssue]


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(  # pyright: ignore[reportAttributeAccessIssue]
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():  # pyright: ignore[reportAttributeAccessIssue]
            context.run_migrations()  # pyright: ignore[reportAttributeAccessIssue]


if context.is_offline_mode():  # pyright: ignore[reportAttributeAccessIssue]
    run_migrations_offline()
else:
    run_migrations_online()