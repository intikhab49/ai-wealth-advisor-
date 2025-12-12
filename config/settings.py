"""Configuration settings for Wealth Management AI Chatbot."""
import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    """Application configuration settings."""
    
    # LLM Settings
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    google_api_key: str = field(default_factory=lambda: os.getenv("GOOGLE_API_KEY", ""))
    openrouter_api_key: str = field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""))
    primary_model: str = "openrouter"  # "gemini", "openrouter", or "openai"
    openrouter_model: str = field(default_factory=lambda: os.getenv("OPENROUTER_MODEL", "nex-agi/deepseek-v3.1-nex-n1:free"))
    openai_model: str = "gpt-4"
    temperature: float = 0.7
    
    # ChromaDB Settings
    chroma_persist_dir: str = "./chroma_db"
    
    # Flask Settings
    flask_host: str = "0.0.0.0"
    flask_port: int = 5000
    flask_debug: bool = True
    
    # MS Fabric Settings (optional)
    azure_tenant_id: Optional[str] = field(default_factory=lambda: os.getenv("AZURE_TENANT_ID"))
    azure_client_id: Optional[str] = field(default_factory=lambda: os.getenv("AZURE_CLIENT_ID"))
    fabric_workspace_id: Optional[str] = field(default_factory=lambda: os.getenv("FABRIC_WORKSPACE_ID"))
    fabric_lakehouse_name: Optional[str] = field(default_factory=lambda: os.getenv("FABRIC_LAKEHOUSE_NAME"))
    
    # Risk Assessment Parameters
    risk_free_rate: float = 0.04  # 4% risk-free rate
    trading_days_per_year: int = 252
    confidence_level: float = 0.95  # 95% VaR
    
    def validate(self) -> bool:
        """Validate required settings."""
        if self.primary_model == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI mode")
        if self.primary_model == "gemini" and not self.google_api_key:
            print("⚠️ GOOGLE_API_KEY not set - running in demo mode")
        return True


# Global settings instance
settings = Settings()
