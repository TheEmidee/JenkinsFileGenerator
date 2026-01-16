"""Template context for Jenkinsfile generation.
This module defines the context passed to template rendering functions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from generator.core.base_feature import FeatureConfig
    from generator.core.pipeline_config import PipelineConfig


@dataclass
class TemplateContext:
    """Rich context passed to template rendering functions."""

    full_config: PipelineConfig
    feature_config: FeatureConfig
    global_values: Dict[str, Any]
