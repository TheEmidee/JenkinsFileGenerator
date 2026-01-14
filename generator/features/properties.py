"""
This module defines the Properties feature for Jenkins pipelines.
You must type the properties exactly as you would in a Jenkinsfile.
For example:
buildDiscarder( logRotator( numToKeepStr: '10' ) )
"""

from typing import Any, ClassVar, Dict, List, Type

from generator.core.base_feature import BaseFeature, FeatureConfig


class PropertiesConfig(FeatureConfig):
    """Configuration for the pipeline properties."""

    items: ClassVar[List[str]] = []


class PropertiesFeature(BaseFeature):
    """Feature for defining the pipeline properties."""

    feature_name = "properties"

    def should_include(self, config: Dict[str, Any]) -> bool:
        return "properties" in config

    def get_config_model(self) -> Type[FeatureConfig]:
        return PropertiesConfig
