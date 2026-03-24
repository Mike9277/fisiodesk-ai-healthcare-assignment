"""
Data Service for MongoDB Operations
Handles all database queries and data aggregation
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from bson import ObjectId
from pymongo import MongoClient
from config import Config
from services.ai_service import AIDataExtractor


class DataService:
    """
    Service for accessing and querying MongoDB data.
    """

    def __init__(self, mongo_uri: str = None, db_name: str = None):
        self.config = Config()
        self.mongo_uri = mongo_uri or self.config.MONGODB_URI
        self.db_name = db_name or self.config.MONGODB_DB
        self._client = None
        self._db = None
        self._ai_extractor = AIDataExtractor()

    def connect(self):
        """Establish database connection"""
        if self._client is None:
            self._client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            self._db = self._client[self.db_name]
        return self._db

    def close(self):
        """Close database connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None

    @property
    def db(self):
        """Get database instance, connecting if necessary"""
        if self._db is None:
            self.connect()
        return self._db

    def load_json_data(self, filepath: str) -> List[Dict]:
        """Load data from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def import_sample_data(self, data_dir: str = 'data'):
        """
        Import sample JSON data into MongoDB collections.
        NOTE: Prefer the mongoimport-based seed in docker-compose for correct
        EJSON handling ($oid -> ObjectId, $date -> ISODate).
        This method is a fallback for local runs without Docker.
        """
        try:
            def _convert_ejson(obj):
                """Recursively convert EJSON dicts to native BSON types."""
                if isinstance(obj, dict):
                    if '$oid' in obj:
                        return ObjectId(obj['$oid'])
                    if '$date' in obj:
                        date_str = obj['$date']
                        return datetime.fromisoformat(date_str.replace('Z', '+00:00')).replace(tzinfo=None)
                    return {k: _convert_ejson(v) for k, v in obj.items()}
                if isinstance(obj, list):
                    return [_convert_ejson(i) for i in obj]
                return obj

            for collection_name, filename in [
                ('pazienti', 'pazienti.json'),
                ('schede_valutazione', 'schede_valutazione.json'),
                ('diario_trattamenti', 'diario_trattamenti.json'),
                ('eventi_calendario', 'eventi_calendario.json'),
            ]:
                raw = self.load_json_data(f'{data_dir}/{filename}')
                converted = _convert_ejson(raw)
                self.db[collection_name].delete_many({})
                self.db[collection_name].insert_many(converted)
                print(f"Imported {len(converted)} records into {collection_name}")

            self._create_indexes()
            return True
        except Exception as e:
            print(f"Error importing data: {e}")
            return False

    def _create_indexes(self):
        """Create database indexes for performance"""
        self.db.pazienti.create_index('professionista_principale')
        self.db.schede_valutazione.create_index('paziente_id')
        self.db.schede_valutazione.create_index('data')
        self.db.schede_valutazione.create_index([('paziente_id', 1), ('data', -1)])
        self.db.diario_trattamenti.create_index('paziente_id')
        self.db.diario_trattamenti.create_index('data')
        self.db.diario_trattamenti.create_index([('paziente_id', 1), ('data', -1)])
        self.db.eventi_calendario.create_index('paziente_id')
        self.db.eventi_calendario.create_index('data')
        self.db.eventi_calendario.create_index('stato')
        self.db.eventi_calendario.create_index([('paziente_id', 1), ('data', -1)])
        print("Database indexes created")

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _to_object_id(self, value) -> Optional[ObjectId]:
        """
        Convert any representation of a Mongo ID to ObjectId.
        Handles: ObjectId, str, {'$oid': '...'} (raw EJSON not yet converted).
        Returns None if conversion fails.
        """
        if value is None:
            return None
        if isinstance(value, ObjectId):
            return value
        if isinstance(value, str):
            try:
                return ObjectId(value)
            except Exception:
                return None
        if isinstance(value, dict) and '$oid' in value:
            try:
                return ObjectId(value['$oid'])
            except Exception:
                return None
        return None

    def _normalize_id(self, oid) -> Optional[str]:
        """Normalize any ID representation to a plain string."""
        obj = self._to_object_id(oid)
        return str(obj) if obj else None

    def _serialize_doc(self, doc: Dict) -> Dict:
        """Convert ObjectId / datetime fields in a document to JSON-serialisable types."""
        if doc is None:
            return None
        result = {}
        for k, v in doc.items():
            if isinstance(v, ObjectId):
                result[k] = str(v)
            elif isinstance(v, datetime):
                result[k] = v.isoformat()
            elif isinstance(v, dict):
                result[k] = self._serialize_doc(v)
            elif isinstance(v, list):
                result[k] = [self._serialize_doc(i) if isinstance(i, dict) else i for i in v]
            else:
                result[k] = v
        return result

    # -------------------------------------------------------------------------
    # Core query methods
    # -------------------------------------------------------------------------

    def get_patients_with_lombare_pain(self, reference_date: datetime = None) -> Set[str]:
        """
        Find patients who have had lombare pain mentioned in clinical documents
        within the last 3 months relative to reference_date.
        """
        if reference_date is None:
            reference_date = datetime(2024, 12, 31)

        three_months_ago = reference_date - timedelta(days=90)
        patients_with_lombare: Set[str] = set()

        for collection_name in ('schede_valutazione', 'diario_trattamenti'):
            docs = self.db[collection_name].find({
                'data': {'$gte': three_months_ago, '$lte': reference_date}
            })
            for doc in docs:
                text = doc.get('descrizione', '')
                if self._ai_extractor.extract_conditions(text)['has_lombare_pain']:
                    pid = self._normalize_id(doc.get('paziente_id'))
                    if pid:
                        patients_with_lombare.add(pid)

        return patients_with_lombare

    def get_patients_with_miglioramento(self, reference_date: datetime = None) -> Set[str]:
        """
        Find patients who have shown improvement (and NOT worsening) in
        clinical documents within the last 3 months.
        """
        if reference_date is None:
            reference_date = datetime(2024, 12, 31)

        three_months_ago = reference_date - timedelta(days=90)
        patients_with_improvement: Set[str] = set()

        for collection_name in ('schede_valutazione', 'diario_trattamenti'):
            docs = self.db[collection_name].find({
                'data': {'$gte': three_months_ago, '$lte': reference_date}
            })
            for doc in docs:
                text = doc.get('descrizione', '')
                extraction = self._ai_extractor.extract_conditions(text)
                if extraction['has_miglioramento'] and not extraction['has_peggioramento']:
                    pid = self._normalize_id(doc.get('paziente_id'))
                    if pid:
                        patients_with_improvement.add(pid)

        return patients_with_improvement

    def get_patients_with_no_show(self) -> Set[str]:
        """
        Find patients whose most recent appointment has stato == 'no_show'.

        FIX: instead of iterating every patient and doing N separate queries,
        we fetch all events sorted by date and determine the last event per
        patient in a single pass — much more efficient.
        """
        # Fetch all events newest-first
        all_events = list(self.db.eventi_calendario.find(
            {},
            {'paziente_id': 1, 'stato': 1, 'data': 1}
        ).sort('data', -1))

        seen: Set[str] = set()
        no_show_patients: Set[str] = set()

        for event in all_events:
            pid = self._normalize_id(event.get('paziente_id'))
            if pid is None or pid in seen:
                continue
            seen.add(pid)
            if event.get('stato') == 'no_show':
                no_show_patients.add(pid)

        return no_show_patients

    # -------------------------------------------------------------------------
    # Patient detail helpers
    # -------------------------------------------------------------------------

    def get_patient_details(self, paziente_id: str) -> Optional[Dict]:
        """Get full patient details"""
        oid = self._to_object_id(paziente_id)
        if oid is None:
            return None
        patient = self.db.pazienti.find_one({'_id': oid})
        return self._serialize_doc(patient) if patient else None

    def get_patient_evaluations(self, paziente_id: str, limit: int = 5) -> List[Dict]:
        """Get recent evaluations for a patient"""
        oid = self._to_object_id(paziente_id)
        if oid is None:
            return []
        docs = list(self.db.schede_valutazione.find(
            {'paziente_id': oid}
        ).sort('data', -1).limit(limit))
        result = []
        for doc in docs:
            serialized = self._serialize_doc(doc)
            serialized['conditions'] = self._ai_extractor.extract_conditions(doc.get('descrizione', ''))
            result.append(serialized)
        return result

    def get_patient_appointments(self, paziente_id: str, limit: int = 5) -> List[Dict]:
        """Get recent appointments for a patient"""
        oid = self._to_object_id(paziente_id)
        if oid is None:
            return []
        docs = list(self.db.eventi_calendario.find(
            {'paziente_id': oid}
        ).sort('data', -1).limit(limit))
        return [self._serialize_doc(d) for d in docs]

    def get_patient_treatments(self, paziente_id: str, limit: int = 5) -> List[Dict]:
        """Get recent treatments for a patient"""
        oid = self._to_object_id(paziente_id)
        if oid is None:
            return []
        docs = list(self.db.diario_trattamenti.find(
            {'paziente_id': oid}
        ).sort('data', -1).limit(limit))
        return [self._serialize_doc(d) for d in docs]

    # -------------------------------------------------------------------------
    # Main complex query
    # -------------------------------------------------------------------------

    def execute_complex_query(self,
                              has_condition: bool = True,
                              condition_type: str = 'lombare',
                              has_improvement: bool = True,
                              timeframe_months: int = 3,
                              has_no_show: bool = True,
                              reference_date: datetime = None) -> List[Dict]:
        """
        Execute the complex query with specified parameters.

        Finds patients who:
        1. Have the specified condition (default: lombare pain)
        2. Have shown improvement in the specified timeframe
        3. Have had a no_show as their most recent appointment
        """
        if reference_date is None:
            reference_date = datetime(2024, 12, 31)

        # Step 1 — patients with the condition
        if has_condition:
            patients_with_condition = self.get_patients_with_lombare_pain(reference_date)
        else:
            patients_with_condition = {
                self._normalize_id(p['_id'])
                for p in self.db.pazienti.find({'stato': 'attivo'}, {'_id': 1})
            }

        # Step 2 — patients with improvement
        patients_with_improvement = (
            self.get_patients_with_miglioramento(reference_date)
            if has_improvement
            else patients_with_condition
        )

        # Step 3 — patients whose last appointment was a no_show
        patients_no_show = self.get_patients_with_no_show() if has_no_show else set()

        # Step 4 — intersection
        result_ids = patients_with_condition & patients_with_improvement
        if has_no_show:
            result_ids &= patients_no_show

        # Step 5 — enrich results
        results = []
        for paziente_id in result_ids:
            patient_data = self.get_patient_details(paziente_id)
            if not patient_data:
                continue

            evaluations = self.get_patient_evaluations(paziente_id)
            appointments = self.get_patient_appointments(paziente_id)
            treatments = self.get_patient_treatments(paziente_id)

            # Find the most recent no_show appointment
            last_no_show = next(
                (a for a in appointments if a.get('stato') == 'no_show'),
                None
            )

            results.append({
                'paziente': patient_data,
                'ultima_valutazione': evaluations[0] if evaluations else None,
                'storico_valutazioni': evaluations,
                'ultimo_appuntamento': appointments[0] if appointments else None,
                'no_show': last_no_show,
                'storico_appuntamenti': appointments,
                'storico_trattamenti': treatments,
            })

        # Sort by no_show date descending
        results.sort(
            key=lambda x: x['no_show']['data'] if x.get('no_show') and x['no_show'].get('data') else '',
            reverse=True
        )

        return results

    # -------------------------------------------------------------------------
    # New helpers for list-all and name-search intents
    # -------------------------------------------------------------------------

    def get_all_patients(self) -> List[Dict]:
        """Return all patients with basic enrichment (last appointment, last evaluation)."""
        patients = list(self.db.pazienti.find({}))
        results = []
        for p in patients:
            pid = self._normalize_id(p['_id'])
            appointments = self.get_patient_appointments(pid, limit=1)
            evaluations  = self.get_patient_evaluations(pid, limit=1)
            last_no_show = next((a for a in self.get_patient_appointments(pid, limit=5)
                                 if a.get('stato') == 'no_show'), None)
            results.append({
                'paziente':           self._serialize_doc(p),
                'ultima_valutazione': evaluations[0]  if evaluations  else None,
                'ultimo_appuntamento': appointments[0] if appointments else None,
                'no_show':            last_no_show,
                'storico_valutazioni':  [],
                'storico_appuntamenti': [],
                'storico_trattamenti':  [],
            })
        return results

    def get_patients_by_name(self, name: str) -> List[Dict]:
        """
        Search patients by partial name match (case-insensitive).
        Splits the input and matches any token against nome or cognome.
        """
        if not name:
            return []

        tokens = [t for t in name.split() if len(t) > 1]
        if not tokens:
            return []

        or_clauses = []
        for token in tokens:
            regex = {'$regex': token, '$options': 'i'}
            or_clauses.append({'nome':    regex})
            or_clauses.append({'cognome': regex})

        patients = list(self.db.pazienti.find({'$or': or_clauses}))
        results = []
        for p in patients:
            pid = self._normalize_id(p['_id'])
            appointments = self.get_patient_appointments(pid, limit=5)
            evaluations  = self.get_patient_evaluations(pid, limit=5)
            treatments   = self.get_patient_treatments(pid, limit=5)
            last_no_show = next((a for a in appointments if a.get('stato') == 'no_show'), None)
            results.append({
                'paziente':            self._serialize_doc(p),
                'ultima_valutazione':  evaluations[0]  if evaluations  else None,
                'ultimo_appuntamento': appointments[0] if appointments else None,
                'no_show':             last_no_show,
                'storico_valutazioni':  evaluations,
                'storico_appuntamenti': appointments,
                'storico_trattamenti':  treatments,
            })
        return results