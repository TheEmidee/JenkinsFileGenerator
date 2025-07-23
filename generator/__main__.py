from pathlib import Path
import subprocess
import sys

from generator.core.pipeline_config import PipelineConfig
from generator.documentation.documentation_generator import DocumentationGenerator

from . import logger
from .core.jenkins_file_generator import JenkinsfileGenerator
from .features import *

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

def main():
    """Main CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Generate Jenkins pipeline from YAML config')
    parser.add_argument('config', type=Path, help='YAML configuration file')
    parser.add_argument('-o', '--output', type=Path, help='Output Jenkinsfile path')
    parser.add_argument('--lint', action='store_true', help='Runs npm-groovy-lint on the generated file')
    parser.add_argument('--generate_documentation', action='store_true', help='Generates the documentation')
    
    args = parser.parse_args()

    if args.generate_documentation:
        try:
            documentation_generator = DocumentationGenerator()
            documentation_generator.generate_documentation()
            # sys.exit(0)
        except Exception as e:
            logger.error(f"{e}")
            sys.exit(1)

    try:
        generator = JenkinsfileGenerator()
        generator.generate_jenkinsfile(args.config, args.output)

        if args.lint:
            lint_output(args.output)
    except Exception as e:
        logger.error(f"{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()