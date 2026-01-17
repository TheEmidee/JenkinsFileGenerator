"""Feature Registry for managing and auto-discovering features in the generator."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Dict, List, Type

if TYPE_CHECKING:
    from generator.core.base_feature import BaseFeature

from generator import logger


class FeatureRegistry:
    """Registry for auto-discovering and managing features"""

    _instance = None
    _features: ClassVar[Dict[str, Type[BaseFeature]]] = {}
    _modules_loaded = False

    def __new__(cls) -> "FeatureRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register_feature(cls, feature_class: Type[BaseFeature]) -> None:
        """Register a feature class"""
        cls._features[feature_class.feature_name] = feature_class
        cls._modules_loaded = True

    @classmethod
    def get_all_features(cls) -> Dict[str, Type[BaseFeature]]:
        """Get all registered features."""
        return cls._features.copy()

    @classmethod
    def fix_missing_dependencies(cls, selected_features: List[BaseFeature]) -> List[BaseFeature]:
        """Returns an updated list of the features, including any missing dependencies."""
        all_features = cls.get_all_features()

        def add_missing_dependencies(feature: BaseFeature) -> None:
            for dep_name in feature.dependencies:  # getattr(feature, "dependencies", []):
                has_match = any(feature_type.feature_name == dep_name for feature_type in selected_features)

                if not has_match:
                    logger.info(
                        "Missing dependency '%s' for feature '%s'",
                        dep_name,
                        feature.feature_name,
                    )
                    dep_class = all_features.get(dep_name)
                    if dep_class is not None:
                        logger.info("Added dependency '%s' with default configuration", dep_name)
                        dependency = dep_class()
                        selected_features.append(dependency)
                        add_missing_dependencies(dependency)

        for feature in selected_features:
            add_missing_dependencies(feature)

        return selected_features


def list_all_features() -> int:
    """Outputs the names of all registered features in the output log"""
    try:
        logger.info("List of all the registered features:")
        for _, feature_class in FeatureRegistry().get_all_features().items():
            logger.info("Feature: %s", feature_class.feature_name)

        return 0
    except Exception as e:
        logger.error("Error while listing the registered features: %s", e)
        return 1
