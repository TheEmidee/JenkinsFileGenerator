"""Validation message: one located finding about a Pipeline config or a template."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

ValidationLevel = Literal["error", "warning", "info"]


@dataclass(frozen=True)
class ValidationMessage:
    """Represents a validation error, warning or info with location info."""

    level: ValidationLevel
    message: str
    file_path: Optional[Path] = None
    line_number: Optional[int] = None
    column: Optional[int] = None
    context: Optional[str] = None
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        location_parts = []
        if self.file_path:
            location_parts.append(f"File: {self.file_path}")
        if self.line_number:
            location_parts.append(f"Line: {self.line_number}")
        if self.column:
            location_parts.append(f"Column: {self.column}")
        if self.context:
            location_parts.append(f"Context: {self.context}")

        result = f"[{self.level.upper()}] {self.message}"
        if location_parts:
            result += f" ({', '.join(location_parts)})"
        if self.suggestion:
            result += f"\n  💡 Suggestion: {self.suggestion}"

        return result
