from talkingcode.pipelines.config import IngestionConfig

from .metadata_ingestion import from_config as metadata_ingestion_from_config
from .metadata_ingestion.ingestion import MetadataIngestionService
from .transformations import TransformationPipeline
from .transformations import from_config as transformations_from_config


async def run_transformation_pipeline(config: IngestionConfig) -> None:
    """
    Run the pipeline with the given configuration. Runs both metadata ingestion and transformation steps.

    Args:
        config (IngestionConfig): The configuration object to use for running the pipeline.

    Returns:
        TransformationPipeline: The transformation pipeline object.
    """
    ingestion_service = metadata_ingestion_from_config(config)
    transformation_pipeline = transformations_from_config(config)
    await ingestion_service.fetch_and_persist_metadata()
    await transformation_pipeline.transform_all_repositories()


__all__ = [
    "MetadataIngestionService",
    "TransformationPipeline",
    "metadata_ingestion_from_config",
    "transformations_from_config",
    "run_transformation_pipeline",
]
