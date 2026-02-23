"""Database provisioning script.

Follows the ReceiptToRecipe provision-db.js pattern:
1. Authenticate to admin Infisical project.
2. Authenticate to app Infisical project.
3. If app DATABASE_URL exists, short-circuit success.
4. Read admin DB creds (POSTGRES_ADMIN_USER, POSTGRES_ADMIN_PASSWORD, POSTGRES_HOST, POSTGRES_PORT).
5. Create database + role idempotently.
6. Grant DB/schema privileges.
7. Write/overwrite app DATABASE_URL secret.
8. Write default config keys only if missing (DB_HOST, DB_PORT, DB_NAME, DB_USER).
"""

import asyncio
import os
import secrets as stdlib_secrets

import structlog
from infisical_client import (
    AuthenticationOptions,
    ClientSettings,
    CreateSecretOptions,
    GetSecretOptions,
    InfisicalClient,
    UniversalAuthMethod,
    UpdateSecretOptions,
)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

logger = structlog.getLogger("talkingcode.provision")


def _generate_password(length: int = 32) -> str:
    return stdlib_secrets.token_hex(length)[:length]


def _connect_infisical(client_id: str, client_secret: str, site_url: str) -> InfisicalClient:
    auth = UniversalAuthMethod(client_id=client_id, client_secret=client_secret)
    auth_options = AuthenticationOptions(universal_auth=auth)
    client_settings = ClientSettings(auth=auth_options, site_url=site_url)
    return InfisicalClient(client_settings)


def _get_secret_if_exists(
    client: InfisicalClient, project_id: str, environment: str, secret_name: str
) -> str | None:
    try:
        secret = client.getSecret(
            options=GetSecretOptions(
                environment=environment,
                project_id=project_id,
                secret_name=secret_name,
            )
        )
        return secret.secret_value
    except Exception:
        return None


def _update_or_create_secret(
    client: InfisicalClient,
    project_id: str,
    environment: str,
    secret_name: str,
    secret_value: str,
) -> None:
    """Force update or create a secret. Use for credentials that MUST match."""
    try:
        client.updateSecret(
            options=UpdateSecretOptions(
                environment=environment,
                project_id=project_id,
                secret_name=secret_name,
                secret_value=secret_value,
            )
        )
        logger.info("provision.secret.updated", key=secret_name)
    except Exception:
        try:
            client.createSecret(
                options=CreateSecretOptions(
                    environment=environment,
                    project_id=project_id,
                    secret_name=secret_name,
                    secret_value=secret_value,
                )
            )
            logger.info("provision.secret.created", key=secret_name)
        except Exception as e:
            raise RuntimeError(f"Failed to save secret '{secret_name}': {e}") from e


def _create_secret_only(
    client: InfisicalClient,
    project_id: str,
    environment: str,
    secret_name: str,
    secret_value: str,
) -> None:
    """Only create secret if it doesn't exist. Use for config like Host/Port."""
    existing = _get_secret_if_exists(client, project_id, environment, secret_name)
    if existing is not None:
        logger.info("provision.secret.exists", key=secret_name)
        return
    try:
        client.createSecret(
            options=CreateSecretOptions(
                environment=environment,
                project_id=project_id,
                secret_name=secret_name,
                secret_value=secret_value,
            )
        )
        logger.info("provision.secret.default_created", key=secret_name)
    except Exception as e:
        logger.warning("provision.secret.default_failed", key=secret_name, error=str(e))


async def provision_database() -> str:
    """Provision database and user, then store connection string in Infisical.

    Returns the DATABASE_URL.
    """
    logger.info("provision.starting")

    # --- Resolve Infisical credentials ---
    site_url = os.getenv("INFISICAL_URL")
    infisical_enabled = os.getenv("INFISICAL_ENABLED")

    admin_client_id = os.getenv("INFISICAL_ADMIN_CLIENT_ID")
    admin_client_secret = os.getenv("INFISICAL_ADMIN_CLIENT_SECRET")
    admin_project_id = os.getenv("INFISICAL_ADMIN_PROJECT_ID")

    app_client_id = os.getenv("INFISICAL_CLIENT_ID")
    app_client_secret = os.getenv("INFISICAL_CLIENT_SECRET")
    app_project_id = os.getenv("INFISICAL_PROJECT_ID")
    app_environment = os.getenv("INFISICAL_ENVIRONMENT")

    db_name = os.getenv("DB_NAME", "talkingcode")
    db_user = os.getenv("DB_USER", "talkingcode")

    # --- Infisical mode: dual client (admin + app) ---
    if infisical_enabled and site_url and admin_client_id and app_client_id:
        if not admin_client_secret or not admin_project_id:
            raise RuntimeError(
                "Missing admin Infisical credentials "
                "(INFISICAL_ADMIN_CLIENT_ID, INFISICAL_ADMIN_CLIENT_SECRET, INFISICAL_ADMIN_PROJECT_ID)"
            )
        if not app_client_secret or not app_project_id or not app_environment:
            raise RuntimeError(
                "Missing app Infisical credentials "
                "(INFISICAL_CLIENT_ID, INFISICAL_CLIENT_SECRET, INFISICAL_PROJECT_ID, INFISICAL_ENVIRONMENT)"
            )

        logger.info("provision.infisical.connecting_admin")
        admin_infisical = _connect_infisical(admin_client_id, admin_client_secret, site_url)

        logger.info("provision.infisical.connecting_app")
        app_infisical = _connect_infisical(app_client_id, app_client_secret, site_url)

        # Check if DATABASE_URL already exists in app project -> short-circuit
        existing_db_url = _get_secret_if_exists(
            app_infisical, app_project_id, app_environment, "DATABASE_URL"
        )
        if existing_db_url:
            logger.info("provision.db.exists", hint="DATABASE_URL already in Infisical")
            return existing_db_url

        # Read admin DB creds from admin Infisical project
        admin_user = _get_secret_if_exists(
            admin_infisical, admin_project_id, app_environment, "POSTGRES_ADMIN_USER"
        )
        admin_password = _get_secret_if_exists(
            admin_infisical, admin_project_id, app_environment, "POSTGRES_ADMIN_PASSWORD"
        )
        postgres_host = _get_secret_if_exists(
            admin_infisical, admin_project_id, app_environment, "POSTGRES_HOST"
        )
        postgres_port = _get_secret_if_exists(
            admin_infisical, admin_project_id, app_environment, "POSTGRES_PORT"
        ) or "5432"

        if not admin_user or not admin_password:
            raise RuntimeError(
                "Missing POSTGRES_ADMIN_USER or POSTGRES_ADMIN_PASSWORD in admin Infisical project"
            )
        if not postgres_host:
            raise RuntimeError("Missing POSTGRES_HOST in admin Infisical project")

        # Generate a new password for the app DB user
        db_password = _generate_password(32)

        # Provision the database
        database_url = await _provision_pg(
            admin_user=admin_user,
            admin_password=admin_password,
            host=postgres_host,
            port=postgres_port,
            db_name=db_name,
            db_user=db_user,
            db_password=db_password,
        )

        # Write credentials to app Infisical project
        logger.info("provision.infisical.writing_secrets")

        # For CREDENTIALS: overwrite because we just generated a new password
        _update_or_create_secret(
            app_infisical, app_project_id, app_environment, "DATABASE_URL", database_url
        )

        # For CONFIG: only create if missing (don't overwrite manual changes)
        _create_secret_only(
            app_infisical, app_project_id, app_environment, "DB_HOST", postgres_host
        )
        _create_secret_only(
            app_infisical, app_project_id, app_environment, "DB_PORT", postgres_port
        )
        _create_secret_only(
            app_infisical, app_project_id, app_environment, "DB_NAME", db_name
        )
        _create_secret_only(
            app_infisical, app_project_id, app_environment, "DB_USER", db_user
        )

        logger.info("provision.completed")
        return database_url

    # --- Env-only mode: use env vars directly ---
    logger.info("provision.mode.env_only")
    admin_user = os.getenv("POSTGRES_ADMIN_USER", "postgres")
    admin_password = os.getenv("POSTGRES_ADMIN_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_password = os.getenv("DB_PASSWORD", "talkingcode")

    database_url = await _provision_pg(
        admin_user=admin_user,
        admin_password=admin_password,
        host=db_host,
        port=db_port,
        db_name=db_name,
        db_user=db_user,
        db_password=db_password,
    )

    logger.info("provision.completed", database_url=database_url.replace(db_password, "****"))
    return database_url


async def _provision_pg(
    *,
    admin_user: str,
    admin_password: str,
    host: str,
    port: str,
    db_name: str,
    db_user: str,
    db_password: str,
) -> str:
    """Create database + role idempotently and grant privileges."""
    admin_url = f"postgresql+asyncpg://{admin_user}:{admin_password}@{host}:{port}/postgres"

    logger.info("provision.pg.connecting", host=host, port=port, db=db_name)

    engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        async with engine.connect() as conn:
            # Check if database exists
            result = await conn.execute(
                text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
            )
            if not result.scalar():
                await conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                logger.info("provision.pg.db_created", name=db_name)
            else:
                logger.info("provision.pg.db_exists", name=db_name)

            # Check if role exists
            result = await conn.execute(
                text(f"SELECT 1 FROM pg_roles WHERE rolname = '{db_user}'")
            )
            if not result.scalar():
                await conn.execute(
                    text(f"CREATE USER \"{db_user}\" WITH PASSWORD '{db_password}'")
                )
                logger.info("provision.pg.user_created", name=db_user)
            else:
                await conn.execute(
                    text(f"ALTER USER \"{db_user}\" WITH PASSWORD '{db_password}'")
                )
                logger.info("provision.pg.user_password_updated", name=db_user)

            # Grant privileges and set owner
            await conn.execute(text(f'ALTER DATABASE "{db_name}" OWNER TO "{db_user}"'))
            await conn.execute(
                text(f'GRANT ALL PRIVILEGES ON DATABASE "{db_name}" TO "{db_user}"')
            )

        # Connect to the app database to grant schema privileges
        app_admin_url = f"postgresql+asyncpg://{admin_user}:{admin_password}@{host}:{port}/{db_name}"
        app_engine = create_async_engine(app_admin_url, isolation_level="AUTOCOMMIT")
        try:
            async with app_engine.connect() as conn:
                await conn.execute(text(f'GRANT ALL ON SCHEMA public TO "{db_user}"'))
                await conn.execute(
                    text(
                        f'ALTER DEFAULT PRIVILEGES IN SCHEMA public '
                        f'GRANT ALL ON TABLES TO "{db_user}"'
                    )
                )
                await conn.execute(
                    text(
                        f'ALTER DEFAULT PRIVILEGES IN SCHEMA public '
                        f'GRANT ALL ON SEQUENCES TO "{db_user}"'
                    )
                )
                # Hardening: revoke CREATE from public to prevent other users from creating tables
                await conn.execute(text("REVOKE CREATE ON SCHEMA public FROM PUBLIC"))
                logger.info("provision.pg.privileges_granted", db=db_name, user=db_user)
        finally:
            await app_engine.dispose()
    finally:
        await engine.dispose()

    return f"postgresql+asyncpg://{db_user}:{db_password}@{host}:{port}/{db_name}"


if __name__ == "__main__":
    asyncio.run(provision_database())
