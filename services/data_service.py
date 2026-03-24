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
        """
        try:
            # Load and import patients
            pazienti = self.load_json_data(f'{data_dir}/pazienti.json')
            self.db.pazienti.delete_many({})
            self.db.pazienti.insert_many(pazienti)
            print(f"Imported {len(pazienti)} patients")
            
            # Load and import schede_valutazione
            schede = self.load_json_data(f'{data_dir}/schede_valutazione.json')
            self.db.schede_valutazione.delete_many({})
            self.db.schede_valutazione.insert_many(schede)
            print(f"Imported {len(schede)} evaluation forms")
            
            # Load and import diario_trattamenti
            trattamenti = self.load_json_data(f'{data_dir}/diario_trattamenti.json')
            self.db.diario_trattamenti.delete_many({})
            self.db.diario_trattamenti.insert_many(trattamenti)
            print(f"Imported {len(trattamenti)} treatments")
            
            # Load and import eventi_calendario
            eventi = self.load_json_data(f'{data_dir}/eventi_calendario.json')
            self.db.eventi_calendario.delete_many({})
            self.db.eventi_calendario.insert_many(eventi)
            print(f"Imported {len(eventi)} calendar events")
            
            # Create indexes
            self._create_indexes()
            
            return True
        except Exception as e:
            print(f"Error importing data: {e}")
            return False
    
    def _create_indexes(self):
        """Create database indexes for performance"""
        # pazienti indexes
        self.db.pazienti.create_index('professionista_principale')
        
        # schede_valutazione indexes
        self.db.schede_valutazione.create_index('paziente_id')
        self.db.schede_valutazione.create_index('data')
        self.db.schede_valutazione.create_index([('paziente_id', 1), ('data', -1)])
        
        # diario_trattamenti indexes
        self.db.diario_trattamenti.create_index('paziente_id')
        self.db.diario_trattamenti.create_index('data')
        self.db.diario_trattamenti.create_index([('paziente_id', 1), ('data', -1)])
        
        # eventi_calendario indexes
        self.db.eventi_calendario.create_index('paziente_id')
        self.db.eventi_calendario.create_index('data')
        self.db.eventi_calendario.create_index('stato')
        self.db.eventi_calendario.create_index([('paziente_id', 1), ('data', -1)])
        
        print("Database indexes created")
    
    def get_patients_with_lombare_pain(self, reference_date: datetime = None) -> Set[str]:
        """
        Find patients who have had lombare pain mentioned in clinical documents.
        """
        if reference_date is None:
            reference_date = datetime(2024, 12, 31)
        
        three_months_ago = reference_date - timedelta(days=90)
        
        patients_with_lombare = set()
        
        # Search in schede_valutazione
        schede = self.db.schede_valutazione.find({
            'data': {'$gte': three_months_ago, '$lte': reference_date}
        })
        
        for scheda in schede:
            text = scheda.get('descrizione', '')
            extraction = self._ai_extractor.extract_conditions(text)
            
            if extraction['has_lombare_pain']:
                paziente_id = self._normalize_id(scheda.get('paziente_id'))
                if paziente_id:
                    patients_with_lombare.add(paziente_id)
        
        # Search in diario_trattamenti
        trattamenti = self.db.diario_trattamenti.find({
            'data': {'$gte': three_months_ago, '$lte': reference_date}
        })
        
        for trattamento in trattamenti:
            text = trattamento.get('descrizione', '')
            extraction = self._ai_extractor.extract_conditions(text)
            
            if extraction['has_lombare_pain']:
                paziente_id = self._normalize_id(trattamento.get('paziente_id'))
                if paziente_id:
                    patients_with_lombare.add(paziente_id)
        
        return patients_with_lombare
    
    def get_patients_with_miglioramento(self, reference_date: datetime = None) -> Set[str]:
        """
        Find patients who have shown improvement in recent evaluations.
        """
        if reference_date is None:
            reference_date = datetime(2024, 12, 31)
        
        three_months_ago = reference_date - timedelta(days=90)
        
        patients_with_improvement = set()
        
        # Search in schede_valutazione
        schede = self.db.schede_valutazione.find({
            'data': {'$gte': three_months_ago, '$lte': reference_date}
        })
        
        for scheda in schede:
            text = scheda.get('descrizione', '')
            extraction = self._ai_extractor.extract_conditions(text)
            
            # Has improvement AND NOT worsening
            if extraction['has_miglioramento'] and not extraction['has_peggioramento']:
                paziente_id = self._normalize_id(scheda.get('paziente_id'))
                if paziente_id:
                    patients_with_improvement.add(paziente_id)
        
        # Also check diario_trattamenti
        trattamenti = self.db.diario_trattamenti.find({
            'data': {'$gte': three_months_ago, '$lte': reference_date}
        })
        
        for trattamento in trattamenti:
            text = trattamento.get('descrizione', '')
            extraction = self._ai_extractor.extract_conditions(text)
            
            if extraction['has_miglioramento'] and not extraction['has_peggioramento']:
                paziente_id = self._normalize_id(trattamento.get('paziente_id'))
                if paziente_id:
                    patients_with_improvement.add(paziente_id)
        
        return patients_with_improvement
    
    def get_patients_with_no_show(self) -> Set[str]:
        """
        Find patients who have had a no_show as their last appointment.
        """
        patients_no_show = set()
        
        # Get all patients
        patients = self.db.pazienti.find({}, {'_id': 1})
        patient_ids = [p['_id'] for p in patients]
        
        for paziente_id in patient_ids:
            # Get last appointment for this patient
            last_event = self.db.eventi_calendario.find_one(
                {'paziente_id': paziente_id},
                sort=[('data', -1)]
            )
            
            if last_event and last_event.get('stato') == 'no_show':
                normalized_id = self._normalize_id(paziente_id)
                if normalized_id:
                    patients_no_show.add(normalized_id)
        
        return patients_no_show
    
    def _normalize_id(self, oid) -> Optional[str]:
        """Normalize ObjectId to string"""
        if oid is None:
            return None
        if isinstance(oid, str):
            return oid
        if isinstance(oid, ObjectId):
            return str(oid)
        if isinstance(oid, dict) and '$oid' in oid:
            return oid['$oid']
        return str(oid)
    
    def get_patient_details(self, paziente_id: str) -> Optional[Dict]:
        """Get full patient details"""
        try:
            patient = self.db.pazienti.find_one({'_id': ObjectId(paziente_id)})
            if patient:
                patient['_id'] = str(patient['_id'])
                if patient.get('professionista_principale'):
                    patient['professionista_principale'] = self._normalize_id(patient['professionista_principale'])
            return patient
        except:
            return None
    
    def get_patient_evaluations(self, paziente_id: str, limit: int = 5) -> List[Dict]:
        """Get recent evaluations for a patient"""
        try:
            evaluations = list(self.db.schede_valutazione.find(
                {'paziente_id': ObjectId(paziente_id)}
            ).sort('data', -1).limit(limit))
            
            for eval in evaluations:
                eval['_id'] = str(eval['_id'])
                eval['paziente_id'] = self._normalize_id(eval.get('paziente_id'))
                eval['professionista_id'] = self._normalize_id(eval.get('professionista_id'))
                
                # Extract conditions from description
                text = eval.get('descrizione', '')
                eval['conditions'] = self._ai_extractor.extract_conditions(text)
            
            return evaluations
        except:
            return []
    
    def get_patient_appointments(self, paziente_id: str, limit: int = 5) -> List[Dict]:
        """Get recent appointments for a patient"""
        try:
            appointments = list(self.db.eventi_calendario.find(
                {'paziente_id': ObjectId(paziente_id)}
            ).sort('data', -1).limit(limit))
            
            for appt in appointments:
                appt['_id'] = str(appt['_id'])
                appt['paziente_id'] = self._normalize_id(appt.get('paziente_id'))
                appt['professionista_id'] = self._normalize_id(appt.get('professionista_id'))
            
            return appointments
        except:
            return []
    
    def get_patient_treatments(self, paziente_id: str, limit: int = 5) -> List[Dict]:
        """Get recent treatments for a patient"""
        try:
            treatments = list(self.db.diario_trattamenti.find(
                {'paziente_id': ObjectId(paziente_id)}
            ).sort('data', -1).limit(limit))
            
            for treatment in treatments:
                treatment['_id'] = str(treatment['_id'])
                treatment['paziente_id'] = self._normalize_id(treatment.get('paziente_id'))
                treatment['professionista_id'] = self._normalize_id(treatment.get('professionista_id'))
            
            return treatments
        except:
            return []
    
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
        3. Have had a no_show as their last appointment (if required)
        """
        if reference_date is None:
            reference_date = datetime(2024, 12, 31)
        
        # Step 1: Get patients with the condition
        if has_condition:
            patients_with_condition = self.get_patients_with_lombare_pain(reference_date)
        else:
            # Get all active patients
            all_patients = self.db.pazienti.find({'stato': 'attivo'})
            patients_with_condition = {self._normalize_id(p['_id']) for p in all_patients}
        
        # Step 2: Get patients with improvement
        if has_improvement:
            patients_with_improvement = self.get_patients_with_miglioramento(reference_date)
        else:
            patients_with_improvement = patients_with_condition
        
        # Step 3: Get patients with no_show
        if has_no_show:
            patients_no_show = self.get_patients_with_no_show()
        else:
            patients_no_show = set()
        
        # Step 4: Intersection
        result_ids = patients_with_condition & patients_with_improvement
        if has_no_show:
            result_ids = result_ids & patients_no_show
        
        # Step 5: Enrich results
        results = []
        for paziente_id in result_ids:
            patient_data = self.get_patient_details(paziente_id)
            if patient_data:
                evaluations = self.get_patient_evaluations(paziente_id)
                appointments = self.get_patient_appointments(paziente_id)
                treatments = self.get_patient_treatments(paziente_id)
                
                # Find the no_show event
                last_no_show = None
                for appt in appointments:
                    if appt.get('stato') == 'no_show':
                        last_no_show = appt
                        break
                
                results.append({
                    'paziente': patient_data,
                    'ultima_valutazione': evaluations[0] if evaluations else None,
                    'storico_valutazioni': evaluations,
                    'ultimo_appuntamento': appointments[0] if appointments else None,
                    'no_show': last_no_show,
                    'storico_appuntamenti': appointments,
                    'storico_trattamenti': treatments
                })
        
        # Sort by most recent no_show
        results.sort(
            key=lambda x: x.get('no_show', {}).get('data', datetime.min) if x.get('no_show') else datetime.min,
            reverse=True
        )
        
        return results
