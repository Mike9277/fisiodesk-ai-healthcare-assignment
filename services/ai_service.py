"""
AI Service for Natural Language Query Processing
"""
import re
from typing import Dict, List, Optional
from config import Config


class AIDataExtractor:
    def __init__(self):
        self.config = Config()

        self.lombare_patterns = [
            re.compile(p, re.IGNORECASE)
            for p in self.config.LOMBAR_PAIN_PATTERNS
        ]

        self.improvement_patterns = [
            re.compile(p, re.IGNORECASE)
            for p in self.config.IMPROVEMENT_PATTERNS
        ]

        self.worsening_patterns = [
            re.compile(p, re.IGNORECASE)
            for p in self.config.WORSENING_PATTERNS
        ]

        self.negation_patterns = [
            re.compile(p, re.IGNORECASE)
            for p in self.config.NEGATION_PATTERNS
        ]

        # 🔥 RISOLUZIONE (fix Marco & casi simili)
        self.resolution_patterns = [
            re.compile(p, re.IGNORECASE)
            for p in [
                r'nessun dolore',
                r'senza dolore',
                r'completa risoluzione',
                r'risoluzione',
                r'sta benissimo',
                r'nessun sintomo',
                r'assenza di dolore',
                r'controllo finale',
                r'fine trattamento',
                r'dimesso',
            ]
        ]

    def extract_conditions(self, text: str) -> Dict:
        if not text:
            return {
                'has_lombare_pain': False,
                'has_miglioramento': False,
                'has_peggioramento': False,
                'is_resolved': False,
                'confidence': 0.0,
                'raw_matches': {}
            }

        text_lower = text.lower()

        lombare_matches = [
            m for p in self.lombare_patterns for m in p.findall(text_lower)
        ]

        improve_matches = [
            m for p in self.improvement_patterns for m in p.findall(text_lower)
        ]

        worsening_matches = [
            m for p in self.worsening_patterns for m in p.findall(text_lower)
        ]

        negation_matches = [
            m for p in self.negation_patterns for m in p.findall(text_lower)
        ]

        resolution_matches = [
            m for p in self.resolution_patterns for m in p.findall(text_lower)
        ]

        # -----------------------------
        # LOGICA CLINICA CORRETTA
        # -----------------------------
        is_resolved = len(resolution_matches) > 0

        has_lombare = (
            len(lombare_matches) > 0
            and len(negation_matches) == 0
            and not is_resolved
        )

        # 🔥 RISOLTO SOLO SE FRASI FORTI
        is_resolved = any(p.search(text_lower) for p in [
            re.compile(r'controllo finale'),
            re.compile(r'fine trattamento'),
            re.compile(r'dimesso'),
        ])

        # 🔥 MIGLIORAMENTO (ANCHE SE OTTIMO)
        has_miglioramento = (
            len(improve_matches) > 0
            or len(resolution_matches) > 0
        )

        has_peggioramento = (
            len(worsening_matches) > 0
            # and len(improve_matches) == 0
            and not is_resolved
        )

        return {
            'has_lombare_pain': has_lombare,
            'has_miglioramento': has_miglioramento,
            'has_peggioramento': has_peggioramento,
            'is_resolved': is_resolved,
            'confidence': min(0.5 + len(lombare_matches) * 0.1, 1.0),
            'raw_matches': {
                'lombare': lombare_matches,
                'miglioramento': improve_matches,
                'peggioramento': worsening_matches,
                'negazioni': negation_matches,
                'risoluzione': resolution_matches,
            }
        }


class MockAIAnalyzer:
    def __init__(self):
        self._data_extractor = AIDataExtractor()

    def analyze_query_intent(self, query: str) -> Dict:
        q = query.lower().strip()

        patient_name = self._extract_patient_name(query)

        has_lombare = any(w in q for w in ['lombare', 'lombalgia', 'schiena'])
        has_improvement = any(w in q for w in ['miglior', 'recupero', 'progress'])
        has_worsening = any(w in q for w in ['peggior', 'deterior', 'invariato'])
        has_no_show = any(w in q for w in ['saltato', 'no_show', 'mancato'])

        # 👉 conteggio filtri REALI
        active_filters = sum([
            has_lombare,
            has_improvement,
            has_worsening,
            has_no_show
        ])

        # 👉 LOGICA CORRETTA
        if patient_name:
            intent = 'find_by_name'
        elif active_filters == 0:
            intent = 'list_all'
        else:
            intent = 'complex_query'

        return {
            'query': query,
            'intent': intent,
            'patient_name': patient_name,
            'has_condition': has_lombare,
            'condition_type': 'lombare',
            'has_improvement': has_improvement,
            'has_worsening': has_worsening,
            'has_no_show': has_no_show,
            'timeframe_months': 3,
            'ai_used': False,
            'analysis_method': 'rule_based_mock',
        }

    def _extract_patient_name(self, query: str) -> Optional[str]:
        match = re.search(r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b', query)
        return match.group(1) if match else None


class OpenAIAnalyzer:
    def __init__(self, api_key: str):
        self._mock = MockAIAnalyzer()
        self._data_extractor = AIDataExtractor()

    def analyze_query_intent(self, query: str) -> Dict:
        return self._mock.analyze_query_intent(query)

    def extract_conditions(self, text: str) -> Dict:
        return self._data_extractor.extract_conditions(text)


def get_ai_analyzer(provider: str = 'mock', api_key: str = None):
    analyzer = MockAIAnalyzer()
    return AIDataExtractor(), analyzer