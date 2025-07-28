"""This module defines the Properties feature for Jenkins pipelines."""

from typing import Any, Dict, List
from pydantic import BaseModel

from generator.core.base_feature import BaseFeature, FeatureConfig


class PropertiesConfig(FeatureConfig):
    """Configuration for the pipeline properties.
    You must type the properties exactly as you would in a Jenkinsfile.
    For example:
    buildDiscarder( logRotator( numToKeepStr: '10' ) )
    """

    items: List[str] = None


class PropertiesFeature(BaseFeature):
    """Feature for defining the pipeline properties."""

    feature_name = "properties"

    def should_include(self, config: Dict[str, Any]) -> bool:
        return "properties" in config

    def get_config_model(self) -> BaseModel:
        return PropertiesConfig
