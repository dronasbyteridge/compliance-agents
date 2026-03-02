# This file is kept for backward compatibility
# The main application now uses the unified interface with chatbot
from app.ui.unified_app import launch_unified_app

def launch_app():
    """Launch the unified app (includes original features + chatbot)"""
    launch_unified_app()

if __name__ == "__main__":
    launch_app()
