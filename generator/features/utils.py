"""Utilities feature for the Jenkins File Generator."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from generator.core.base_feature import BaseFeature, FeatureConfig


class UtilsConfig(FeatureConfig):
    """Configuration model for the utils feature."""

    abort_running_builds: Optional[bool] = Field(
        default=True,
        description="If true, aborts any running builds before starting a new one.",
    )


class UtilsFeature(BaseFeature):
    """Feature for defining some utilities."""

    feature_name = "utils"

    def should_include(self, config: Dict[str, Any]) -> bool:
        return "utils" in config

    def get_config_model(self) -> BaseModel:
        return UtilsConfig
