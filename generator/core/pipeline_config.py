"""Configuration for the Jenkins pipeline generator.
This is what should be at the top of the config file.
It defines all the general settings, such as the project configuration, the global jenkins configuration, and the features to be used in the pipeline."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ProjectConfig(BaseModel):
    """Project specific configuration."""

    name: str = Field(
        description="The project name. Used in various places in the Jenkinsfile."
    )


class JenkinsConfig(BaseModel):
    """Jenkins specific configuration."""

    workspace_suffix: Optional[str] = Field(
        default=None, description="Suffix to append to the Jenkins workspace path"
    )
    default_node_names: str = Field(
        description="The names of the nodes to use by default by Jenkins for each stage"
    )


class PipelineConfig(BaseModel):
    """Configuration for the Jenkins pipeline generator."""

    pipeline_name: str = Field(
        description="Pipeline name. Used as an identifier at the top of the jenkinsfile"
    )
    project: ProjectConfig = Field(description="Project Configuration")
    jenkins: JenkinsConfig = Field(description="Jenkins Configuration")
    features: Dict[str, Any] = Field(
        default={},
        description="All the features that you want to use in your jenkins file",
    )
