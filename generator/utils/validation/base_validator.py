"""Base Validator Module
This module defines the base validator class for validating configurations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
import traceback
from typing import List, Optional

from colorama import Fore, Style, init

from generator import logger


@dataclass
class ValidationMessage:
    """Represents a validation error or warning with location info"""

    level: str  # 'error', 'warning', 'info'
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    column: Optional[int] = None
    context: Optional[str] = None
    suggestion: Optional[str] = None

    def __str__(self):
        location = ""
        if self.file_path:
            location += f"File: {self.file_path}"
        if self.line_number:
            location += f", Line: {self.line_number}"
        if self.column:
            location += f", Column: {self.column}"
        if self.context:
            location += f", {self.get_context_output_name()}: {self.context}"

        result = f"[{self.level.upper()}] {self.message}"
        if location:
            result += f" ({location})"
        if self.suggestion:
            result += f"\n  💡 Suggestion: {self.suggestion}"

        return result

    @abstractmethod
    def get_context_output_name(self) -> str:
        """Return a string representation of the context for output"""


class BaseValidator(ABC):
    """Base class for validators"""

    def __init__(self):
        self.messages: List[ValidationMessage] = []

    def validate(self, print_summary: bool = True) -> bool:
        """Validate the configuration and print the warnings and errors messages"""
        self.messages.clear()

        try:
            self._validate_internal()
        except Exception as e:
            self._add_message("error", f"Unexpected validation error: {str(e)}")
            logger.error("Validation exception: %s", traceback.format_exc())

        if self.messages and print_summary:
            self.print_messages(show_info=True)
            print(f"\n{self.get_summary()}")

        if self.has_errors():
            logger.error(
                "❌ %s validation failed! Use --no-validation to skip (not recommended)",
                self._get_validation_identifier(),
            )
            return False
        if self.has_warnings():
            logger.warning(
                "⚠️ %s has warnings but is valid", self._get_validation_identifier()
            )
        else:
            logger.info("✅ %s validation passed!", self._get_validation_identifier())

        return True

    @abstractmethod
    def _validate_internal(self):
        pass

    @abstractmethod
    def _get_validation_identifier(self) -> str:
        pass

    def _get_file_path(self) -> Path:
        return Path()

    def _add_message(
        self,
        level: str,
        message: str,
        file_path: Path = None,
        line_number: Optional[int] = None,
        column: Optional[int] = None,
        context: Optional[str] = None,
        suggestion: Optional[str] = None,
    ):
        """Add a validation message"""
        if file_path is None:
            file_path = self._get_file_path()

        self.messages.append(
            ValidationMessage(
                level=level,
                message=message,
                file_path=file_path,
                line_number=line_number,
                column=column,
                context=context,
                suggestion=suggestion,
            )
        )

    def has_errors(self) -> bool:
        """Check if there are any error-level messages"""
        return any(msg.level == "error" for msg in self.messages)

    def has_warnings(self) -> bool:
        """Check if there are any warning-level messages"""
        return any(msg.level == "warning" for msg in self.messages)

    def print_messages(self, show_info: bool = True):
        """Print all validation messages with colors"""
        try:
            init()  # Initialize colorama

            colors = {"error": Fore.RED, "warning": Fore.YELLOW, "info": Fore.BLUE}
        except ImportError:
            # Fallback without colors
            colors = {"error": "", "warning": "", "info": ""}
            Style.RESET_ALL = ""

        for msg in self.messages:
            if not show_info and msg.level == "info":
                continue

            color = colors.get(msg.level, "")
            print(f"{color}{msg}{Style.RESET_ALL}")

    def get_summary(self) -> str:
        """Get a summary of validation results"""
        error_count = sum(1 for msg in self.messages if msg.level == "error")
        warning_count = sum(1 for msg in self.messages if msg.level == "warning")
        info_count = sum(1 for msg in self.messages if msg.level == "info")

        if error_count == 0 and warning_count == 0:
            return f"✅ {self._get_validation_identifier()} is valid! ({info_count} info messages)"
        if error_count == 0:
            return f"⚠️ {self._get_validation_identifier()} is valid with {warning_count} warnings ({info_count} info messages)"

        return f"❌ {self._get_validation_identifier()} has {error_count} errors and {warning_count} warnings"
