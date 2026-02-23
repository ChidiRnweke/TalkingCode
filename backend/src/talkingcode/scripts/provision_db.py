import asyncio
import os
from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from talkingcode.environment.env import SecretsReader, SecretsNotFoundError

logger = structlog.getLogger("talkingcode.provision")


async def provision_database() -> None:
    """Provision database and role, then update Infisical secrets."""
    reader = SecretsReader.from_env()

    # 1. Check if app DATABASE_URL already exists (idempotency)
    try:
        app_db_url = reader.read_optional("DATABASE_URL")
        if app_db_url and "localhost" not in app_db_url:
            logger.info("provision.db.exists", url=app_db_url.split("@")[-1])
            # For now, we trust it exists if it's set to something non-localhost
            # return
    except Exception:
        pass

    # 2. Read admin DB creds from ENV (required for provisioning)
    # These should be passed to the setup service
    admin_user = os.getenv("POSTGRES_ADMIN_USER", "postgres")
    admin_password = os.getenv("POSTGRES_ADMIN_PASSWORD")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "talkingcode")
    db_user = os.getenv("DB_USER", "talkingcode")
    db_password = os.getenv("DB_PASSWORD", "talkingcode")

    if not admin_password:
        logger.warning("provision.admin_password.missing", message="Using empty password for admin")
        admin_password = ""

    admin_url = f"postgresql+asyncpg://{admin_user}:{admin_password}@{db_host}:{db_port}/postgres"

    # 3. Create database and role idempotently
    logger.info("provision.starting", host=db_host, db=db_name)
    
    engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    async with engine.connect() as conn:
        # Create role if not exists
        await conn.execute(text(f"DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '{db_user}') THEN CREATE ROLE {db_user} WITH LOGIN PASSWORD '{db_password}'; END IF; END $$"))
        
        # Create database if not exists
        result = await conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
        if not result.scalar():
            await conn.execute(text(f"CREATE DATABASE {db_name} OWNER {db_user}"))
            logger.info("provision.db.created", name=db_name)
        else:
            logger.info("provision.db.already_exists", name=db_name)
            
        # Grant privileges
        await conn.execute(text(f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user}"))

    await engine.dispose()

    # 4. Write/overwrite app DATABASE_URL secret back to Infisical if enabled
    # We use a special admin client if needed or just the current reader if it has write access
    # Actually, the plan says "Write/overwrite app DATABASE_URL secret".
    # For now, let's just log what the URL should be.
    # In a real environment, we'd use the Infisical client to set the secret.
    
    final_db_url = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    # Update Infisical if enabled
    enabled = os.getenv("INFISICAL_ENABLED")
    if enabled:
        try:
            from infisical_client import (
                AuthenticationOptions,
                ClientSettings,
                InfisicalClient,
                UniversalAuthMethod,
                CreateSecretOptions
            )
            client_id = os.getenv("INFISICAL_ADMIN_CLIENT_ID") or os.getenv("INFISICAL_CLIENT_ID")
            client_secret = os.getenv("INFISICAL_ADMIN_CLIENT_SECRET") or os.getenv("INFISICAL_CLIENT_SECRET")
            project_id = os.getenv("INFISICAL_PROJECT_ID")
            environment = os.getenv("INFISICAL_ENVIRONMENT")
            url = os.getenv("INFISICAL_URL")

            if client_id and client_secret and project_id and environment and url:
                auth = UniversalAuthMethod(client_id=client_id, client_secret=client_secret)
                auth_options = AuthenticationOptions(universal_auth=auth)
                client_settings = ClientSettings(auth=auth_options, site_url=url)
                client = InfisicalClient(client_settings)
                
                client.createSecret(
                    options=CreateSecretOptions(
                        environment=environment,
                        project_id=project_id,
                        secret_name="DATABASE_URL",
                        secret_value=final_db_url,
                    )
                )
                logger.info("provision.infisical.updated", var="DATABASE_URL")
        except Exception as inf_err:
            logger.warning("provision.infisical.failed", error=str(inf_err))

    logger.info("provision.completed", database_url=final_db_url.replace(db_password, "****"))


if __name__ == "__main__":
    asyncio.run(provision_database())
