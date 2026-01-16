"""Configuration for the Jenkins pipeline generator.
This is what should be at the top of the config file.
It defines all the general settings, such as the project configuration,
the global jenkins configuration, and the features to be used in the pipeline."""

from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, ValidationInfo, model_validator

from generator import logger


class ProjectConfig(BaseModel):
    """Project specific configuration."""

    name: str = Field(description="The project name. Used in various places in the Jenkinsfile.")


class JenkinsConfig(BaseModel):
    """Jenkins specific configuration."""

    workspace_suffix: Optional[str] = Field(default=None, description="Suffix to append to the Jenkins workspace path")
    default_node_names: str = Field(description="The names of the nodes to use by default by Jenkins for each stage")


class PipelineConfig(BaseModel):
    """Configuration for the Jenkins pipeline generator."""

    pipeline_name: str = Field(description="Pipeline name. Used as an identifier at the top of the jenkinsfile")
    customization_folder: Optional[Path] = Field(
        default=None,
        description=(
            "Path to a folder containing templates to use to override specific parts of some features."
            "The path can be absolute, or relative to the config file"
        ),
    )
    project: ProjectConfig = Field(description="Project Configuration")
    jenkins: JenkinsConfig = Field(description="Jenkins Configuration")
    features: Dict[str, Any] = Field(
        default={},
        description="All the features that you want to use in your jenkins file",
    )

    @model_validator(mode="after")
    def validate_model(self, info: ValidationInfo) -> "PipelineConfig":
        if not info.context:
            raise RuntimeError("The validation info must have a context")

        if self.customization_folder is not None:
            if not self.customization_folder.is_absolute():
                # Resolve relative to config file directory
                config_dir = Path(info.context.config_file_path).parent
                self.customization_folder = (config_dir / self.customization_folder).resolve()
                logger.debug(
                    "Resolved customization_folder relative to config file: %s",
                    self.customization_folder,
                )

            if not self.customization_folder.is_dir():
                raise ValueError("customization_folder does not point to a valid folder")

            logger.info("Resolved customization_folder: %s", self.customization_folder)

        return self
