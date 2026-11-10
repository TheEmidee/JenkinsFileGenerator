import argparse
import logging
import traceback
from pathlib import Path
from typing import List

from generator import logger
from generator.core.batch import GenerationItem, load_batch_config_file
from generator.core.feature_registry import list_all_features
from generator.core.jenkins_file_generator import JenkinsfileGenerator
from generator.core.pipeline_loading import load_pipeline
from generator.features import *  # noqa: F403
from generator.utils import linter
from generator.utils.documentation_generator import generate_documentation
from generator.utils.validation.report import report_messages
from generator.utils.validation.template_validator import validate_templates


def main() -> int:
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

  # Generate a batch of files
  %(prog)s --batch input.yaml --lint
  
  # Generate documentation
  %(prog)s --generate-documentation
        """,
    )

    parser.add_argument("config", nargs="?", type=Path, help="YAML configuration file")
    parser.add_argument("-o", "--output", type=Path, help="Output Jenkinsfile path")
    parser.add_argument("--batch", type=Path, help="Path to the file which describes a batch of configurations to process")

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
        help=(
            "A comma separated list of key=value pairs to be used in the blackboard (Ex: build_type=Development,platform=Windows). "
            "These values can be referenced in the config file using ^BLACKBOARD_DATA.key^ syntax."
        ),
    )
    parser.add_argument("--lint", action="store_true", help="Run npm-groovy-lint on the generated file")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed validation messages including info level",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress non-error output")

    args = parser.parse_args()

    if args.generate_documentation:
        return generate_documentation()

    batch_mode = args.batch is not None
    manual_mode = args.config is not None or args.output is not None

    if batch_mode and manual_mode:
        parser.error("Cannot use --batch with config and -o")
        return 1
    if not batch_mode and not manual_mode and not args.list_features:
        parser.error("Must provide either --batch or both config and -o")
        return 1
    if manual_mode:
        # In manual mode the config is always required; -o only when generating
        if not args.config or (not args.output and not args.validate):
            parser.error("Both config and -o are required when not using --batch")
            return 1

    if args.quiet:
        logger.setLevel(logging.WARNING)
    elif args.verbose:
        logger.setLevel(logging.DEBUG)

    if args.list_features:
        return list_all_features()

    items: List[GenerationItem] = []

    if batch_mode:
        items = load_batch_config_file(args.batch)
    else:
        items.append(GenerationItem(input_config_file=args.config, output_jenkinsfile=args.output or Path(), blackboard_data=args.blackboarddata))

    if args.validate:
        exit_code = 0 if report_messages("Template", validate_templates(), not args.quiet) else 1
        for item in items:
            logger.info("Validating item: input='%s', blackboard_data='%s'", item.input_config_file, item.blackboard_data)
            result = load_pipeline(item.input_config_file, item.blackboard_data)
            if not report_messages("Configuration", result.messages, not args.quiet):
                exit_code = 1
        return exit_code

    try:
        if not report_messages("Template", validate_templates(), not args.quiet):
            return 1
    except KeyboardInterrupt:
        logger.error("❌ Operation cancelled by user")
        return 130

    for item in items:
        logger.info(
            "Processing item: input='%s', output='%s', blackboard_data='%s'", item.input_config_file, item.output_jenkinsfile, item.blackboard_data
        )

        try:
            logger.info("Step 1/3: Loading and validating configuration...")

            result = load_pipeline(item.input_config_file, item.blackboard_data)
            if not report_messages("Configuration", result.messages, not args.quiet) or result.pipeline is None:
                return 1

            logger.info("Step 2/3: Generating Jenkinsfile...")

            generator = JenkinsfileGenerator()
            generator.generate_jenkinsfile(result.pipeline, item.output_jenkinsfile)

            logger.info("✅ Jenkinsfile generated successfully: %s", item.output_jenkinsfile)

            if args.lint:
                logger.info("Step 3/3: Linting generated file...")
                linter.lint_jenkinsfile(item.output_jenkinsfile)
                logger.info("✅ Linting completed successfully!")
            else:
                logger.info("Step 3/3: Skipping lint (use --lint flag to enable)")

            logger.info("🎉 All steps completed successfully!")
        except KeyboardInterrupt:
            logger.error("❌ Operation cancelled by user")
            return 130
        except Exception as e:
            logger.error("❌ Generation failed: %s", e)
            if args.verbose:
                logger.error("Stack trace:\n%s", traceback.format_exc())
            return 1

    return 0
