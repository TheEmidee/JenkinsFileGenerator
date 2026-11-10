"""Printing of Validation messages and their summary."""

import sys
from typing import Sequence

from colorama import Fore, Style, init

from generator import logger
from generator.core.validation_message import ValidationMessage

_COLORS = {"error": Fore.RED, "warning": Fore.YELLOW, "info": Fore.BLUE}


def report_messages(identifier: str, messages: Sequence[ValidationMessage], print_details: bool = True) -> bool:
    """Print the messages and a summary, log the outcome, and return True when there are no errors.

    Args:
        identifier: What was validated, e.g. "Configuration" or "Template".
        messages: The Validation messages to report.
        print_details: Print each message and the summary line. The outcome is always logged.
    """
    errors = sum(1 for msg in messages if msg.level == "error")
    warnings = sum(1 for msg in messages if msg.level == "warning")
    infos = sum(1 for msg in messages if msg.level == "info")

    if messages and print_details:
        init()
        for msg in messages:
            _print(f"{_COLORS.get(msg.level, '')}{msg}{Style.RESET_ALL}")
        _print(f"\n{_summary(identifier, errors, warnings, infos)}")

    if errors:
        logger.error("❌ %s validation failed!", identifier)
        return False
    if warnings:
        logger.warning("⚠️ %s has warnings but is valid", identifier)
    else:
        logger.info("✅ %s validation passed!", identifier)
    return True


def _print(text: str) -> None:
    """Print, replacing characters (e.g. emoji) the console encoding cannot represent instead of crashing."""
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    print(text.encode(encoding, errors="replace").decode(encoding))


def _summary(identifier: str, errors: int, warnings: int, infos: int) -> str:
    if errors == 0 and warnings == 0:
        return f"✅ {identifier} is valid! ({infos} info messages)"
    if errors == 0:
        return f"⚠️ {identifier} is valid with {warnings} warnings ({infos} info messages)"
    return f"❌ {identifier} has {errors} errors and {warnings} warnings"
