"""Archive feature for the Jenkins File Generator.
This feature allows to archive the artifacts or build products created by the jenkins pipeline.
It also allows to upload the archives to an S3 bucket.

Both actions have the same behavior:
1. The local folder will be copied over to the shared folder / s3 bucket with the current date
2. If a directory with the same name already exists, an incremental suffix will be added (_01, _02, etc...)
3. Only the specified number of most recent directories in the parent folder will be kept, older ones will be deleted.
4. Optionally, a slack notification can be sent on completion of the action.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, Field

from generator.core.base_feature import BaseFeature, FeatureConfig


class SlackNotificationConfig(BaseModel):
    """Configuration model for Slack notifications."""

    enabled: bool = Field(
        default=False,
        description="Enable or disable Slack notifications",
    )
    channel: str = Field(
        default="",
        description="Slack channel to send notifications to",
    )
    message_template: str = Field(
        default="",
        description="Template for the notification message",
    )


class RotateArchivesConfig(BaseModel):
    """Configuration model for the action of rotating the archives.."""

    enabled: bool = Field(
        default=False,
        description="Enable or disable the action of rotating the archives",
    )
    directory_path: Path = Field(description="Path to the directory to rename with the current date")
    keep_count: int = Field(
        default=10,
        description="Number of directories to keep in the parent folder after directory_path has been renamed",
    )
    folder_output_file_name: Optional[Path] = Field(
        default=None,
        description="Optional path to text file where the new directory name will be written to be re-used by other tasks",
    )
    slack: Optional[SlackNotificationConfig] = Field(
        default=None,
        description="Slack configuration",
    )


class UploadArchivesConfig(BaseModel):
    """Configuration model for the action of uploading the archives."""

    enabled: bool = Field(
        default=False,
        description="Enable or disable the action of uploading the archives",
    )
    local_folder: Optional[Path] = Field(
        default=None,
        description=(
            "Path to the local folder containing the archives to upload. Optional. "
            "If you're using rotate_archives, jenkins will set the local folder path with the contents of output_file."
        ),
    )
    bucket_name: str = Field(default="", description="Name of the S3 bucket to upload the archives to")
    region: str = Field(default="", description="AWS region where the S3 bucket is located")
    access_key: str = Field(default="", description="Access key for AWS S3 authentication")
    secret_key: str = Field(default="", description="Secret key for AWS S3 authentication")
    destination_folder: str = Field(default="", description="Destination folder in the S3 bucket where the archives will be uploaded")
    keep_count: int = Field(default=-1, description="Number of archives to keep in the S3 bucket. If lower than 1, all archives will be kept.")
    output_file_name: Optional[Path] = Field(
        default=None, description="Optional path to text file where the download URLs of uploaded archives will be written"
    )
    slack: Optional[SlackNotificationConfig] = Field(default=None, description="Slack configuration")


class ArchiveConfig(FeatureConfig):
    """Configuration model for the Archive feature."""

    additional_node_name: Optional[str] = Field(
        default=None, description="Additional jenkins node tags to use if you want the archiving tasks to be executed on specific nodes."
    )
    rotate_archives: RotateArchivesConfig = Field(description="Configuration for rotating archives")
    upload_archives: UploadArchivesConfig = Field(description="Configuration for uploading archives")


class ArchiveFeature(BaseFeature):
    """Feature for manipulating the Archive created by the jenkins pipeline."""

    feature_name = "archive"

    def should_include(self, config: Dict[str, Any]) -> bool:
        return "archive" in config

    def get_config_model(self) -> Type[FeatureConfig]:
        return ArchiveConfig
    
    @property
    def dependencies(self) -> list[str]:
        return ["python"]
