"""Utility for linting Jenkinsfiles using npm-groovy-lint."""

from pathlib import Path
import subprocess

from generator import logger


def lint_jenkinsfile(output_file: Path):
    """Run npm-groovy-lint on the generated Jenkinsfile."""
    try:
        logger.info("Running npm-groovy-lint on %s", output_file)

        cmd = ["npx.cmd", "npm-groovy-lint", "--format", str(output_file)]

        result = subprocess.run(cmd, capture_output=False, text=True, check=True)
        logger.info("Linting completed successfully")
        if result.stdout:
            logger.info("Lint output: %s", result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error("Linting failed with exit code %s", e.returncode)
        logger.error("Error output: %s", e.stderr)
        raise e
    except FileNotFoundError as e:
        logger.error(
            "npm-groovy-lint not found. Please ensure it's installed and in your PATH"
        )
        raise e
