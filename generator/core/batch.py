from pathlib import Path
from typing import Any, List

import yaml
from pydantic import BaseModel, Field, field_validator


class GenerationItem(BaseModel):
    """Class for keeping track of the information required to generate a jenkinsfile."""

    input_config_file: Path
    output_jenkinsfile: Path
    blackboard_data: str = Field(
        default="",
        description="The blackboard data to use for this item",
    )

    @field_validator("input_config_file", "output_jenkinsfile", mode="before")
    @classmethod
    def convert_to_path(cls, v: Any) -> Path:  # noqa: ANN401
        """Convert string paths to Path objects."""
        return Path(v) if isinstance(v, str) else v

    @field_validator("blackboard_data")
    @classmethod
    def validate_blackboard_format(cls, v: str) -> str:
        """Validate that blackboard_data follows key=value,key=value format."""
        if not v:
            return v

        pairs = v.split(",")
        for pair in pairs:
            if "=" not in pair:
                raise ValueError(f"Invalid blackboard_data format: '{pair}' must contain '='")
        return v


class GenerationConfig(BaseModel):
    """Container for multiple generation items."""

    items: List[GenerationItem]


def load_batch_config_file(yaml_path: Path) -> List[GenerationItem]:
    """
    Load and validate generation items from a YAML file.

    Args:
        yaml_path: Path to the YAML configuration file

    Returns:
        List of validated GenerationItem objects

    Raises:
        pydantic.ValidationError: If the YAML doesn't match the expected schema
        FileNotFoundError: If the YAML file doesn't exist
    """
    yaml_file = Path(yaml_path)
    yaml_dir = yaml_file.parent.resolve()

    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Pydantic will validate the structure and types
    config = GenerationConfig(**data)

    for item in config.items:
        item.input_config_file = yaml_dir / item.input_config_file
        item.output_jenkinsfile = yaml_dir / item.output_jenkinsfile

    return config.items
