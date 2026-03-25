"""
Configuration for FisioDesk AI Query System
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""

    # Flask
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT = int(os.getenv('FLASK_PORT', 5000))

    # MongoDB
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    MONGODB_DB = os.getenv('MONGODB_DB', 'fisiodesk')

    # AI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'mock')  # 'openai', 'mock', 'anthropic'
    AI_FALLBACK_TO_RULES = os.getenv('AI_FALLBACK_TO_RULES', 'true').lower() == 'true'

    # Query Configuration
    TIMEFRAME_DEFAULT_MONTHS = 3
    TIMEFRAME_REFERENCE_DATE = os.getenv('TIMEFRAME_REFERENCE_DATE', '2024-12-31')

    # Cache Configuration
    CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
    CACHE_TTL_SECONDS = int(os.getenv('CACHE_TTL_SECONDS', 300))

    # ---------------------------------------------------------------------------
    # Medical Term Patterns (Italian)
    # ---------------------------------------------------------------------------

    LOMBAR_PAIN_PATTERNS = [
        r"\bdolore lombare\b",
        r"\blombalgia\b",
        r"\blow back pain\b",
        r"\bmal di schiena\b",
        r"\brachialgia lombare\b",
        r"\bdolore alla bassa schiena\b",
        r"\bcolpo della strega\b",
    ]

    IMPROVEMENT_PATTERNS = [
        r"\bmiglioramento\b",
        r"\bmigliorato\b",
        r"\bmigliora\b",
        r"\bsta meglio\b",
        r"\bprogressi\b",
        r"\bottimi progressi\b",
        r"\brecupero\b",
        r"\brecuperato\b",
        r"\brisoluzione\b",
        r"\brisolto\b",
        r"\bnetto miglioramento\b",
        r"\bsituazione eccellente\b",
        r"\bcompleta risoluzione\b",
        r"\bbuon recupero\b",
        r"\bquasi senza dolore\b",
        r"\bsta benissimo\b",
        r"\bnessun dolore residuo\b",
        r"\bcompletamente recuperato\b",
        r"\bcompletamente guarito\b",
    ]

    # Worsening: explicit deterioration terms only.
    # "situazione stazionaria" and "persistente" intentionally excluded —
    # they describe lack of improvement, not active worsening, and were
    # causing false positives (e.g. flagging patients in stable condition).
    WORSENING_PATTERNS = [
        r"\bpeggioramento\b",
        r"\bpeggiorato\b",
        r"\bpeggiora\b",
        r"\bnon migliora\b",
        r"\bdeterioramento\b",
        r"\binvariato\b",
        r"\blieve peggioramento\b",
    ]

    # Negation patterns: suppress "has_lombare_pain" when pain is explicitly absent
    NEGATION_PATTERNS = [
        r"\bnessun(?:\s+\w+){0,3}\s+dolore\b",
        r"\bnessuna(?:\s+\w+){0,3}\s+dolore\b",
        r"\bassenza(?:\s+di)?(?:\s+\w+){0,3}\s+dolore\b",
        r"\bnon\s+(?:ha|presenta|riferisce)(?:\s+\w+){0,3}\s+dolore\b",
        r"\bsenza(?:\s+\w+){0,3}\s+dolore\b",
        r"\bdolore\s+(?:risolto|scomparso)\b",
    ]

    # Resolution patterns: patient discharged / fully healed.
    # Used ONLY to detect "is_resolved" state — does NOT suppress lombare signal
    # when scanning historical records (the patient DID have lombare pain).
    RESOLUTION_PATTERNS = [
        r"\bcontrollo finale\b",
        r"\bfine trattamento\b",
        r"\bdimesso\b",
        r"\bnessun dolore residuo\b",
        r"\bsta benissimo\b",
        r"\bcompleta risoluzione\b",
        r"\bcompletamente recuperato\b",
        r"\bcompletamente guarito\b",
    ]