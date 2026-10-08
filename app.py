"""Local entry point for the SupportPilot multi-agent demo."""

import gradio as gr
from src.ui.app import create_app
from src.config import settings
from src.ui.styles import CUSTOM_CSS

if __name__ == "__main__":
    app = create_app()
    app.launch(
        server_name="127.0.0.1",
        server_port=settings.port,
        share=False,
        show_error=False,
        css=CUSTOM_CSS,
        theme=gr.themes.Soft(primary_hue="blue", secondary_hue="slate"),
    )
