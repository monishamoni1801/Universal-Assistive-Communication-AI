# Routes package initialization
from .stt_routes import stt_bp
from .tts_routes import tts_bp
from .sign_routes import sign_bp
from .emergency_routes import emergency_bp

__all__ = ['stt_bp', 'tts_bp', 'sign_bp', 'emergency_bp']