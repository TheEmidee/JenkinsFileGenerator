"""TemplateValidator class for validating Mako templates in the JenkinsFileGenerator project."""

import re
from pathlib import Path

from mako.exceptions import CompileException, SyntaxException  # type: ignore[import-untyped]
from mako.lookup import TemplateLookup  # type: ignore[import-untyped]
from mako.template import Template  # type: ignore[import-untyped]

from generator import logger
from generator.core import constants
from generator.core.feature_registry import FeatureRegistry
from generator.utils.validation.base_validator import BaseValidator


class TemplateValidator(BaseValidator):
    """Validates Mako template syntax and usage"""

    def __init__(self, config_path: Path) -> None:
        super().__init__()
        self.templates_dir = constants.TEMPLATES_FOLDER
        self.template_lookup = TemplateLookup(directories=[str(self.templates_dir)])
        self.config_path = config_path

    def _get_validation_identifier(self) -> str:
        return "Template"

    def _validate_internal(self) -> None:
        template_files = list(self.templates_dir.glob("*.mako"))

        if not template_files:
            self._add_message(
                "warning",
                "No template files found",
                suggestion="Ensure template files have .mako extension",
            )

        logger.info("Validating %s template files...", len(template_files))

        for template_file in template_files:
            self._validate_template_file(template_file)

        # Validate template relationships
        self._validate_template_relationships()

    def _validate_template_file(self, template_path: Path) -> None:
        """Validate a single template file"""
        logger.debug("Validating template: %s", template_path)

        try:
            # Read template content
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read()

            self._validate_basic_syntax(template_path, content)
            self._validate_mako_compilation(template_path, content)
            self._validate_template_structure(template_path, content)

        except Exception as e:
            self._add_message(
                "error",
                f"Failed to validate template: {e!s}",
                file_path=template_path,
            )

    def _validate_basic_syntax(self, template_path: Path, content: str) -> None:
        """Check for basic syntax issues"""
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            # Check for unmatched brackets/parentheses in Mako expressions
            if "${" in line:
                # Count opening and closing braces in expressions
                expressions = re.findall(r"\$\{[^}]*\}?", line)
                for expr in expressions:
                    if not expr.endswith("}"):
                        self._add_message(
                            "error",
                            "Unclosed Mako expression",
                            file_path=template_path,
                            line_number=i,
                            context=line.strip(),
                            suggestion="Ensure all ${...} expressions are properly closed",
                        )

            # Check for unmatched % blocks
            if line.strip().startswith("%"):
                if line.strip().startswith("% if") and "endif" not in content[content.find(line) :]:
                    # This is a simplified check
                    # more sophisticated logic needed for real validation
                    pass

            # Check for common typos in def blocks
            def_match = re.match(r'<%def\s+name="([^"]+)"', line.strip())
            if def_match:
                def_name = def_match.group(1)
                # Check if def name contains common typos
                if def_name in constants.MAKO_BLOCKS and def_name != def_name.lower():
                    self._add_message(
                        "warning",
                        f"Block name case mismatch: '{def_name}' should be lowercase",
                        file_path=template_path,
                        line_number=i,
                        context=line.strip(),
                        suggestion=f'Use <%def name="{def_name.lower()}"> instead',
                    )

    def _validate_mako_compilation(self, template_path: Path, content: str) -> None:
        """Validate that Mako can compile the template"""
        try:
            Template(content, filename=str(template_path))

            # Also test with template lookup (for includes/inheritance)
            try:
                self.template_lookup.get_template(template_path.name)
            except Exception as e:
                self._add_message(
                    "warning",
                    f"Template lookup failed: {e!s}",
                    file_path=template_path,
                    suggestion="Check for missing template dependencies or includes",
                )

        except (CompileException, SyntaxException) as e:
            # Extract line number if available
            line_number = getattr(e, "lineno", None)

            self._add_message(
                "error",
                f"Mako compilation error: {e!s}",
                file_path=template_path,
                line_number=line_number,
                suggestion="Fix the Mako syntax error",
            )
        except Exception as e:
            self._add_message(
                "error",
                f"Template compilation failed: {e!s}",
                file_path=template_path,
            )

    def _validate_template_structure(self, template_path: Path, content: str) -> None:
        """Validate template structure and def blocks"""
        # Find all def blocks
        def_blocks = re.findall(r'<%def\s+name="([^"]+)"[^>]*>', content)

        # Check for unknown blocks
        # for block_name in def_blocks:
        #     if block_name not in self.STANDARD_BLOCKS:
        #         self._add_message(
        #             'warning',
        #             f"Unknown template block: '{block_name}'",
        #             file_path=template_path,
        #             suggestion=f"Standard blocks are: {', '.join(sorted(self.STANDARD_BLOCKS))}"
        #         )

        # Check for duplicate blocks
        seen_blocks = set()
        for block_name in def_blocks:
            if block_name in seen_blocks:
                self._add_message(
                    "error",
                    f"Duplicate template block: '{block_name}'",
                    file_path=template_path,
                    suggestion="Each block should be defined only once per template",
                )
            seen_blocks.add(block_name)

        # Check for orphaned closing tags
        if content.count("</%def>") != len(def_blocks):
            self._add_message(
                "error",
                "Mismatched <%def> and </%def> tags",
                file_path=template_path,
                suggestion="Ensure every <%def> has a corresponding </%def>",
            )

    def _validate_template_relationships(self) -> None:
        """Validate relationships between templates"""
        # Check base template exists
        base_template = self.templates_dir / "base_jenkinsfile.mako"
        if not base_template.exists():
            self._add_message(
                "error",
                "Base template not found",
                file_path=base_template,
                suggestion="Create base_jenkinsfile.mako as the main template",
            )
            return

        # Check that all features have corresponding templates
        feature_registry = FeatureRegistry()
        available_features = feature_registry.get_all_features()

        for feature_name, _ in available_features.items():
            template_path = self.templates_dir / f"{feature_name}.mako"
            if not template_path.exists():
                self._add_message(
                    "warning",
                    f"No template found for feature '{feature_name}'",
                    file_path=template_path,
                    suggestion=f"Create {template_path} or the feature won't generate any code",
                )
