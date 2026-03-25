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

    def __init__(self, mongo_uri: str = None, db_name: str = None):
        self.config = Config()
        self.mongo_uri = mongo_uri or self.config.MONGODB_URI
        self.db_name   = db_name   or self.config.MONGODB_DB
        self._client   = None
        self._db       = None
        self._ai_extractor = AIDataExtractor()

    # -------------------------------------------------------------------------
    # Connection
    # -------------------------------------------------------------------------

    def connect(self):
        if self._client is None:
            self._client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            self._db = self._client[self.db_name]
        return self._db

    def close(self):
        if self._client:
            self._client.close()
            self._client = None
            self._db = None

    @property
    def db(self):
        if self._db is None:
            self.connect()
        return self._db

    # -------------------------------------------------------------------------
    # Data import
    # -------------------------------------------------------------------------

    def load_json_data(self, filepath: str) -> List[Dict]:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def import_sample_data(self, data_dir: str = 'data'):
        try:
            def _convert_ejson(obj):
                if isinstance(obj, dict):
                    if '$oid' in obj:
                        return ObjectId(obj['$oid'])
                    if '$date' in obj:
                        return datetime.fromisoformat(
                            obj['$date'].replace('Z', '+00:00')
                        ).replace(tzinfo=None)
                    return {k: _convert_ejson(v) for k, v in obj.items()}
                if isinstance(obj, list):
                    return [_convert_ejson(i) for i in obj]
                return obj

            for collection_name, filename in [
                ('pazienti',            'pazienti.json'),
                ('schede_valutazione',  'schede_valutazione.json'),
                ('diario_trattamenti',  'diario_trattamenti.json'),
                ('eventi_calendario',   'eventi_calendario.json'),
            ]:
                raw       = self.load_json_data(f'{data_dir}/{filename}')
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
        obj = self._to_object_id(oid)
        return str(obj) if obj else None

    def _serialize_doc(self, doc: Dict) -> Dict:
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
    # Core filter methods
    # -------------------------------------------------------------------------

    def get_patients_with_lombare_pain(self, reference_date: datetime = None) -> Set[str]:
        """
        Returns patients who had lombare pain mentioned in ANY clinical record
        within the timeframe.

        Uses historical=True so that resolved cases (e.g. Marco Colombo, Roberto
        Romano) are still included — the query asks "has had lombare pain", not
        "currently has lombare pain".
        """
        if reference_date is None:
            reference_date = datetime(2024, 12, 31)
        three_months_ago = reference_date - timedelta(days=90)

        result: Set[str] = set()

        for collection in ('schede_valutazione', 'diario_trattamenti'):
            docs = self.db[collection].find({
                'data': {'$gte': three_months_ago, '$lte': reference_date}
            })
            for doc in docs:
                extraction = self._ai_extractor.extract_conditions(
                    doc.get('descrizione', ''), historical=True
                )
                if extraction['has_lombare_pain']:
                    pid = self._normalize_id(doc.get('paziente_id'))
                    if pid:
                        result.add(pid)

        return result

    def get_patients_with_miglioramento(self, reference_date: datetime = None) -> Set[str]:
        """
        Returns patients who showed improvement in ANY clinical record within
        the timeframe.

        Scans all records (not just the last one) because a patient may show
        improvement in an intermediate visit even if the latest note is a
        discharge note — both are valid signals of improvement.
        """
        if reference_date is None:
            reference_date = datetime(2024, 12, 31)
        three_months_ago = reference_date - timedelta(days=90)

        result: Set[str] = set()

        for collection in ('schede_valutazione', 'diario_trattamenti'):
            docs = self.db[collection].find({
                'data': {'$gte': three_months_ago, '$lte': reference_date}
            })
            for doc in docs:
                extraction = self._ai_extractor.extract_conditions(
                    doc.get('descrizione', '')
                )
                if extraction['has_miglioramento'] and not extraction['has_peggioramento']:
                    pid = self._normalize_id(doc.get('paziente_id'))
                    if pid:
                        result.add(pid)

        return result

    def get_patients_with_worsening(self, reference_date: datetime = None) -> Set[str]:
        """
        Returns patients whose MOST RECENT evaluation shows worsening.

        Uses only the last record because we want current clinical state,
        not historical episodes.
        """
        result: Set[str] = set()
        patients = self.db.pazienti.find({})

        for p in patients:
            pid = self._normalize_id(p['_id'])
            oid = self._to_object_id(pid)

            last_eval = self.db.schede_valutazione.find_one(
                {'paziente_id': oid},
                sort=[('data', -1)]
            )
            if not last_eval:
                continue

            extraction = self._ai_extractor.extract_conditions(
                last_eval.get('descrizione', '')
            )
            if extraction['has_peggioramento']:
                result.add(pid)

        return result

    def get_patients_with_no_show(self) -> Set[str]:
        """
        Returns patients whose most recent appointment has stato == 'no_show'.
        Single-pass over all events sorted newest-first.
        """
        all_events = list(self.db.eventi_calendario.find(
            {},
            {'paziente_id': 1, 'stato': 1, 'data': 1}
        ).sort('data', -1))

        seen: Set[str] = set()
        result: Set[str] = set()

        for event in all_events:
            pid = self._normalize_id(event.get('paziente_id'))
            if pid is None or pid in seen:
                continue
            seen.add(pid)
            if event.get('stato') == 'no_show':
                result.add(pid)

        return result

    def get_patients_with_attended(self) -> Set[str]:
        """
        Returns patients whose most recent appointment has stato == 'completato'.
        """
        all_events = list(self.db.eventi_calendario.find(
            {},
            {'paziente_id': 1, 'stato': 1, 'data': 1}
        ).sort('data', -1))

        seen: Set[str] = set()
        result: Set[str] = set()

        for event in all_events:
            pid = self._normalize_id(event.get('paziente_id'))
            if pid is None or pid in seen:
                continue
            seen.add(pid)
            if event.get('stato') == 'completato':
                result.add(pid)

        return result

    # -------------------------------------------------------------------------
    # Patient detail helpers
    # -------------------------------------------------------------------------

    def get_patient_details(self, paziente_id: str) -> Optional[Dict]:
        oid = self._to_object_id(paziente_id)
        if oid is None:
            return None
        patient = self.db.pazienti.find_one({'_id': oid})
        return self._serialize_doc(patient) if patient else None

    def get_patient_evaluations(self, paziente_id: str, limit: int = 5) -> List[Dict]:
        oid = self._to_object_id(paziente_id)
        if oid is None:
            return []
        docs = list(self.db.schede_valutazione.find(
            {'paziente_id': oid}
        ).sort('data', -1).limit(limit))
        result = []
        for doc in docs:
            serialized = self._serialize_doc(doc)
            serialized['conditions'] = self._ai_extractor.extract_conditions(
                doc.get('descrizione', '')
            )
            result.append(serialized)
        return result

    def get_patient_appointments(self, paziente_id: str, limit: int = 5) -> List[Dict]:
        oid = self._to_object_id(paziente_id)
        if oid is None:
            return []
        docs = list(self.db.eventi_calendario.find(
            {'paziente_id': oid}
        ).sort('data', -1).limit(limit))
        return [self._serialize_doc(d) for d in docs]

    def get_patient_treatments(self, paziente_id: str, limit: int = 5) -> List[Dict]:
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
                              has_condition:    bool = False,
                              condition_type:   str  = 'lombare',
                              has_improvement:  bool = False,
                              has_worsening:    bool = False,
                              timeframe_months: int  = 3,
                              has_no_show:      bool = False,
                              has_attended:     bool = False,
                              reference_date:   datetime = None) -> List[Dict]:
        """
        AND-intersection of all active filters.
        If no filters are active, returns all patients.
        """
        if reference_date is None:
            reference_date = datetime(2024, 12, 31)

        candidate_sets = []

        if has_condition:
            candidate_sets.append(self.get_patients_with_lombare_pain(reference_date))
        if has_improvement:
            candidate_sets.append(self.get_patients_with_miglioramento(reference_date))
        if has_worsening:
            candidate_sets.append(self.get_patients_with_worsening(reference_date))
        if has_no_show:
            candidate_sets.append(self.get_patients_with_no_show())
        if has_attended:
            candidate_sets.append(self.get_patients_with_attended())

        if not candidate_sets:
            return self.get_all_patients()

        result_ids = candidate_sets[0]
        for s in candidate_sets[1:]:
            result_ids = result_ids & s

        results = []
        for paziente_id in result_ids:
            patient_data = self.get_patient_details(paziente_id)
            if not patient_data:
                continue

            evaluations  = self.get_patient_evaluations(paziente_id)
            appointments = self.get_patient_appointments(paziente_id)
            treatments   = self.get_patient_treatments(paziente_id)

            last_no_show = next(
                (a for a in appointments if a.get('stato') == 'no_show'), None
            )

            results.append({
                'paziente':             patient_data,
                'ultima_valutazione':   evaluations[0]  if evaluations  else None,
                'storico_valutazioni':  evaluations,
                'ultimo_appuntamento':  appointments[0] if appointments else None,
                'no_show':              last_no_show,
                'storico_appuntamenti': appointments,
                'storico_trattamenti':  treatments,
                'has_lombare':          has_condition,
                'has_improvement':      has_improvement,
            })

        results.sort(
            key=lambda x: (
                x['no_show']['data']
                if x.get('no_show') and x['no_show'].get('data')
                else ''
            ),
            reverse=True,
        )

        return results

    # -------------------------------------------------------------------------
    # List-all and name-search helpers
    # -------------------------------------------------------------------------

    def get_all_patients(self) -> List[Dict]:
        patients = list(self.db.pazienti.find({}))
        results = []
        for p in patients:
            pid          = self._normalize_id(p['_id'])
            appointments = self.get_patient_appointments(pid, limit=5)
            evaluations  = self.get_patient_evaluations(pid, limit=1)
            last_no_show = next(
                (a for a in appointments if a.get('stato') == 'no_show'), None
            )
            results.append({
                'paziente':             self._serialize_doc(p),
                'ultima_valutazione':   evaluations[0] if evaluations else None,
                'ultimo_appuntamento':  appointments[0] if appointments else None,
                'no_show':              last_no_show,
                'storico_valutazioni':  [],
                'storico_appuntamenti': [],
                'storico_trattamenti':  [],
            })
        return results

    def get_patients_by_name(self, name: str) -> List[Dict]:
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
        results  = []
        for p in patients:
            pid          = self._normalize_id(p['_id'])
            appointments = self.get_patient_appointments(pid, limit=5)
            evaluations  = self.get_patient_evaluations(pid, limit=5)
            treatments   = self.get_patient_treatments(pid, limit=5)
            last_no_show = next(
                (a for a in appointments if a.get('stato') == 'no_show'), None
            )
            results.append({
                'paziente':             self._serialize_doc(p),
                'ultima_valutazione':   evaluations[0] if evaluations else None,
                'ultimo_appuntamento':  appointments[0] if appointments else None,
                'no_show':              last_no_show,
                'storico_valutazioni':  evaluations,
                'storico_appuntamenti': appointments,
                'storico_trattamenti':  treatments,
            })
        return results