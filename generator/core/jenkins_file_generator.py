from pathlib import Path
from typing import Any, Dict, List
from mako.lookup import TemplateLookup

import os
import yaml

from .. import logger
from .template_context import TemplateContext
from .pipeline_config import PipelineConfig
from .generated_blocks import GeneratedBlocks
from .base_feature import BaseFeature
from .dependency_resolver import DependencyResolver
from .feature_registry import FeatureRegistry

class JenkinsfileGenerator:
    """Main generator class that orchestrates the entire process."""

    def __init__(self):
        file_path = os.path.realpath(__file__)
        templates_dir = os.path.join(os.path.dirname(file_path), "../templates")

        self.templates_dir = Path(templates_dir)
        self.template_lookup = TemplateLookup( directories=[str(self.templates_dir)] )
        self.base_template_path = "base_jenkinsfile.mako"

    def generate_jenkinsfile(self, config_path: str, output_path: str) -> None:
        """Main method to generate a Jenkinsfile from configuration."""

        config = self.load_config(config_path)
        selected_features = self.select_features(config)
        logger.info(f"Selected {len(selected_features)} features: {[f.feature_name for f in selected_features]}")

        ordered_features = DependencyResolver.resolve_dependencies(selected_features)
        logger.info(f"Feature order (after dependency resolution): {[f.feature_name for f in ordered_features]}")

        all_blocks = GeneratedBlocks()
        global_values = {
            'generator_version': '1.0.0',
            'output_feature_sections': False
        }

        for feature in ordered_features:
            try:
                feature_config = feature.get_feature_config(config)
                context = TemplateContext(
                    full_config=config,
                    feature_config=feature_config,
                    global_values=global_values
                )

                blocks = feature.render_blocks(context, self.template_lookup)

                all_blocks.merge_with(blocks)

            except Exception as e:
                raise RuntimeError(f"Failed to process feature '{feature.feature_name}': {e}")

        self.render_final_jenkinsfile(all_blocks, config, global_values, output_path)

    def load_config(self, config_path: str) -> PipelineConfig:
        """Load and parse YAML configuration file."""
        try:
            with open(config_path, 'r') as f:
                yaml_contents = yaml.safe_load(f)
                return PipelineConfig(**yaml_contents)
        except Exception as e:
            raise ValueError(f"Failed to load config file '{config_path}': {e}")

    def select_features(self, config: PipelineConfig) -> List[BaseFeature]:
        """Select and instantiate features based on configuration."""
        selected_features : List[BaseFeature] = []
        
        for _, feature_class in FeatureRegistry().get_all_features().items():
            feature_instance = feature_class()
            if feature_instance.should_include(config.features):
                selected_features.append(feature_instance)

        selected_features = FeatureRegistry.fix_missing_dependencies(selected_features)

        return selected_features
    
    def render_final_jenkinsfile(self, blocks: GeneratedBlocks, config: PipelineConfig, global_values: Dict[str, Any], output_path: str) -> None:
        """Render the final Jenkinsfile using the base template."""
        try:
            base_template = self.template_lookup.get_template(self.base_template_path)
        except Exception as e:
            raise FileNotFoundError(f"Base template not found: {self.base_template_path}")

        try:
            d = {k: "\n".join(v or []) for k, v in blocks.blocks.items()}
            
            # for k, v in global_values.items():
            #     d.update( { k: v } )

            d.update( { "global_values" : global_values } )
            d.update( { "full_config" : config } )

            rendered = base_template.render_unicode(**d).strip().encode('utf-8', 'replace')

        except Exception as e:
            raise RuntimeError(f"Failed to render base template: {e}")
        
        with open(output_path, 'wb') as f:
            f.write(rendered)