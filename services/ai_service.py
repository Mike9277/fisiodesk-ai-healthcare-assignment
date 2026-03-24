"""
AI Service for Natural Language Query Processing
Handles both mock AI (for MVP) and real OpenAI integration
"""
import re
import json
from typing import Dict, List, Optional, Tuple
from config import Config


class AIDataExtractor:
    """
    Extracts clinical information from text using pattern matching.
    In production, this would be replaced or enhanced with OpenAI GPT calls.
    """

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

    def extract_conditions(self, text: str) -> Dict:
        if not text:
            return {
                'has_lombare_pain': False,
                'has_miglioramento': False,
                'has_peggioramento': False,
                'confidence': 0.0,
                'matched_terms': [],
                'raw_matches': {'lombare': [], 'miglioramento': [], 'peggioramento': []}
            }

        text_lower = text.lower()

        lombare_matches   = [m for p in self.lombare_patterns     for m in p.findall(text_lower)]
        improve_matches   = [m for p in self.improvement_patterns for m in p.findall(text_lower)]
        worsening_matches = [m for p in self.worsening_patterns   for m in p.findall(text_lower)]

        all_matched = lombare_matches + improve_matches + worsening_matches
        confidence = min(0.5 + len(all_matched) * 0.1, 1.0)

        return {
            'has_lombare_pain':   len(lombare_matches) > 0,
            'has_miglioramento':  len(improve_matches) > 0,
            'has_peggioramento':  len(worsening_matches) > 0,
            'confidence':         confidence,
            'matched_terms':      list(set(all_matched)),
            'raw_matches': {
                'lombare':        list(set(lombare_matches)),
                'miglioramento':  list(set(improve_matches)),
                'peggioramento':  list(set(worsening_matches)),
            }
        }

    def analyze_clinical_document(self, document: Dict) -> Dict:
        text = document.get('descrizione', '')
        extraction = self.extract_conditions(text)
        return {
            'document_id': str(document.get('_id', '')),
            'paziente_id': str(document.get('paziente_id', '')),
            'data':        document.get('data'),
            'conditions':  extraction,
            'source':      document.get('_collection', 'unknown')
        }


class MockAIAnalyzer:
    """
    Mock AI analyzer that simulates OpenAI GPT responses.
    Used for development and demo purposes.
    """

    def __init__(self):
        self._data_extractor = AIDataExtractor()

    def analyze_query_intent(self, query: str) -> Dict:
        """
        Parse a natural-language query into structured parameters that
        execute_complex_query (and the /api/v1/query endpoint) can use.

        Returned keys
        -------------
        intent            : str  — primary intent (see below)
        patient_name      : str | None  — full/partial name to filter by
        has_condition     : bool
        condition_type    : str | None
        has_improvement   : bool | None  (None = "don't care")
        has_no_show       : bool | None  (None = "don't care")
        timeframe_months  : int
        ai_used           : bool
        analysis_method   : str

        Intents
        -------
        list_all          — no filters, return every patient
        find_by_name      — filter by patient name only
        complex_query     — full multi-criteria filter (original target query)
        condition_only    — filter by condition, no improvement/no-show constraint
        """
        q = query.lower().strip()

        # ------------------------------------------------------------------
        # 1. Patient name detection
        # ------------------------------------------------------------------
        patient_name = self._extract_patient_name(query)

        # ------------------------------------------------------------------
        # 2. Detect "show all / list all" intent
        # ------------------------------------------------------------------
        list_all_triggers = [
            'tutti i pazienti', 'tutti pazienti', 'elenco pazienti',
            'lista pazienti', 'mostra pazienti', 'mostrami i pazienti',
            'visualizza pazienti', 'vedi pazienti',
        ]
        is_list_all = any(t in q for t in list_all_triggers)

        # A query that is ONLY "mostra pazienti" (no extra conditions) → list all
        has_extra_filter = any(w in q for w in [
            'lombare', 'schiena', 'lombalgia', 'cervical', 'spalla',
            'miglioramento', 'miglior', 'progress', 'recupero',
            'saltato', 'no_show', 'mancato', 'appuntamento',
            'peggioramento',
        ])

        if patient_name and not has_extra_filter:
            intent = 'find_by_name'
        elif is_list_all and not has_extra_filter:
            intent = 'list_all'
        else:
            intent = 'complex_query'  # will be refined below

        # ------------------------------------------------------------------
        # 3. Condition detection
        # ------------------------------------------------------------------
        has_lombare = any(w in q for w in [
            'lombare', 'lombalgia', 'low back', 'mal di schiena',
            'schiena', 'rachialgia', 'colpo della strega',
        ])
        has_cervical = any(w in q for w in ['cervical', 'collo', 'cervicalgia'])
        has_spalla   = any(w in q for w in ['spalla', 'shoulder'])

        condition_type = None
        if has_lombare:
            condition_type = 'lombare'
        elif has_cervical:
            condition_type = 'cervicale'
        elif has_spalla:
            condition_type = 'spalla'

        has_condition = condition_type is not None

        # ------------------------------------------------------------------
        # 4. Improvement / worsening detection
        # ------------------------------------------------------------------
        asks_improvement = any(w in q for w in [
            'miglioramento', 'migliorat', 'progress', 'recupero', 'sta meglio',
        ])
        asks_worsening = any(w in q for w in [
            'peggioramento', 'peggiorat', 'peggiora',
        ])

        # ------------------------------------------------------------------
        # 5. No-show / compliance detection
        # ------------------------------------------------------------------
        asks_no_show = any(w in q for w in [
            'saltato', 'no_show', 'mancato', 'non si è presentato',
            'non presentato', 'assente', 'appuntamento mancato',
        ])

        # ------------------------------------------------------------------
        # 6. Timeframe
        # ------------------------------------------------------------------
        timeframe_months = 3  # default
        match = re.search(r'(\d+)\s*(?:mese|mesi)', q)
        if match:
            timeframe_months = int(match.group(1))

        # ------------------------------------------------------------------
        # 7. Refine intent
        # ------------------------------------------------------------------
        if intent == 'complex_query':
            if has_condition and not asks_improvement and not asks_no_show:
                intent = 'condition_only'
            elif not has_condition and not asks_improvement and not asks_no_show:
                # Generic query with no recognisable filters
                if patient_name:
                    intent = 'find_by_name'
                else:
                    intent = 'list_all'

        # ------------------------------------------------------------------
        # 8. Map intent → filter flags
        # ------------------------------------------------------------------
        if intent == 'list_all':
            has_condition   = False
            asks_improvement = False
            asks_no_show    = False
        elif intent == 'find_by_name':
            has_condition   = False
            asks_improvement = False
            asks_no_show    = False
        elif intent == 'condition_only':
            asks_improvement = False
            asks_no_show    = False

        return {
            'query':            query,
            'intent':           intent,
            'patient_name':     patient_name,
            'has_condition':    has_condition,
            'condition_type':   condition_type,
            'has_improvement':  asks_improvement,
            'has_no_show':      asks_no_show,
            'timeframe_months': timeframe_months,
            'ai_used':          False,
            'analysis_method':  'rule_based_mock',
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _extract_patient_name(self, query: str) -> Optional[str]:
        """
        Try to extract a patient name from the query.
        Looks for patterns like:
          - "Laura Bianchi"
          - "il paziente Mario Rossi"
          - "paziente: Anna Ferrari"
          - "cerca Mario"
        Returns the matched name fragment or None.
        """
        # Words that start sentences / queries but are NOT names
        STOP_WORDS = {
            'Mostra', 'Mostrami', 'Cerca', 'Trovami', 'Visualizza',
            'Elenca', 'Lista', 'Dammi', 'Dimmi', 'Pazienti', 'Paziente',
        }

        # Pattern: two or more capitalised words (likely First [Middle] Last)
        for match in re.finditer(
            r'\b([A-Z][a-zàáèéìíòóùú]+(?:\s+[A-Z][a-zàáèéìíòóùú]+)+)\b',
            query
        ):
            tokens = match.group(1).split()
            # Skip if ALL tokens are stop-words
            if all(t in STOP_WORDS for t in tokens):
                continue
            # Strip leading stop-words
            while tokens and tokens[0] in STOP_WORDS:
                tokens.pop(0)
            if tokens:
                return ' '.join(tokens)

        # Pattern: after trigger words, single capitalised word
        match = re.search(
            r'(?:paziente|cerca|trovami|mostrami)\s+([A-Z][a-zàáèéìíòóùú]+)',
            query,
            re.IGNORECASE,
        )
        if match:
            return match.group(1)

        return None

    def extract_conditions(self, text: str) -> Dict:
        return self._data_extractor.extract_conditions(text)

    def extract_clinical_summary(self, documents: List[Dict]) -> str:
        if not documents:
            return "Nessun documento clinico disponibile."
        summaries = []
        for doc in documents:
            extraction = self._data_extractor.extract_conditions(doc.get('descrizione', ''))
            if extraction['has_lombare_pain']:
                summaries.append(f"- Dolore lombare ({', '.join(extraction['raw_matches']['lombare'])})")
            if extraction['has_miglioramento']:
                summaries.append(f"- Miglioramento ({', '.join(extraction['raw_matches']['miglioramento'])})")
            if extraction['has_peggioramento']:
                summaries.append(f"- Peggioramento ({', '.join(extraction['raw_matches']['peggioramento'])})")
        return '\n'.join(summaries) if summaries else "Nessuna condizione clinica rilevante."


class OpenAIAnalyzer:
    """Real OpenAI GPT integration — falls back to MockAIAnalyzer for MVP."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._mock = MockAIAnalyzer()
        self._data_extractor = AIDataExtractor()

    def analyze_query_intent(self, query: str) -> Dict:
        return self._mock.analyze_query_intent(query)

    def extract_conditions(self, text: str) -> Dict:
        return self._data_extractor.extract_conditions(text)


def get_ai_analyzer(provider: str = 'mock', api_key: str = None):
    if provider == 'openai' and api_key:
        analyzer = OpenAIAnalyzer(api_key)
    else:
        analyzer = MockAIAnalyzer()
    return AIDataExtractor(), analyzer