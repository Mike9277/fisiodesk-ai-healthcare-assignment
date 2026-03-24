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
        
        # Compile patterns for performance
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
    
    def extract_conditions(self, text: str) -> Dict[str, any]:
        """
        Extract clinical conditions from text.
        Returns dict with conditions, confidence scores, and matched terms.
        """
        if not text:
            return {
                'has_lombare_pain': False,
                'has_miglioramento': False,
                'has_peggioramento': False,
                'confidence': 0.0,
                'matched_terms': []
            }
        
        text_lower = text.lower()
        matched_terms = []
        
        # Check for lombare pain
        lombare_matches = []
        for pattern in self.lombare_patterns:
            matches = pattern.findall(text_lower)
            lombare_matches.extend(matches)
        
        has_lombare_pain = len(lombare_matches) > 0
        matched_terms.extend(lombare_matches)
        
        # Check for improvement
        improvement_matches = []
        for pattern in self.improvement_patterns:
            matches = pattern.findall(text_lower)
            improvement_matches.extend(matches)
        
        has_miglioramento = len(improvement_matches) > 0
        matched_terms.extend(improvement_matches)
        
        # Check for worsening
        worsening_matches = []
        for pattern in self.worsening_patterns:
            matches = pattern.findall(text_lower)
            worsening_matches.extend(matches)
        
        has_peggioramento = len(worsening_matches) > 0
        matched_terms.extend(worsening_matches)
        
        # Calculate confidence based on number of matches
        total_matches = len(matched_terms)
        confidence = min(0.5 + (total_matches * 0.1), 1.0)
        
        return {
            'has_lombare_pain': has_lombare_pain,
            'has_miglioramento': has_miglioramento,
            'has_peggioramento': has_peggioramento,
            'confidence': confidence,
            'matched_terms': list(set(matched_terms)),
            'raw_matches': {
                'lombare': list(set(lombare_matches)),
                'miglioramento': list(set(improvement_matches)),
                'peggioramento': list(set(worsening_matches))
            }
        }
    
    def analyze_clinical_document(self, document: Dict) -> Dict:
        """
        Analyze a clinical document (scheda_valutazione or diario_trattamenti).
        """
        text = document.get('descrizione', '')
        extraction = self.extract_conditions(text)
        
        return {
            'document_id': str(document.get('_id', '')),
            'paziente_id': str(document.get('paziente_id', '')),
            'data': document.get('data'),
            'conditions': extraction,
            'source': document.get('_collection', 'unknown')
        }


class MockAIAnalyzer:
    """
    Mock AI analyzer that simulates OpenAI GPT responses.
    Used for development and demo purposes.
    """
    
    def analyze_query_intent(self, query: str) -> Dict:
        """
        Simulates AI intent recognition for natural language queries.
        """
        query_lower = query.lower()
        
        # Determine intent based on keywords
        intents = []
        
        if any(word in query_lower for word in ['mostra', 'trova', 'elenco', 'lista', 'quali']):
            intents.append('list_patients')
        
        if any(word in query_lower for word in ['dolore', 'lombare', 'lombalgia', 'cervical']):
            intents.append('filter_by_condition')
        
        if any(word in query_lower for word in ['miglioramento', 'miglior', 'progress', 'recupero']):
            intents.append('filter_by_improvement')
        
        if any(word in query_lower for word in ['saltato', 'no_show', 'mancato', 'appuntamento']):
            intents.append('filter_by_compliance')
        
        # Extract timeframe
        timeframe = '3_mesi'  # default
        if 'ultimi' in query_lower or 'ultime' in query_lower:
            if 'mese' in query_lower or 'mesi' in query_lower:
                match = re.search(r'(\d+)\s*(?:mese|mesi)', query_lower)
                if match:
                    timeframe = f'{match.group(1)}_mesi'
        
        return {
            'query': query,
            'intents': intents,
            'timeframe': timeframe,
            'condition_type': 'dolore_lombare' if 'lombare' in query_lower or 'schiena' in query_lower else None,
            'compliance_status': 'no_show' if any(w in query_lower for w in ['saltato', 'no_show', 'mancato']) else None,
            'ai_used': False,
            'analysis_method': 'rule_based_mock'
        }
    
    def extract_clinical_summary(self, documents: List[Dict]) -> str:
        """
        Generate a clinical summary from multiple documents.
        """
        if not documents:
            return "Nessun documento clinico disponibile."
        
        summaries = []
        for doc in documents:
            text = doc.get('descrizione', '')
            extraction = self.extract_conditions(text)
            
            if extraction['has_lombare_pain']:
                summaries.append(f"- Dolore lombare rilevato ({', '.join(extraction['raw_matches']['lombare'])})")
            if extraction['has_miglioramento']:
                summaries.append(f"- Miglioramento rilevato ({', '.join(extraction['raw_matches']['miglioramento'])})")
            if extraction['has_peggioramento']:
                summaries.append(f"- Peggioramento rilevato ({', '.join(extraction['raw_matches']['peggioramento'])})")
        
        return '\n'.join(summaries) if summaries else "Nessuna condizione clinica rilevante."
    
    def extract_conditions(self, text: str) -> Dict:
        """Forward to AIDataExtractor"""
        return self._data_extractor.extract_conditions(text)
    
    def __init__(self):
        self._data_extractor = AIDataExtractor()


class OpenAIAnalyzer:
    """
    Real OpenAI GPT integration for production use.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1"
        self._data_extractor = AIDataExtractor()
    
    def analyze_query_intent(self, query: str) -> Dict:
        """
        Use GPT to analyze query intent.
        Falls back to rule-based if API fails.
        """
        if not self.api_key:
            return MockAIAnalyzer().analyze_query_intent(query)
        
        # In production, make actual OpenAI API call here
        # For MVP, we use the mock implementation
        return MockAIAnalyzer().analyze_query_intent(query)
    
    def extract_conditions(self, text: str) -> Dict:
        """Forward to AIDataExtractor"""
        return self._data_extractor.extract_conditions(text)


def get_ai_analyzer(provider: str = 'mock', api_key: str = None) -> Tuple[AIDataExtractor, object]:
    """
    Factory function to get the appropriate AI analyzer.
    """
    if provider == 'openai' and api_key:
        analyzer = OpenAIAnalyzer(api_key)
    else:
        analyzer = MockAIAnalyzer()
    
    return AIDataExtractor(), analyzer
