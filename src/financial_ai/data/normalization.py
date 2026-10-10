from __future__ import annotations

import re

INDIAN_SUFFIXES = (".NS", ".BO")
MAX_SYMBOL_LENGTH = 32

# Supports symbols such as AAPL, RELIANCE.NS, BRK.B and symbols
# containing digits, ampersands or hyphens.
SYMBOL_PATTERN = re.compile(r"[A-Z0-9&-]+(?:\.[A-Z0-9&-]+)*")


class InvalidSymbolError(ValueError):
    """Raised when a market symbol has invalid syntax."""


def normalize_symbol(symbol: str) -> str:
    """Trim and uppercase a valid market symbol without changing its suffix."""
    if not isinstance(symbol, str):
        raise InvalidSymbolError("Symbol must be a string.")

    value = symbol.strip().upper()

    if not value:
        raise InvalidSymbolError("Symbol cannot be empty.")

    if len(value) > MAX_SYMBOL_LENGTH:
        raise InvalidSymbolError(f"Symbol cannot exceed {MAX_SYMBOL_LENGTH} characters.")

    if not SYMBOL_PATTERN.fullmatch(value):
        raise InvalidSymbolError("Symbol contains invalid characters or formatting.")

    return value


def infer_market(symbol: str) -> str:
    """Infer the market from a normalized symbol."""
    value = normalize_symbol(symbol)

    if value.endswith(".NS"):
        return "NSE"
    if value.endswith(".BO"):
        return "BSE"

    return "US_OR_OTHER"
