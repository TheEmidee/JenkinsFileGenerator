import os

from pathlib import Path

MAKO_BLOCKS = [
    "libraries",
    "imports",
    "properties",
    "pre_pipeline_steps",
    "build_steps",
    "on_build_unstable",
    "on_build_failure",
    "on_build_success",
    "post_build_steps",
    "on_exception_thrown",
    "on_finally",
    "additional_functions",
]

TEMPLATES_FOLDER = Path(os.path.realpath(__file__)) / "../../templates"
