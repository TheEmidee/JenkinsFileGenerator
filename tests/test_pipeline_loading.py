"""Tests for Pipeline loading, through its public interface only."""

from pathlib import Path
from typing import List

from conftest import WriteConfig

from generator.core.pipeline_loading import PipelineLoadResult, load_pipeline
from generator.core.validation_message import ValidationMessage

VALID_CONFIG = """\
pipeline_name: "Test pipeline"
project:
  name: "MyGame"
jenkins:
  default_node_names: "windows"
features:
  git:
    retry_count: 2
  utils: {}
"""


def errors(result: PipelineLoadResult) -> List[ValidationMessage]:
    return [message for message in result.messages if message.level == "error"]


def warnings(result: PipelineLoadResult) -> List[ValidationMessage]:
    return [message for message in result.messages if message.level == "warning"]


def test_valid_config_returns_a_loaded_pipeline_without_messages(write_config: WriteConfig) -> None:
    path = write_config(VALID_CONFIG)

    result = load_pipeline(path)

    assert result.messages == []
    assert result.pipeline is not None
    assert result.pipeline.config.project.name == "MyGame"
    assert set(result.pipeline.feature_configs) == {"git", "utils"}
    assert result.pipeline.feature_configs["git"].retry_count == 2  # type: ignore[attr-defined]
    assert result.pipeline.source_path == path


def test_blackboard_data_is_substituted_and_unresolved_tokens_are_located_errors(write_config: WriteConfig) -> None:
    path = write_config(
        VALID_CONFIG.replace('name: "MyGame"', 'name: "^BLACKBOARD_DATA.project^"').replace(
            'default_node_names: "windows"', 'default_node_names: "^BLACKBOARD_DATA.platform^"'
        )
    )

    resolved = load_pipeline(path, "project=Resolved,platform=Win64")
    assert resolved.pipeline is not None
    assert resolved.pipeline.config.project.name == "Resolved"
    assert resolved.pipeline.config.jenkins.default_node_names == "Win64"
    assert resolved.pipeline.blackboard_data == "project=Resolved,platform=Win64"

    unresolved = load_pipeline(path, "project=Resolved")
    assert unresolved.pipeline is None
    [error] = errors(unresolved)
    assert "^BLACKBOARD_DATA.platform^" in error.message
    assert error.line_number == 5


def test_top_level_schema_error_reports_its_line(write_config: WriteConfig) -> None:
    path = write_config(VALID_CONFIG.replace('pipeline_name: "Test pipeline"', "pipeline_name: [1, 2]"))

    result = load_pipeline(path)

    assert result.pipeline is None
    [error] = errors(result)
    assert error.context == "pipeline_name"
    assert error.line_number == 1


def test_feature_config_error_reports_its_line(write_config: WriteConfig) -> None:
    path = write_config(VALID_CONFIG.replace("retry_count: 2", "retry_count: lots"))

    result = load_pipeline(path)

    assert result.pipeline is None
    [error] = errors(result)
    assert error.context == "features.git.retry_count"
    assert error.line_number == 8
    assert "git" in error.message


def test_missing_field_falls_back_to_nearest_ancestor_line(write_config: WriteConfig) -> None:
    path = write_config(VALID_CONFIG + '  github:\n    owner: "me"\n    credentials_id: "token"\n')

    result = load_pipeline(path)

    assert result.pipeline is None
    [error] = errors(result)
    assert error.context == "features.github.repository"
    assert error.message.endswith("Required field is missing")
    assert error.line_number == 10  # the `github:` key


def test_unknown_feature_is_an_error_with_a_suggestion(write_config: WriteConfig) -> None:
    path = write_config(VALID_CONFIG + "  githb: {}\n")

    result = load_pipeline(path)

    assert result.pipeline is None
    [error] = errors(result)
    assert error.message == "Unknown feature: 'githb'"
    assert error.line_number == 10
    assert error.suggestion is not None
    assert error.suggestion.startswith("Did you mean:")
    assert "github" in error.suggestion.split("?")[0]


def test_style_issues_are_warnings_and_do_not_block_loading(write_config: WriteConfig) -> None:
    path = write_config(VALID_CONFIG.replace('pipeline_name: "Test pipeline"', 'pipeline_name: "Test pipeline"   ') + "# note:\tsee docs\n")

    result = load_pipeline(path)

    assert result.pipeline is not None
    assert errors(result) == []
    assert sorted((w.line_number, w.message.split(".")[0]) for w in warnings(result)) == [
        (1, "Found trailing whitespace"),
        (10, "Found tab character"),
    ]


def test_customization_folder_is_resolved_relative_to_the_config_file(write_config: WriteConfig, tmp_path: Path) -> None:
    (tmp_path / "Customization").mkdir()
    path = write_config('customization_folder: "Customization"\n' + VALID_CONFIG)

    result = load_pipeline(path)

    assert result.pipeline is not None
    assert result.pipeline.config.customization_folder == (tmp_path / "Customization").resolve()
