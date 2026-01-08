#!/usr/bin/env python
"""This script is the entry point for the jenkinsfile generator module"""

import argparse
import logging
import argparse
import traceback

from pathlib import Path

from generator import logger
from generator.core.feature_registry import list_all_features
from generator.core.jenkins_file_generator import JenkinsfileGenerator
from generator.utils import linter
from generator.utils.documentation_generator import generate_documentation
from generator.features import *
from generator.utils.validation.config_validator import ConfigValidator
from generator.utils.validation.template_validator import TemplateValidator


def main():
    """Main CLI entry point"""

    parser = argparse.ArgumentParser(
        description="Generate Jenkins pipeline from YAML config",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate Jenkinsfile
  %(prog)s config.yaml -o Jenkinsfile
  
  # Validate configuration only
  %(prog)s --validate config.yaml
  
  # Generate with linting
  %(prog)s config.yaml -o Jenkinsfile --lint
  
  # Generate documentation
  %(prog)s --generate-documentation
        """,
    )

    parser.add_argument("config", type=Path, help="YAML configuration file")
    parser.add_argument("-o", "--output", type=Path, help="Output Jenkinsfile path")

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--validate",
        action="store_true",
        help="Validate configuration only (no generation)",
    )
    mode_group.add_argument(
        "--generate-documentation",
        action="store_true",
        help="Generate configuration documentation",
    )
    mode_group.add_argument(
        "--list_features",
        action="store_true",
        help="Output all the registered features",
    )

    parser.add_argument(
        "-bbd",
        "--blackboarddata",
        default="",
        help="A comma separated list of key=value pairs to be used in the blackboard (Ex: build_type=Development,platform=Windows). These values can be referenced in the config file using ^BLACKBOARD_DATA.key^ syntax.",
    )
    parser.add_argument(
        "--lint", action="store_true", help="Run npm-groovy-lint on the generated file"
    )
    parser.add_argument(
        "--no-validation",
        action="store_true",
        help="Skip configuration validation (not recommended)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed validation messages including info level",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress non-error output"
    )

    args = parser.parse_args()

    if args.quiet:
        logger.setLevel(logging.WARNING)
    elif args.verbose:
        logger.setLevel(logging.DEBUG)

    if args.generate_documentation:
        return generate_documentation()

    if args.list_features:
        return list_all_features()

    if not args.config:
        parser.error(
            "Configuration file is required (except for --generate-documentation)"
        )

    def validate_config() -> int:
        config_validator = ConfigValidator(args.config)
        if not config_validator.validate(not args.quiet):
            return 1

        return 0

    if args.validate:
        return validate_config()

    try:
        if not args.no_validation:
            logger.info("Step 1/3: Validating configuration...")

            config_validation_result = validate_config()
            if config_validation_result != 0:
                return config_validation_result

            templates_validator = TemplateValidator(args.config)
            if not templates_validator.validate(not args.quiet):
                return 1
        else:
            logger.warning(
                "⚠️  Skipping configuration validation (--no-validation flag used)"
            )

        logger.info("Step 2/3: Generating Jenkinsfile...")

        generator = JenkinsfileGenerator()
        generator.generate_jenkinsfile(args.config, args.output, args.blackboarddata)

        logger.info("✅ Jenkinsfile generated successfully: %s", args.output)

        if args.lint:
            logger.info("Step 3/3: Linting generated file...")
            linter.lint_jenkinsfile(args.output)
            logger.info("✅ Linting completed successfully!")
        else:
            logger.info("Step 3/3: Skipping lint (use --lint flag to enable)")

        logger.info("🎉 All steps completed successfully!")
        return 0

    except KeyboardInterrupt:
        logger.error("❌ Operation cancelled by user")
        return 130
    except Exception as e:
        logger.error("❌ Generation failed: %s", e)
        if args.verbose:
            logger.error("Stack trace:\n%s", traceback.format_exc())
        return 1


if __name__ == "__main__":
    main()
