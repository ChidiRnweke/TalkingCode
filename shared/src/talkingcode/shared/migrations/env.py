import os
from logging import getLogger
from logging.config import fileConfig

import pgvector.sqlalchemy
from alembic import context
from sqlalchemy import Connection, create_engine, text
from talkingcode.shared.database import Base
from talkingcode.shared.env import SecretsReader, get_env_or_raise
from talkingcode.shared.telemetry import configure_telemetry

logger = getLogger("app_logger")

config = context.config

telemetry_enabled = os.getenv("TELEMETRY_ENABLED")
if telemetry_enabled:
    telemetry_endpoint = get_env_or_raise("TELEMETRY_ENDPOINT")
    configure_telemetry(telemetry_endpoint)
secrets_reader = SecretsReader.from_env()
url = secrets_reader.read_secret("MIGRATIONS_DATABASE_URL")


# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def do_run_migrations(connection: Connection) -> None:
    connection.dialect.ischema_names["vector"] = pgvector.sqlalchemy.Vector  # type: ignore
    connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = create_engine(url)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            do_run_migrations(connection)
            context.run_migrations()


try:
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
    logger.info("Migrations run successfully")
except Exception as e:
    logger.error(f"Error running migrations: {e}", exc_info=True)
    raise e
