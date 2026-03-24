"""
FisioDesk AI Query System - Flask API
Main application entry point
"""
import time
import os
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

from config import Config
from services.data_service import DataService
from services.ai_service import AIDataExtractor, MockAIAnalyzer, get_ai_analyzer

app = Flask(__name__, static_folder='.', template_folder='.')
CORS(app)

if not os.path.exists('index.html'):
    print("WARNING: index.html not found!")

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/index.html')
def index_html():
    return send_file('index.html')

# Initialize services
config = Config()
data_service = DataService()
ai_extractor, ai_analyzer = get_ai_analyzer(
    provider=config.AI_PROVIDER,
    api_key=config.OPENAI_API_KEY
)


@app.route('/api/v1/health', methods=['GET'])
def health_check():
    try:
        data_service.connect()
        data_service.db.command('ping')
        mongo_status = 'ok'
    except Exception as e:
        mongo_status = f'error: {str(e)}'

    return jsonify({
        'status': 'ok' if mongo_status == 'ok' else 'degraded',
        'mongodb': mongo_status,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/v1/query', methods=['POST'])
def execute_query():
    """
    Execute a natural language query on clinical data.

    Request body:
    {
        "query": "mostra pazienti con dolore lombare...",
        "reference_date": "2024-12-31"  (optional)
    }
    """
    start_time = time.time()

    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        reference_date_str = data.get('reference_date', config.TIMEFRAME_REFERENCE_DATE)

        try:
            reference_date = datetime.fromisoformat(
                reference_date_str.replace('Z', '+00:00')
            ).replace(tzinfo=None)
        except Exception:
            reference_date = datetime(2024, 12, 31)

        # ── Analyse intent ──────────────────────────────────────────────────
        analysis = ai_analyzer.analyze_query_intent(query)
        intent        = analysis.get('intent', 'complex_query')
        patient_name  = analysis.get('patient_name')

        # ── Build query parameters from intent ─────────────────────────────
        if intent == 'list_all':
            # Return all patients, no filters
            results = data_service.get_all_patients()

        elif intent == 'find_by_name':
            # Filter patients by name
            results = data_service.get_patients_by_name(patient_name or query)

        else:
            # complex_query or condition_only — use the flag-based pipeline
            results = data_service.execute_complex_query(
                has_condition    = analysis.get('has_condition', False),
                condition_type   = analysis.get('condition_type', 'lombare'),
                has_improvement  = analysis.get('has_improvement', False),
                timeframe_months = analysis.get('timeframe_months', 3),
                has_no_show      = analysis.get('has_no_show', False),
                reference_date   = reference_date,
            )

            # If the complex query found nothing, check whether the user
            # mentioned a specific patient name and fall back to name search.
            if not results and patient_name:
                results = data_service.get_patients_by_name(patient_name)

        execution_time = time.time() - start_time

        return jsonify({
            'success': True,
            'query':   query,
            'analysis': analysis,
            'results': format_results(results),
            'metadata': {
                'total_results':          len(results),
                'execution_time_seconds': round(execution_time, 3),
                'reference_date':         reference_date.isoformat(),
                'intent':                 intent,
                'patient_name':           patient_name,
                'ai_used':                analysis.get('ai_used', False),
                'analysis_method':        analysis.get('analysis_method', 'rule_based'),
            }
        })

    except Exception as e:
        execution_time = time.time() - start_time
        return jsonify({
            'success': False,
            'error':   str(e),
            'query':   data.get('query', '') if data else '',
            'metadata': {
                'execution_time_seconds': round(execution_time, 3)
            }
        }), 500


@app.route('/api/v1/patients', methods=['GET'])
def list_all_patients():
    """Return all patients."""
    try:
        results = data_service.get_all_patients()
        return jsonify({
            'success': True,
            'results': format_results(results),
            'metadata': {'total_results': len(results)}
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/patients/<patient_id>/summary', methods=['GET'])
def get_patient_summary(patient_id):
    try:
        patient = data_service.get_patient_details(patient_id)
        if not patient:
            return jsonify({'success': False, 'error': 'Patient not found'}), 404

        return jsonify({
            'success':      True,
            'patient':      patient,
            'evaluations':  data_service.get_patient_evaluations(patient_id, limit=10),
            'appointments': data_service.get_patient_appointments(patient_id, limit=10),
            'treatments':   data_service.get_patient_treatments(patient_id, limit=10),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/analyze', methods=['POST'])
def analyze_text():
    try:
        data = request.get_json()
        text = data.get('text', '')
        extraction = ai_extractor.extract_conditions(text)
        return jsonify({'success': True, 'text': text, 'extraction': extraction})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/data/import', methods=['POST'])
def import_data():
    try:
        data_dir = request.json.get('data_dir', 'data') if request.json else 'data'
        success = data_service.import_sample_data(data_dir)
        return jsonify({
            'success': success,
            'message': 'Data imported successfully' if success else 'Error importing data'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/demo/target-query', methods=['GET'])
def demo_target_query():
    start_time = time.time()
    try:
        results = data_service.execute_complex_query(
            has_condition    = True,
            condition_type   = 'lombare',
            has_improvement  = True,
            timeframe_months = 3,
            has_no_show      = True,
            reference_date   = datetime(2024, 12, 31),
        )
        execution_time = time.time() - start_time
        return jsonify({
            'success': True,
            'query':   "Mostra pazienti con dolore lombare che hanno mostrato miglioramento negli ultimi 3 mesi ma hanno saltato l'ultimo appuntamento",
            'results': format_results(results),
            'metadata': {
                'total_results':          len(results),
                'execution_time_seconds': round(execution_time, 3),
                'description':            'Query target implementata con successo',
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ── Helpers ────────────────────────────────────────────────────────────────

def format_results(results):
    """Format query results for API response."""
    formatted = []
    for result in results:
        paziente         = result.get('paziente', {})
        no_show          = result.get('no_show')
        ultima_val       = result.get('ultima_valutazione')
        conditions       = ultima_val.get('conditions') if ultima_val else None

        formatted.append({
            'id':                paziente.get('_id'),
            'nome':              paziente.get('nome'),
            'cognome':           paziente.get('cognome'),
            'eta':               paziente.get('eta'),
            'telefono':          paziente.get('telefono'),
            'email':             paziente.get('email'),
            'stato':             paziente.get('stato'),
            'data_registrazione': paziente.get('data_registrazione'),
            'condizione':        'Dolore Lombare' if result.get('has_lombare') else 'N/D',
            'miglioramento':     'Rilevato' if result.get('has_improvement') else 'N/D',
            'ultimo_appuntamento': {
                'data':  no_show.get('data'),
                'stato': no_show.get('stato'),
                'note':  no_show.get('note'),
            } if no_show else None,
            'ultima_valutazione': {
                'data':              ultima_val.get('data'),
                'descrizione':       (ultima_val.get('descrizione', '')[:200] + '...') if ultima_val else None,
                'condizioni_estratte': conditions,
            } if ultima_val else None,
            'azioni_consigliate': generate_recommended_actions(paziente, no_show),
        })

    return formatted


def generate_recommended_actions(patient, no_show):
    actions = []
    if no_show:
        actions.append("Contattare il paziente per riprogrammare l'appuntamento")
        actions.append('Verificare eventuali difficoltà/fuori budget')
    if patient.get('stato') == 'attivo':
        actions.append('Continuare il monitoraggio del paziente')
    if not actions:
        actions.append('Nessuna azione immediata richiesta')
    return actions


if __name__ == '__main__':
    print("=" * 60)
    print("FisioDesk AI Query System")
    print("=" * 60)
    print(f"Starting API server on {config.HOST}:{config.PORT}")
    print(f"MongoDB: {config.MONGODB_URI}")
    print(f"AI Provider: {config.AI_PROVIDER}")
    print("=" * 60)

    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)