import os
import sys
# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai.openrouter_client import OpenRouterClient
from config.settings import settings

print(f"Using OpenRouter Model: {settings.openrouter_model}")
client = OpenRouterClient()

if client.is_available:
    print("Client initialized successfully.")
    print("Sending request 'Hello, who are you?'...")
    response = client.generate("Hello, who are you?")
    print(f"\nResponse:\n{response}")
else:
    print("Client failed to initialize.")
