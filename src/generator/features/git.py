"""This module defines the Git-related features and configurations for Jenkins pipelines."""

from typing import Any, Dict, List, Optional, Type

from pydantic import Field

from generator.core.base_feature import BaseFeature, FeatureConfig


class GitConfig(FeatureConfig):
    """Configuration model for the git properties."""

    checkout_code: str = Field(
        default="checkout scm",
        description=(
            "This property will be output in the jenkinsfile as is. You can generate a valid code by using the pipeline syntax page of Jenkins."
        ),
    )
    pre_checkout_tasks: Optional[List[str]] = Field(
        default=[],
        description="List of tasks to run before running the checkout.",
    )
    retry_count: Optional[int] = Field(
        default=1,
        description=(
            "Set to a value greater than 1 to try to checkout multiple times. "
            "This can help avoid the job to fail in some circumstances (for example with a github app)"
        ),
    )


class GitFeature(BaseFeature):
    """Feature for defining the git properties."""

    feature_name = "git"

    def should_include(self, config: Dict[str, Any]) -> bool:
        return "git" in config

    def get_config_model(self) -> Type[FeatureConfig]:
        return GitConfig
