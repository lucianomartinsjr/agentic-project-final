from __future__ import annotations

import os
import sys

import gradio as gr


def _ensure_project_root_on_path() -> None:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)


def main() -> None:
    _ensure_project_root_on_path()

    from src.runtime.windows_asyncio_fix import apply_windows_selector_event_loop_policy
    from src.ui.gradio_app import MODAL_CSS, create_demo

    apply_windows_selector_event_loop_policy()
    demo = create_demo()
    demo.launch(theme=gr.themes.Soft(), css=MODAL_CSS)


if __name__ == "__main__":
    main()