"""DocumentationGenerator class for generating markdown documentation from Pydantic models.
This class is designed to create documentation for the Jenkins pipeline configuration"""

import importlib
import inspect
import os
import sys
from pathlib import Path
import pkgutil
from typing import List, Union, get_args, get_origin

from pydantic import BaseModel

from generator import logger
from generator.core.pipeline_config import PipelineConfig


class DocumentationGenerator:
    """Generates markdown documentation for the Jenkins pipeline configuration."""

    def __init__(self):
        package_path = Path(os.path.abspath("documentation"))

        if not package_path.exists():
            raise FileNotFoundError(f"Output path {package_path} does not exist.")

        self.output_path = package_path
        self.feature_configs = self._discover_feature_configs()

    def generate_documentation(self):
        """Generates documentation for the Jenkins pipeline configuration."""

        try:
            self._generate_main_docs_page()
            self._generate_features_docs_pages()
            # markdown_docs += self._generate_features_config_docs()
        except Exception as e:
            logger.error("Failed to generate documentation: %s", e)
            raise e

    def _generate_main_docs_page(self):
        markdown_docs = self._generate_markdown_docs(PipelineConfig)

        features = ["# Features"]
        for cls in self.feature_configs:
            class_anchor = cls.__name__.lower().replace(" ", "-")
            features.append(f"- [{cls.__name__}]({class_anchor}.md)")
        features.append("")

        markdown_docs += "\n".join(features)

        main_page = self.output_path / "index.md"
        main_page.write_text(markdown_docs)

    def _get_field_type_description(
        self, model_class: BaseModel, field_name: str, field_info: dict
    ) -> str:
        """Get a human-readable type description for a field."""
        try:
            # First try to get the type from the model field annotation
            field = model_class.model_fields[field_name]
            field_type = field.annotation

            # Handle the type annotation
            return self._format_type_annotation(field_type)

        except Exception:
            # Fallback to JSON schema analysis
            return self._get_type_from_schema(field_info)

    def _format_type_annotation(self, type_annotation) -> str:
        """Format a type annotation into a readable string."""
        # Handle None type
        if type_annotation is type(None):
            return "None"

        # Handle basic types
        if hasattr(type_annotation, "__name__"):
            if type_annotation.__name__ in [
                "str",
                "int",
                "float",
                "bool",
                "dict",
                "list",
            ]:
                return type_annotation.__name__

        # Handle typing generics (Optional, List, Union, etc.)
        origin = get_origin(type_annotation)
        args = get_args(type_annotation)

        if origin is not None:
            if origin is list:
                if args:
                    return f"List[{self._format_type_annotation(args[0])}]"
                return "List"
            if origin is dict:
                if len(args) >= 2:
                    return f"Dict[{self._format_type_annotation(args[0])}, {self._format_type_annotation(args[1])}]"
                return "Dict"
            if origin is tuple:
                if args:
                    arg_strs = [self._format_type_annotation(arg) for arg in args]
                    return f"Tuple[{', '.join(arg_strs)}]"
                return "Tuple"
            if origin is type(Union[str, int]):  # Union type
                if len(args) == 2 and type(None) in args:
                    # This is Optional[T]
                    non_none_type = args[0] if args[1] is type(None) else args[1]
                    return f"Optional[{self._format_type_annotation(non_none_type)}]"
                else:
                    # Regular Union
                    arg_strs = [self._format_type_annotation(arg) for arg in args]
                    return f"Union[{', '.join(arg_strs)}]"

        # Handle Pydantic models
        if inspect.isclass(type_annotation) and issubclass(type_annotation, BaseModel):
            return type_annotation.__name__

        # Handle enums
        try:
            if hasattr(type_annotation, "__bases__") and any(
                "Enum" in base.__name__ for base in type_annotation.__bases__
            ):
                return f"Enum ({type_annotation.__name__})"
        except (AttributeError, TypeError):
            pass

        # Fallback to string representation
        type_str = str(type_annotation)
        # Clean up common typing module prefixes
        type_str = type_str.replace("typing.", "")
        return type_str

    def _get_type_from_schema(self, field_info: dict) -> str:
        """Extract type information from JSON schema field info."""
        if "enum" in field_info:
            return f"enum: {', '.join(map(str, field_info['enum']))}"
        elif "$ref" in field_info:
            return field_info["$ref"].split("/")[-1]
        elif "type" in field_info:
            schema_type = field_info["type"]
            if schema_type == "array" and "items" in field_info:
                items_type = self._get_type_from_schema(field_info["items"])
                return f"List[{items_type}]"
            elif schema_type == "object":
                return "Dict"
            return schema_type
        elif "anyOf" in field_info:
            # Handle Optional types and unions
            types = []
            has_null = False
            for option in field_info["anyOf"]:
                if option.get("type") == "null":
                    has_null = True
                else:
                    types.append(self._get_type_from_schema(option))

            if has_null and len(types) == 1:
                return f"Optional[{types[0]}]"
            elif has_null:
                return f"Union[{', '.join(types + ['None'])}]"
            else:
                return f"Union[{', '.join(types)}]"

        return "unknown"

    def _generate_markdown_docs(
        self,
        model_class: BaseModel,
        title: str = None,
        level: int = 0,
        output_description=True,
    ) -> str:
        """Generate markdown documentation from a Pydantic model."""
        schema = model_class.model_json_schema()

        if title is None:
            title = model_class.__name__

        docs = []
        if output_description:
            prefix = "* " if level > 0 else "# "
            docs.append(f"{'  ' * level}{prefix}{title}\n")

            if "description" in schema:
                prefix = "\t" if level > 0 else ""
                description = schema["description"]

                if level == 0:
                    docs.append("```")

                processed_lines = [
                    f"{'  ' * level}{prefix}{line}" for line in description.split("\n")
                ]
                docs.append("\n".join(processed_lines))

                if level == 0:
                    docs.append("```")

        properties = schema.get("properties", {})
        required_fields = set(schema.get("required", []))

        for field_name, field_info in properties.items():
            text = f"{'  ' * (level+1)}* **{field_name}**"

            if "description" in field_info:
                text += f": {field_info['description']}"

            text += " ( "

            if field_name in required_fields:
                text += " (Required)"

            # Get improved type information
            field_type = self._get_field_type_description(
                model_class, field_name, field_info
            )
            text += f" Type: `{field_type}`"

            # Default value
            if "default" in field_info:
                text += f" Default: `{field_info['default']}`"

            # Validation constraints
            constraints = []
            for key in ["minimum", "maximum", "minLength", "maxLength", "pattern"]:
                if key in field_info:
                    constraints.append(f"{key}: {field_info[key]}")

            if constraints:
                text += f" Constraints: {', '.join(constraints)}"

            text += " )"

            docs.append(text)

            # Recursively document nested BaseModel fields
            # Try to get the actual type from the model_class
            try:
                field = model_class.model_fields[field_name]
                field_type_obj = field.annotation

                # Handle typing.Optional and typing.List using get_origin and get_args
                origin = get_origin(field_type_obj)
                if origin is not None:
                    args = get_args(field_type_obj)
                    for arg in args:
                        if inspect.isclass(arg) and issubclass(arg, BaseModel):
                            docs.append(
                                self._generate_markdown_docs(
                                    arg,
                                    title=f"{field_name} ({arg.__name__})",
                                    level=level + 1,
                                    output_description=False,
                                )
                            )
                elif inspect.isclass(field_type_obj) and issubclass(
                    field_type_obj, BaseModel
                ):
                    docs.append(
                        self._generate_markdown_docs(
                            field_type_obj,
                            title=f"{field_name} ({field_type_obj.__name__})",
                            level=level + 1,
                            output_description=False,
                        )
                    )
            except (AttributeError, TypeError):
                pass

            docs.append("")

        return "\n".join(docs)

    def _generate_features_docs_pages(self):
        """Generate markdown documentation for all feature configurations."""
        if not self.feature_configs:
            return

        for cls in self.feature_configs:
            path = self.output_path / f"{cls.__name__.lower()}.md"
            text = self._generate_markdown_docs(cls, title=cls.__name__)
            text += "\n[Back to main page](index.md)"
            path.write_text(text)

    def _discover_feature_configs(self) -> List[BaseModel]:
        """
        Discover all classes that inherit from a base class (e.g., FeatureConfig) in a package.

        Args:
            package_path: Path to the package/folder containing the Python files
            base_class_name: Name of the base class to look for (default: "FeatureConfig")

        Returns:
            List of discovered classes that inherit from the base class
        """

        discovered_classes = []
        package_path = os.path.abspath("generator/features")

        # Temporarily add the parent directory to sys.path
        parent_dir = os.path.dirname(package_path)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
            path_added = True
        else:
            path_added = False

        try:
            # Method 1: Try to import as a package if __init__.py exists
            init_file = os.path.join(package_path, "__init__.py")
            if os.path.exists(init_file):
                package_name = os.path.basename(package_path)
                try:
                    package = importlib.import_module(package_name)

                    # Walk through all modules in the package
                    for importer, modname, ispkg in pkgutil.iter_modules(
                        package.__path__
                    ):
                        try:
                            full_modname = f"{package_name}.{modname}"
                            module = importlib.import_module(full_modname)

                            # Inspect all classes in the module
                            for _, obj in inspect.getmembers(
                                module, inspect.isclass
                            ):
                                if self._is_subclass_of_base(obj, "FeatureConfig"):
                                    discovered_classes.append(obj)

                        except ImportError as e:
                            print(
                                f"Warning: Could not import module {full_modname}: {e}"
                            )
                            continue

                except ImportError as e:
                    print(
                        f"Package import failed: {e}, trying individual file imports..."
                    )
        finally:
            # Clean up sys.path
            if path_added and parent_dir in sys.path:
                sys.path.remove(parent_dir)

        return discovered_classes

    def _is_subclass_of_base(self, obj, base_class_name: str) -> bool:
        """
        Helper function to check if a class inherits from a base class by name.
        """
        if not inspect.isclass(obj):
            return False

        # Skip the base class itself
        if obj.__name__ == base_class_name:
            return False

        # Check if any class in the MRO has the target base class name
        try:
            for base in inspect.getmro(obj):
                if base.__name__ == base_class_name:
                    return True
        except (TypeError, AttributeError):
            # Handle any issues with MRO inspection
            pass

        return False


def generate_documentation() -> int:
    """Entry point for generating documentation."""
    try:
        logger.info("Generating documentation...")
        documentation_generator = DocumentationGenerator()
        documentation_generator.generate_documentation()
        logger.info("✅ Documentation generated successfully!")
        return 0
    except (OSError, RuntimeError) as e:
        logger.error("Documentation generation failed: %s", e)
        return 1
