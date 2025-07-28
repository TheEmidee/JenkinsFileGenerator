"""This module defines the base feature class and configuration model for the Jenkinsfile generator.
It provides the structure for all pipeline features, including methods for rendering templates
and validating configurations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Type
from pydantic import BaseModel, PrivateAttr, ValidationError
from mako.lookup import TemplateLookup

from generator.core.pipeline_config import PipelineConfig
from generator.core.generated_blocks import GeneratedBlocks
from generator.core.template_context import TemplateContext
from generator.core.feature_registry import FeatureRegistry


class FeatureConfig(BaseModel, ABC):
    """Base class for feature configuration models."""

    _accumulator: Dict[str, Any] = PrivateAttr(default_factory=dict)


class BaseFeature(ABC):
    """Base class for all pipeline features"""

    feature_name: str = None  # Class attribute instead of property

    def __init_subclass__(cls, **kwargs):
        """Auto-register feature subclasses"""
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "feature_name") and cls.feature_name:
            FeatureRegistry().register_feature(cls)

    @property
    def dependencies(self) -> List[str]:
        """List of feature names this feature depends on."""
        return []

    @property
    def template_path(self) -> str:
        """Path to the Mako template file for this feature."""
        return f"{self.feature_name}.mako"

    @abstractmethod
    def should_include(self, config: Dict[str, Any]) -> bool:
        """Determine if this feature should be included based on config."""

    @abstractmethod
    def get_config_model(self) -> Type[BaseModel]:
        """Return the Pydantic model for validating this feature's config."""

    def get_feature_config(
        self, full_config: PipelineConfig, context: Any
    ) -> Dict[str, Any]:
        """Extract and validate this feature's config from the full config."""
        feature_config = full_config.features.get(self.feature_name, {})

        config_model = self.get_config_model()
        try:
            validated = config_model.model_validate(feature_config, context=context)
            return validated
        except ValidationError as e:
            raise ValueError(f"Invalid config for feature '{self.feature_name}': {e}") from e

    def render_blocks(
        self, context: TemplateContext, template_lookup: TemplateLookup
    ) -> GeneratedBlocks:
        """Render all template blocks for this feature."""
        try:
            template = template_lookup.get_template(self.template_path)
        except Exception as exc:
            raise FileNotFoundError(
                f"Template not found for feature '{self.feature_name}': {self.template_path}"
            ) from exc

        blocks = GeneratedBlocks()

        for block_type, block_value in blocks.blocks.items():
            try:
                block = self.render_block(block_type, context, template)
                block_value.append(block)
            except AttributeError:
                # Block not defined in template - that's OK
                pass
            except Exception as e:
                print(
                    f"Warning: Error rendering {block_type} for {self.feature_name}: {e}"
                )

        return blocks

    def render_block(self, block_type: str, context: TemplateContext, template) -> str:
        """Render a single block for this feature."""
        rendered = template.get_def(block_type).render_unicode(**context.__dict__)
        if rendered.strip():
            cleaned = rendered.strip()  # re.sub(r'\n\s*\n', '\n', rendered.strip())
            if context.global_values.get("output_feature_sections", True):
                cleaned = f"// === Feature: {self.feature_name} ===\n{cleaned}\n// === End feature: {self.feature_name} ==="

            return cleaned

        return ""
