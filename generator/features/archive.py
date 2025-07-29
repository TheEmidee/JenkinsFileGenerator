"""Archive feature for the Jenkins File Generator.
This feature allows to archive the artifacts or build products created by the jenkins pipeline.

You can rotate the archives:
1. The folder pointed to by the `directory_path` will be renamed to the current date.
2. The script will keep the specified number of most recent directories in the parent folder.
"""

from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from generator.core.base_feature import BaseFeature, FeatureConfig


class RotateArchivesConfig(BaseModel):
    """Configuration model for the action of rotating the archives.."""

    enabled: bool = Field(
        default=False,
        description="Enable or disable the action of rotating the archives",
    )
    directory_path: Path = (
        Field(description="Path to the directory to rename with the current date"),
    )
    keep_count: int = Field(
        default=10,
        description="Number of directories to keep in the parent folder after directory_path has been renamed",
    )
    output_file_name: Optional[Path] = Field(
        default=None,
        description="Optional path to text file where the new directory name will be written to be re-used by other tasks",
    )

class UploadArchivesConfig(BaseModel):
    """Configuration model for the action of uploading the archives."""

    enabled: bool = Field(
        default=False,
        description="Enable or disable the action of uploading the archives",
    )


class ArchiveConfig(FeatureConfig):
    """Configuration model for the Archive feature."""

    additional_node_name: Optional[str] = Field(
        default=None,
        description="Additional jenkins node tags to use if you want the archiving tasks to be executed on specific nodes.",
    )
    rotate_archives: RotateArchivesConfig = Field(
        default_factory=RotateArchivesConfig,
        description="Configuration for rotating archives",
    )
    upload_archives: UploadArchivesConfig = Field(
        default_factory=UploadArchivesConfig,
        description="Configuration for uploading archives",
    )


class ArchiveFeature(BaseFeature):
    """Feature for manipulating the Archive created by the jenkins pipeline."""

    feature_name = "archive"

    def should_include(self, config: Dict[str, Any]) -> bool:
        return "archive" in config

    def get_config_model(self) -> BaseModel:
        return ArchiveConfig
