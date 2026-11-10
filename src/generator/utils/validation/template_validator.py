"""Validation of the built-in Mako templates."""

import re
from pathlib import Path
from typing import List

from mako.exceptions import CompileException, SyntaxException  # type: ignore[import-untyped]
from mako.lookup import TemplateLookup  # type: ignore[import-untyped]
from mako.template import Template  # type: ignore[import-untyped]

from generator import logger
from generator.core import constants
from generator.core.feature_registry import FeatureRegistry
from generator.core.validation_message import ValidationMessage


def validate_templates(templates_dir: Path = constants.TEMPLATES_FOLDER) -> List[ValidationMessage]:
    """Validate Mako syntax and structure of every template in `templates_dir`, and that each Feature has a template."""
    messages: List[ValidationMessage] = []
    template_lookup = TemplateLookup(directories=[str(templates_dir)])
    template_files = list(templates_dir.glob("*.mako"))

    if not template_files:
        messages.append(ValidationMessage("warning", "No template files found", suggestion="Ensure template files have .mako extension"))

    logger.info("Validating %s template files...", len(template_files))

    for template_file in template_files:
        logger.debug("Validating template: %s", template_file)
        try:
            content = template_file.read_text(encoding="utf-8")
            messages += _validate_basic_syntax(template_file, content)
            messages += _validate_mako_compilation(template_file, content, template_lookup)
            messages += _validate_template_structure(template_file, content)
        except Exception as e:
            messages.append(ValidationMessage("error", f"Failed to validate template: {e!s}", file_path=template_file))

    messages += _validate_template_relationships(templates_dir)
    return messages


def _validate_basic_syntax(template_path: Path, content: str) -> List[ValidationMessage]:
    messages: List[ValidationMessage] = []

    for i, line in enumerate(content.split("\n"), 1):
        if "${" in line:
            for expr in re.findall(r"\$\{[^}]*\}?", line):
                if not expr.endswith("}"):
                    messages.append(
                        ValidationMessage(
                            "error",
                            "Unclosed Mako expression",
                            file_path=template_path,
                            line_number=i,
                            context=line.strip(),
                            suggestion="Ensure all ${...} expressions are properly closed",
                        )
                    )

        def_match = re.match(r'<%def\s+name="([^"]+)"', line.strip())
        if def_match:
            def_name = def_match.group(1)
            if def_name in constants.MAKO_BLOCKS and def_name != def_name.lower():
                messages.append(
                    ValidationMessage(
                        "warning",
                        f"Block name case mismatch: '{def_name}' should be lowercase",
                        file_path=template_path,
                        line_number=i,
                        context=line.strip(),
                        suggestion=f'Use <%def name="{def_name.lower()}"> instead',
                    )
                )

    return messages


def _validate_mako_compilation(template_path: Path, content: str, template_lookup: TemplateLookup) -> List[ValidationMessage]:
    try:
        Template(content, filename=str(template_path))
    except (CompileException, SyntaxException) as e:
        return [
            ValidationMessage(
                "error",
                f"Mako compilation error: {e!s}",
                file_path=template_path,
                line_number=getattr(e, "lineno", None),
                suggestion="Fix the Mako syntax error",
            )
        ]
    except Exception as e:
        return [ValidationMessage("error", f"Template compilation failed: {e!s}", file_path=template_path)]

    try:
        template_lookup.get_template(template_path.name)
    except Exception as e:
        return [
            ValidationMessage(
                "warning",
                f"Template lookup failed: {e!s}",
                file_path=template_path,
                suggestion="Check for missing template dependencies or includes",
            )
        ]

    return []


def _validate_template_structure(template_path: Path, content: str) -> List[ValidationMessage]:
    messages: List[ValidationMessage] = []
    def_blocks = re.findall(r'<%def\s+name="([^"]+)"[^>]*>', content)

    seen_blocks = set()
    for block_name in def_blocks:
        if block_name in seen_blocks:
            messages.append(
                ValidationMessage(
                    "error",
                    f"Duplicate template block: '{block_name}'",
                    file_path=template_path,
                    suggestion="Each block should be defined only once per template",
                )
            )
        seen_blocks.add(block_name)

    if content.count("</%def>") != len(def_blocks):
        messages.append(
            ValidationMessage(
                "error",
                "Mismatched <%def> and </%def> tags",
                file_path=template_path,
                suggestion="Ensure every <%def> has a corresponding </%def>",
            )
        )

    return messages


def _validate_template_relationships(templates_dir: Path) -> List[ValidationMessage]:
    base_template = templates_dir / "base_jenkinsfile.mako"
    if not base_template.exists():
        return [
            ValidationMessage(
                "error",
                "Base template not found",
                file_path=base_template,
                suggestion="Create base_jenkinsfile.mako as the main template",
            )
        ]

    messages: List[ValidationMessage] = []
    for feature_name in FeatureRegistry().get_all_features():
        template_path = templates_dir / f"{feature_name}.mako"
        if not template_path.exists():
            messages.append(
                ValidationMessage(
                    "warning",
                    f"No template found for feature '{feature_name}'",
                    file_path=template_path,
                    suggestion=f"Create {template_path} or the feature won't generate any code",
                )
            )
    return messages
