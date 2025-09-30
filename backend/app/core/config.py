#!/usr/bin/env python3
"""
Core configuration module for FastAPI Backend
Sử dụng PydanticSettings cho environment variables và configuration management
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings với PydanticSettings
    Hỗ trợ environment variables và default values
    """
    
    # Project metadata
    PROJECT_NAME: str = "Vietnamese Speech-to-Text + Toxic Detection API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Offline-first Vietnamese Speech Analysis with Wav2Vec2 ASR and PhoBERT Classification"
    
    # API Configuration
    API_V1_STR: str = "/v1"
    
    # Server Configuration  
    HOST: str = Field(default="127.0.0.1", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    DEBUG: bool = Field(default=True, description="Debug mode")
    
    # Model Paths - Offline Local Models
    ASR_MODEL_PATH: str = Field(
        default="../wav2vec2-base-vietnamese-250h",
        description="Path to local Wav2Vec2 Vietnamese ASR model"
    )
    CLASSIFIER_MODEL_PATH: str = Field(
        default="../phobert-vi-comment-4class", 
        description="Path to local PhoBERT Vietnamese classifier model"
    )
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
        description="Allowed CORS origins for frontend"
    )
    
    # WebSocket Configuration
    WEBSOCKET_ENDPOINT: str = "/v1/ws"
    
    # Audio Processing Settings
    AUDIO_CHUNK_DURATION: float = Field(default=2.0, description="Audio chunk duration in seconds")
    MIN_AUDIO_DURATION: float = Field(default=0.1, description="Minimum audio duration in seconds")
    MAX_AUDIO_DURATION: float = Field(default=30.0, description="Maximum audio duration in seconds")
    TARGET_SAMPLE_RATE: int = Field(default=16000, description="Target sample rate for ASR")
    
    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Log format: json or console")
    
    # Model Configuration
    MODEL_DEVICE: str = Field(default="cpu", description="Device for model inference: cpu or cuda")
    MODEL_CACHE_SIZE: int = Field(default=1, description="Number of model instances to cache")
    
    # Security Settings
    ALLOWED_AUDIO_FORMATS: list[str] = Field(
        default=["audio/webm", "audio/wav", "audio/ogg"],
        description="Allowed audio MIME types"
    )
    
    # Performance Settings
    MAX_CONCURRENT_CONNECTIONS: int = Field(default=100, description="Max concurrent WebSocket connections")
    REQUEST_TIMEOUT: float = Field(default=30.0, description="Request timeout in seconds")
    
    class Config:
        """Pydantic configuration"""
        case_sensitive = True
        # Use backend/.env (resolved relative to this file) so running from project root still loads backend env
        env_file = str(Path(__file__).resolve().parents[2] / ".env")
        env_file_encoding = "utf-8"
        
    def get_model_paths(self) -> dict[str, Path]:
        """
        Get resolved model paths
        
        Returns:
            Dictionary với resolved paths cho ASR và Classifier models
        """
        # Resolve model paths relative to the backend package directory (two parents up)
        # Defaults like '../wav2vec2-base-vietnamese-250h' are written relative to backend/
        backend_dir = Path(__file__).resolve().parents[2]
        asr_path = (backend_dir / Path(self.ASR_MODEL_PATH)).resolve()
        classifier_path = (backend_dir / Path(self.CLASSIFIER_MODEL_PATH)).resolve()

        return {
            "asr": asr_path,
            "classifier": classifier_path,
        }
    
    def validate_model_paths(self) -> dict[str, bool]:
        """
        Validate model paths exist
        
        Returns:
            Dictionary với validation status cho từng model path
        """
        paths = self.get_model_paths()
        
        return {
            "asr_exists": paths["asr"].exists(),
            "classifier_exists": paths["classifier"].exists(),
            "asr_has_config": (paths["asr"] / "config.json").exists(),
            "classifier_has_config": (paths["classifier"] / "config.json").exists()
        }
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.DEBUG
        
    @property  
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as list"""
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]
        return self.BACKEND_CORS_ORIGINS


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Dependency function to get settings instance
    
    Returns:
        Settings instance for dependency injection
    """
    return settings


# Development helper functions
def print_model_status():
    """Print model validation status for debugging"""
    validation = settings.validate_model_paths()
    paths = settings.get_model_paths()
    
    print("🔍 MODEL VALIDATION STATUS:")
    print(f"   ASR Path: {paths['asr']}")
    print(f"   ASR Exists: {'✅' if validation['asr_exists'] else '❌'}")
    print(f"   ASR Config: {'✅' if validation['asr_has_config'] else '❌'}")
    
    print(f"   Classifier Path: {paths['classifier']}")
    print(f"   Classifier Exists: {'✅' if validation['classifier_exists'] else '❌'}")
    print(f"   Classifier Config: {'✅' if validation['classifier_has_config'] else '❌'}")


if __name__ == "__main__":
    # Development testing
    print("🚀 FASTAPI BACKEND CONFIGURATION")
    print("=" * 50)
    
    print(f"Project: {settings.PROJECT_NAME}")
    print(f"Version: {settings.VERSION}")
    print(f"Debug: {settings.DEBUG}")
    print(f"Host: {settings.HOST}:{settings.PORT}")
    print(f"CORS Origins: {settings.cors_origins_list}")
    
    print("\n" + "=" * 50)
    print_model_status()
    
    print("\n" + "=" * 50)
    print("✅ Configuration loaded successfully!")