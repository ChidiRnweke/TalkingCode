from dagster import Definitions, load_assets_from_modules
from dotenv import load_dotenv
from dataprocessing.orchestration.resources import AppConfigResource
from .orchestration import assets
from dataprocessing.log import setup_custom_logger

load_dotenv("config/.env.secret")

logger = setup_custom_logger("app_logger")


all_assets = load_assets_from_modules([assets])


defs = Definitions(
    assets=all_assets,
    resources={"app_config_resource": AppConfigResource.from_env()},
)
