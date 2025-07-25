import logging
import os
from pathlib import Path
import subprocess
import sys

from generator import logger
from generator.core.config_validator import ConfigValidator
from generator.core.jenkins_file_generator import JenkinsfileGenerator
from generator.core.template_validator import TemplateValidator
from generator.documentation.documentation_generator import DocumentationGenerator
from generator.features import *

def lint_output(output_file:Path):
    try:
        logger.info(f"Running npm-groovy-lint on {output_file}")

        cmd = ["npx.cmd", "npm-groovy-lint", "--format", str(output_file)]

        result = subprocess.run(
            cmd,
            capture_output=False,
            text=True,
            check=True
        )
        logger.info("Linting completed successfully")
        if result.stdout:
            logger.info(f"Lint output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Linting failed with exit code {e.returncode}")
        logger.error(f"Error output: {e.stderr}")
        raise e
    except FileNotFoundError:
        logger.error("npm-groovy-lint not found. Please ensure it's installed and in your PATH")
        raise e
    
def validate_config_only(config_path: Path, verbose: bool = True) -> int:
    """
    Validate configuration only and return exit code.
    
    Args:
        config_path: Path to configuration file
        verbose: Show info-level messages
        
    Returns:
        0 if valid, 1 if errors found
    """
    logger.info(f"Validating configuration: {config_path}")
    
    validator = ConfigValidator()
    messages = validator.validate_config_file(config_path)
    
    if messages:
        validator.print_messages(show_info=verbose)
        print(f"\n{validator.get_summary()}")
        logger.error("❌ Configuration validation failed!")
        return 1
    else:
        logger.info("✅ Configuration validation passed!")
        return 0

def main():
    """Main CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate Jenkins pipeline from YAML config',
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
        """
        )
    
    parser.add_argument('config', type=Path, help='YAML configuration file')
    parser.add_argument('-o', '--output', type=Path, help='Output Jenkinsfile path')

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--validate', action='store_true', help='Validate configuration only (no generation)')
    mode_group.add_argument('--generate-documentation', action='store_true', help='Generate configuration documentation')
    
    parser.add_argument('--lint', action='store_true', help='Run npm-groovy-lint on the generated file')
    parser.add_argument('--no-validation', action='store_true', help='Skip configuration validation (not recommended)')

    parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed validation messages including info level')
    parser.add_argument('--quiet', action='store_true', help='Suppress non-error output')
    
    args = parser.parse_args()

    if args.quiet:
        logger.setLevel(logging.WARNING)
    elif args.verbose:
        logger.setLevel(logging.DEBUG)

    if args.generate_documentation:
        try:
            logger.info("Generating documentation...")
            documentation_generator = DocumentationGenerator()
            documentation_generator.generate_documentation()
            logger.info("✅ Documentation generated successfully!")
            return 0
        except Exception as e:
            logger.error(f"Documentation generation failed: {e}")
            return 1
        
    if not args.config:
        parser.error("Configuration file is required (except for --generate-documentation)")

    if args.validate:
        return validate_config_only(args.config, verbose=args.verbose)

    try:
        if not args.no_validation:
            logger.info("Step 1/3: Validating configuration...")
            
            config_validator = ConfigValidator(args.config)
            if not config_validator.validate(not args.quiet):
                return 1

            templates_validator = TemplateValidator(args.config)
            if not templates_validator.validate(not args.quiet):
                return 1
        else:
            logger.warning("⚠️  Skipping configuration validation (--no-validation flag used)")

        # Step 2: Generate Jenkinsfile
        logger.info("Step 2/3: Generating Jenkinsfile...")
        
        generator = JenkinsfileGenerator()
        generator.generate_jenkinsfile(args.config, args.output)
        
        logger.info(f"✅ Jenkinsfile generated successfully: {args.output}")

        # Step 3: Optional linting
        if args.lint:
            logger.info("Step 3/3: Linting generated file...")
            lint_output(args.output)
            logger.info("✅ Linting completed successfully!")
        else:
            logger.info("Step 3/3: Skipping lint (use --lint flag to enable)")

        logger.info("🎉 All steps completed successfully!")
        return 0

    except KeyboardInterrupt:
        logger.error("❌ Operation cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"❌ Generation failed: {e}")
        if args.verbose:
            import traceback
            logger.error(f"Stack trace:\n{traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    main()