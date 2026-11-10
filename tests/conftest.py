"""Shared fixtures. Importing the Feature modules registers them with the FeatureRegistry."""

import importlib
from pathlib import Path
from typing import Callable

import pytest

import generator.features

for _feature_module in generator.features.__all__:
    importlib.import_module(f"generator.features.{_feature_module}")

WriteConfig = Callable[[str], Path]


@pytest.fixture
def write_config(tmp_path: Path) -> WriteConfig:
    """Write YAML text to a Pipeline config file in a temporary folder and return its path."""

    def _write(text: str) -> Path:
        path = tmp_path / "pipeline.yaml"
        path.write_text(text, encoding="utf-8")
        return path

    return _write
