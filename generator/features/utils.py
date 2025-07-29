"""Utilities feature for the Jenkins File Generator."""

from typing import Any, Dict
from pydantic import BaseModel

from generator.core.base_feature import BaseFeature, FeatureConfig


class UtilsConfig(FeatureConfig):
    """Configuration model for the utils feature."""


class UtilsFeature(BaseFeature):
    """Feature for defining some utilities."""

    feature_name = "utils"

    def should_include(self, config: Dict[str, Any]) -> bool:
        return "utils" in config

    def get_config_model(self) -> BaseModel:
        return UtilsConfig
