"""Pipeline loading: the only place a Pipeline config is read and parsed (see docs/adr/0001).

Turns a Pipeline config file plus Blackboard data into either a Loaded pipeline or a list of
located Validation messages. User mistakes are reported as messages; exceptions are reserved
for programming errors and unexpected I/O failures.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml
from pydantic import ValidationError
from pydantic_core import ErrorDetails

from generator.core.base_feature import FeatureConfig
from generator.core.feature_registry import FeatureRegistry
from generator.core.pipeline_config import PipelineConfig
from generator.core.validation_context import ConfigValidationContext
from generator.core.validation_message import ValidationLevel, ValidationMessage

BLACKBOARD_TOKEN_PATTERN = re.compile(r"\^BLACKBOARD_DATA\.([^\^]+)\^")

KeyPath = Tuple[str, ...]


@dataclass(frozen=True)
class LoadedPipeline:
    """A Pipeline config that passed validation, with the Feature config of every declared Feature."""

    config: PipelineConfig
    feature_configs: Dict[str, FeatureConfig]
    source_path: Path
    blackboard_data: str = ""


@dataclass
class PipelineLoadResult:
    """Outcome of Pipeline loading: a Loaded pipeline when there are no errors, and every Validation message found."""

    pipeline: Optional[LoadedPipeline]
    messages: List[ValidationMessage] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        """True if any message is an error. When True, `pipeline` is None."""
        return any(message.level == "error" for message in self.messages)


def load_pipeline(config_path: Path, blackboard_data: str = "") -> PipelineLoadResult:
    """Load and validate a Pipeline config.

    Args:
        config_path: Path to the Pipeline config YAML file. Relative paths inside the file are resolved against its folder.
        blackboard_data: Comma separated `key=value` pairs substituted for `^BLACKBOARD_DATA.key^` tokens before parsing.

    Returns:
        A PipelineLoadResult. `pipeline` is set only when no error-level message was produced.
    """
    return _PipelineLoader(Path(config_path), blackboard_data).load()


class _PipelineLoader:
    def __init__(self, config_path: Path, blackboard_data: str) -> None:
        self._path = config_path
        self._blackboard_data = blackboard_data
        self._messages: List[ValidationMessage] = []
        self._line_map: Dict[KeyPath, int] = {}

    def load(self) -> PipelineLoadResult:
        text = self._read()
        if text is None:
            return self._result(None)

        self._check_style(text)

        text = self._substitute_blackboard_data(text)
        if text is None:
            return self._result(None)

        data = self._parse_yaml(text)
        if data is None:
            return self._result(None)

        validation_context = ConfigValidationContext(self._path)
        config = self._validate_pipeline_config(data, validation_context)
        if config is None:
            return self._result(None)

        feature_configs = self._validate_feature_configs(config, validation_context)

        if any(message.level == "error" for message in self._messages):
            return self._result(None)

        return self._result(
            LoadedPipeline(
                config=config,
                feature_configs=feature_configs,
                source_path=self._path,
                blackboard_data=self._blackboard_data,
            )
        )

    def _result(self, pipeline: Optional[LoadedPipeline]) -> PipelineLoadResult:
        return PipelineLoadResult(pipeline=pipeline, messages=list(self._messages))

    def _add(
        self,
        level: ValidationLevel,
        message: str,
        line_number: Optional[int] = None,
        column: Optional[int] = None,
        context: Optional[str] = None,
        suggestion: Optional[str] = None,
    ) -> None:
        self._messages.append(
            ValidationMessage(
                level=level,
                message=message,
                file_path=self._path,
                line_number=line_number,
                column=column,
                context=context,
                suggestion=suggestion,
            )
        )

    # --- Reading -------------------------------------------------------------------------------

    def _read(self) -> Optional[str]:
        if not self._path.exists():
            self._add("error", f"Configuration file not found: {self._path}")
            return None
        if not self._path.is_file():
            self._add("error", f"Path is not a file: {self._path}")
            return None

        with open(self._path, "r", encoding="utf-8") as f:
            return f.read()

    def _check_style(self, text: str) -> None:
        for line_number, line in enumerate(text.split("\n"), 1):
            if "\t" in line:
                self._add(
                    "warning",
                    "Found tab character. YAML should use spaces for indentation",
                    line_number=line_number,
                    suggestion="Replace tabs with spaces (typically 2 or 4 spaces per indent level)",
                )
            if line.strip() and line.rstrip() != line:
                self._add(
                    "warning",
                    "Found trailing whitespace",
                    line_number=line_number,
                    suggestion="Remove trailing spaces from the end of the line",
                )

    # --- Blackboard data -----------------------------------------------------------------------

    def _substitute_blackboard_data(self, text: str) -> Optional[str]:
        values: Dict[str, str] = {}
        if self._blackboard_data:
            for pair in self._blackboard_data.split(","):
                if "=" not in pair:
                    self._add(
                        "error",
                        f"Invalid Blackboard data entry '{pair}': expected key=value",
                        suggestion="Use a comma separated list of key=value pairs, e.g. build_type=Development,platform=Win64",
                    )
                    continue
                key, value = pair.split("=", 1)
                values[key.strip()] = value

        if any(message.level == "error" for message in self._messages):
            return None

        for key, value in values.items():
            text = text.replace(f"^BLACKBOARD_DATA.{key}^", value)

        unresolved = list(BLACKBOARD_TOKEN_PATTERN.finditer(text))
        for match in unresolved:
            line_number = text.count("\n", 0, match.start()) + 1
            self._add(
                "error",
                f"Unresolved Blackboard data token: {match.group(0)}",
                line_number=line_number,
                suggestion=f"Pass a value for it, e.g. --blackboarddata {match.group(1)}=<value>",
            )

        return None if unresolved else text

    # --- YAML ----------------------------------------------------------------------------------

    def _parse_yaml(self, text: str) -> Optional[Dict[str, Any]]:
        loader = yaml.SafeLoader(text)
        try:
            node = loader.get_single_node()
            data = loader.construct_document(node) if node is not None else None
        except yaml.YAMLError as e:
            mark = getattr(e, "problem_mark", None)
            self._add(
                "error",
                f"YAML syntax error: {e}",
                line_number=mark.line + 1 if mark else None,
                column=mark.column + 1 if mark else None,
            )
            return None
        finally:
            loader.dispose()

        if node is None or data is None:
            self._add("error", "Configuration file is empty")
            return None
        if not isinstance(data, dict):
            self._add("error", "Configuration file must contain a mapping at its top level", line_number=1)
            return None

        self._record_lines(node, ())
        return data

    def _record_lines(self, node: yaml.Node, path: KeyPath) -> None:
        if isinstance(node, yaml.MappingNode):
            for key_node, value_node in node.value:
                child = (*path, str(key_node.value))
                self._line_map[child] = key_node.start_mark.line + 1
                self._record_lines(value_node, child)
        elif isinstance(node, yaml.SequenceNode):
            for index, item_node in enumerate(node.value):
                child = (*path, str(index))
                self._line_map[child] = item_node.start_mark.line + 1
                self._record_lines(item_node, child)

    def _line_for(self, path: KeyPath) -> Optional[int]:
        """Line of the key at `path`, or of its nearest ancestor that has one."""
        for length in range(len(path), 0, -1):
            line = self._line_map.get(path[:length])
            if line is not None:
                return line
        return None

    # --- Validation ----------------------------------------------------------------------------

    def _validate_pipeline_config(self, data: Dict[str, Any], validation_context: ConfigValidationContext) -> Optional[PipelineConfig]:
        try:
            return PipelineConfig.model_validate(data, context=validation_context)
        except ValidationError as e:
            self._add_pydantic_errors(e, prefix=(), label=None)
            return None

    def _validate_feature_configs(self, config: PipelineConfig, validation_context: ConfigValidationContext) -> Dict[str, FeatureConfig]:
        available = FeatureRegistry().get_all_features()
        feature_configs: Dict[str, FeatureConfig] = {}

        for feature_name, raw_feature_config in config.features.items():
            prefix: KeyPath = ("features", feature_name)

            feature_class = available.get(feature_name)
            if feature_class is None:
                suggestion = f"Available features: {', '.join(available.keys())}"
                similar = _find_similar_names(feature_name, available.keys())
                if similar:
                    suggestion = f"Did you mean: {', '.join(similar)}? " + suggestion
                self._add(
                    "error",
                    f"Unknown feature: '{feature_name}'",
                    line_number=self._line_for(prefix),
                    context=".".join(prefix),
                    suggestion=suggestion,
                )
                continue

            config_model = feature_class().get_config_model()
            try:
                feature_configs[feature_name] = config_model.model_validate(raw_feature_config or {}, context=validation_context)
            except ValidationError as e:
                self._add_pydantic_errors(e, prefix=prefix, label=feature_name)

        return feature_configs

    def _add_pydantic_errors(self, error: ValidationError, prefix: KeyPath, label: Optional[str]) -> None:
        for details in error.errors():
            path = (*prefix, *(str(loc) for loc in details["loc"]))
            field_path = ".".join(path)
            message = _format_pydantic_error(details)
            if label:
                message = f"Feature '{label}': {message}"
            self._add(
                "error",
                message,
                line_number=self._line_for(path),
                context=field_path or None,
                suggestion=_get_error_suggestion(details, field_path),
            )


def _format_pydantic_error(error: ErrorDetails) -> str:
    """Format a Pydantic validation error into a readable message."""
    error_type = error.get("type", "unknown")
    input_value = error.get("input")

    if error_type == "missing":
        return "Required field is missing"
    if error_type == "string_type":
        return f"Expected string, got {type(input_value).__name__}: {input_value}"
    if error_type == "bool_parsing":
        return f"Expected boolean (true/false), got: {input_value}"
    if error_type == "int_parsing":
        return f"Expected integer, got: {input_value}"
    if error_type == "value_error":
        return f"Invalid value: {error.get('msg', str(input_value))}"

    return error.get("msg", f"Validation error: {error_type}")


def _get_error_suggestion(error: ErrorDetails, field_path: str) -> Optional[str]:
    """Get helpful suggestions for common validation errors."""
    error_type = error.get("type", "unknown")

    if error_type == "missing":
        if "channel" in field_path:
            return 'Add a channel field like: channel: "#ci-builds"'
        if "name" in field_path:
            return "Add a name field with your project name"

    if error_type == "bool_parsing":
        return "Use true or false (lowercase, no quotes)"

    if error_type == "string_type":
        return "Wrap the value in quotes if it contains special characters"

    if "url" in field_path.lower():
        return "Ensure the URL starts with http:// or https://"

    return None


def _find_similar_names(target: str, available: Iterable[str]) -> List[str]:
    """Find names similar to the target (substring or shared 3-letter prefix)."""
    similar = []
    target_lower = target.lower()

    for name in available:
        name_lower = name.lower()
        if target_lower in name_lower or name_lower in target_lower:
            similar.append(name)
        elif (target_lower.startswith(name_lower[:3]) or name_lower.startswith(target_lower[:3])) and len(target) > 3:
            similar.append(name)

    return similar[:3]
