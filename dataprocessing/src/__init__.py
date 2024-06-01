from dagster import Definitions, load_assets_from_modules
from dotenv import load_dotenv
from . import assets

load_dotenv("config/.env.secret")


all_assets = load_assets_from_modules([assets])


defs = Definitions(
    assets=all_assets,
)
