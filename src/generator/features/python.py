"""
This module defines the python feature for Jenkins pipelines.

This feature will create 2 additional functions:
* activatePythonEnvironment which will call the script defined in the config with the venv_activation_script_path
* executePythonScript which will execute an executable in the virtual environment's Scripts folder
"""

from typing import Any, Dict, Type

from pydantic import Field, ValidationInfo, model_validator

from generator.core.base_feature import BaseFeature, FeatureConfig


class PythonConfig(FeatureConfig):
    """Configuration for the pipeline properties."""

    venv_activation_script_path: str = Field(
        description=(
            "The path to the virtual environment activation script."
            "This must point to a script that can be sourced to activate the virtual environment."
        )
    )
    venv_folder: str = Field(
        description="The path to the virtual environment folder after it has been created by executing venv_activation_script_path.",
    )

    @model_validator(mode="after")
    def validate_model(self, info: ValidationInfo) -> "PythonConfig":
        if self.venv_folder == "":
            raise ValueError("venv_folder cannot be an empty string")

        if not self.venv_folder.endswith("/"):
            self.venv_folder += "/"

        return self


class PythonFeature(BaseFeature):
    """Feature for helper functions to use python packages."""

    feature_name = "python"

    def should_include(self, config: Dict[str, Any]) -> bool:
        return "python" in config

    def get_config_model(self) -> Type[FeatureConfig]:
        return PythonConfig
