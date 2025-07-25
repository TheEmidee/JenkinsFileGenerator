from pathlib import Path
import subprocess

from generator import logger

def lint_jenkinsfile(output_file:Path):
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