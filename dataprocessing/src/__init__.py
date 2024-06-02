import logging
from dagster import Definitions, load_assets_from_modules
from dotenv import load_dotenv
from .orchestration import assets

load_dotenv("config/.env.secret")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


all_assets = load_assets_from_modules([assets])


defs = Definitions(
    assets=all_assets,
)
