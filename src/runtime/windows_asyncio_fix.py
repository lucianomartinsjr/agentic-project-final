from __future__ import annotations

import asyncio
import sys
import warnings


def apply_windows_selector_event_loop_policy() -> None:
    """Necessário para que subprocessos (MCP) funcionem corretamente no Windows."""
    if not sys.platform.startswith("win"):
        return

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
