from pathlib import Path


class ConfigValidationContext:
    def __init__(self, config_file_path: Path) -> None:
        self.config_file_path = config_file_path
