#!/usr/bin/env python3
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from services.telegram_service import start_polling

app = create_app()

def app_context_provider():
    return app.app_context()

if __name__ == "__main__":
    print("Starting Telegram Bot Service...")
    start_polling(app_context_provider)
