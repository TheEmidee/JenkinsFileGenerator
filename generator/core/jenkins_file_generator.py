"""The main entry point for generating a Jenkinsfile from a configuration file."""

from pathlib import Path
from typing import Any, Dict, List
from mako.lookup import TemplateLookup

import re
import yaml

from generator import logger
from generator.core import constants

from generator.core.template_context import TemplateContext
from generator.core.pipeline_config import PipelineConfig
from generator.core.generated_blocks import GeneratedBlocks
from generator.core.base_feature import BaseFeature
from generator.core.dependency_resolver import DependencyResolver
from generator.core.feature_registry import FeatureRegistry


class JenkinsfileGenerator:
    """Main generator class that orchestrates the entire process."""

    def __init__(self):
        self.templates_dir = constants.TEMPLATES_FOLDER
        self.base_template_path = "base_jenkinsfile.mako"
        self.template_lookup = None

    def __create_template_lookup(self, config: PipelineConfig):
        directories=[
            str(self.templates_dir)
            ]
        
        if config.customization_folder is not None:
            directories.insert(0,str(config.customization_folder))
            
        self.template_lookup = TemplateLookup(directories=directories)

    def generate_jenkinsfile(self, config_path: Path, output_path: Path, blackboard_data: str = "") -> None:
        """Main method to generate a Jenkinsfile from configuration."""

        config = self.__load_config(config_path, blackboard_data)
        self.__create_template_lookup(config)
        
        selected_features = self.__select_features(config)
        logger.info(
            "Selected %s features: %s",
            len(selected_features),
            [f.feature_name for f in selected_features],
        )

        ordered_features = DependencyResolver.resolve_dependencies(selected_features)
        logger.info(
            "Feature order (after dependency resolution): %s",
            [f.feature_name for f in ordered_features],
        )

        all_blocks = GeneratedBlocks()
        global_values = {
            "generator_version": "1.0.0", 
            "output_feature_sections": False, 
            "source_yaml_file": config_path,
            "blackboard_data": blackboard_data,
            "customization" : {
                file.stem: file.name
                for file in Path(config.customization_folder).rglob("*.mako")
            }
        }

        for feature in ordered_features:
            try:
                validation_context = {"config_file_path": config_path}
                feature_config = feature.get_feature_config(config, validation_context)
                context = TemplateContext(
                    full_config=config,
                    feature_config=feature_config,
                    global_values=global_values,
                )

                blocks = feature.render_blocks(context, self.template_lookup)

                all_blocks.merge_with(blocks)

            except Exception as e:
                raise RuntimeError(
                    f"Failed to process feature '{feature.feature_name}': {e}"
                ) from e

        self.__render_final_jenkinsfile(all_blocks, config, global_values, output_path)

    def __load_config(self, config_path: str, blackboard_data: str = "") -> PipelineConfig:
        """Load and parse YAML configuration file."""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                yaml_str = f.read()

            if blackboard_data != '':
                blackboard_data_dict: dict[str, str] = dict(item.split('=') for item in blackboard_data.split(','))

                for key, value in blackboard_data_dict.items():
                    logger.info(
                        "Replace blackboard data key %s by %s",
                        key, value,
                    )
                    placeholder = f"^BLACKBOARD_DATA.{key}^"
                    yaml_str = yaml_str.replace(placeholder, value)

                remaining_tokens = re.findall(r'\^BLACKBOARD_DATA\.[^\^]+\^', yaml_str)
                if remaining_tokens:
                    raise ValueError(f"Unresolved BLACKBOARD_DATA tokens in config: {remaining_tokens}")

            yaml_contents = yaml.safe_load(yaml_str)
            validation_context = {"config_file_path": config_path}
            return PipelineConfig.model_validate(
                yaml_contents, context=validation_context
            )
        except Exception as e:
            raise ValueError(f"Failed to load config file '{config_path}': {e}") from e

    def __select_features(self, config: PipelineConfig) -> List[BaseFeature]:
        """Select and instantiate features based on configuration."""
        selected_features: List[BaseFeature] = []

        for _, feature_class in FeatureRegistry().get_all_features().items():
            feature_instance = feature_class()
            if feature_instance.should_include(config.features):
                selected_features.append(feature_instance)

        selected_features = FeatureRegistry.fix_missing_dependencies(selected_features)

        return selected_features

    def __render_final_jenkinsfile(
        self,
        blocks: GeneratedBlocks,
        config: PipelineConfig,
        global_values: Dict[str, Any],
        output_path: str,
    ) -> None:
        """Render the final Jenkinsfile using the base template."""
        try:
            base_template = self.template_lookup.get_template(self.base_template_path)
        except Exception as e:
            raise FileNotFoundError(
                f"Base template not found: {self.base_template_path}"
            ) from e

        try:
            d = {k: "\n".join(v or []) for k, v in blocks.blocks.items()}

            # for k, v in global_values.items():
            #     d.update( { k: v } )

            d.update({"global_values": global_values})
            d.update({"full_config": config})

            rendered = (
                base_template.render_unicode(**d).strip().encode("utf-8", "replace")
            )

        except Exception as e:
            raise RuntimeError(f"Failed to render base template: {e}") from e

        with open(output_path, "wb") as f:
            f.write(rendered)
