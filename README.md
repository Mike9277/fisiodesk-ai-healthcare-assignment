# FisioDesk AI Query System

## 🎯 Sistema di Query Intelligenti con AI per Professionisti Sanitari

Sistema MVP che permette ai professionisti sanitari di effettuare query complesse sui dati clinici usando linguaggio naturale e AI.

### Query Target Implementata

> *"Mostra pazienti con dolore lombare che hanno mostrato miglioramento negli ultimi 3 mesi ma hanno saltato l'ultimo appuntamento"*

---

## 📁 Struttura del Progetto

```
fisiodesk-ai-healthcare-assignment/
├── app.py                    # Flask API principale
├── config.py                 # Configurazione del sistema
├── requirements.txt           # Dipendenze Python
├── Dockerfile                # Container per l'API
├── docker-compose.yml        # Stack completo (MongoDB + API + UI)
├── index.html                # Frontend web per test
├── ARCHITECTURE.md           # Diagramma architettura completo
├── data/                     # Dataset di test
│   ├── pazienti.json
│   ├── schede_valutazione.json
│   ├── diario_trattamenti.json
│   └── eventi_calendario.json
└── services/
    ├── __init__.py
    ├── ai_service.py         # AI per estrazione condizioni cliniche
    └── data_service.py        # Servizio per query MongoDB
```

---

## 🚀 Quick Start

### Opzione 1: Script di Avvio Automatico (Windows) ⭐

```bash
# Doppio click su start.bat oppure da terminale:
start.bat

# Lo script offre:
# [1] Avvia tutto
# [2] Riavvia da zero
# [3] Ferma tutto
# [4] Verifica status
# [5] Apri interfacce web
```

### Opzione 2: Docker Compose Manuale

```bash
# Clona il repository
git clone <repo-url>
cd fisiodesk-ai-healthcare-assignment

# Avvia tutti i servizi
docker-compose up -d

# Verifica che tutti i servizi siano attivi
docker-compose ps

# I servizi saranno disponibili su:
# - API Flask: http://localhost:5000
# - MongoDB Express UI: http://localhost:8081
# - MongoDB: localhost:27017
```

### Opzione 3: Esecuzione Locale

```bash
# Crea un virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oppure
venv\Scripts\activate  # Windows

# Installa dipendenze
pip install -r requirements.txt

# Avvia MongoDB localmente (o usa la stringa di connessione esistente)
# Avvia l'API
python app.py
```

---

## 🧪 Testare la Query Target

### Via API

```bash
# Esegue la query target
curl -X GET http://localhost:5000/api/v1/demo/target-query

# Oppure con una query personalizzata
curl -X POST http://localhost:5000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "mostra pazienti con dolore lombare che hanno mostrato miglioramento", "reference_date": "2024-12-31"}'
```

### Via Frontend Web

Apri `index.html` nel browser (o vai a http://localhost:5000 quando l'API è in esecuzione).

### Via MongoDB Express

Vai a http://localhost:8081 per esplorare il database.

---

## 📊 Risultati Attesi dalla Query Target

### ✅ Casi Positivi (4 pazienti)

| Paziente | Condizione | Miglioramento | No Show |
|----------|------------|---------------|---------|
| Mario Rossi | Dolore lombare (8/10 → 3/10) | ✓ | 20/12/2024 |
| Laura Bianchi | Rachialgia lombare | ✓ | 22/12/2024 |
| Roberto Romano | Low back pain (VAS 9/10 → risolto) | ✓ | 30/12/2024 |
| Marco Colombo | Lombalgia acuta | ✓ | 31/12/2024 |

### ❌ Casi Negativi (esclusi dalla query)

| Paziente | Motivo Esclusione |
|----------|-------------------|
| Anna Ferrari | Lombalgia MA no_show senza miglioramento |
| Giuseppe Verdi | Solo cervicalgia, niente dolore lombare |
| Francesca Ricci | Solo spalla congelata |

---

## 🔌 API Endpoints

### `GET /api/v1/health`
Verifica lo stato del sistema.

```json
{
  "status": "ok",
  "mongodb": "ok",
  "timestamp": "2024-12-31T10:00:00"
}
```

### `POST /api/v1/query`
Esegue una query in linguaggio naturale.

**Request:**
```json
{
  "query": "mostra pazienti con dolore lombare...",
  "reference_date": "2024-12-31"
}
```

**Response:**
```json
{
  "success": true,
  "query": "mostra pazienti con dolore lombare...",
  "analysis": {
    "intents": ["list_patients", "filter_by_condition"],
    "timeframe": "3_mesi",
    "condition_type": "dolore_lombare"
  },
  "results": [...],
  "metadata": {
    "total_results": 4,
    "execution_time_seconds": 0.123
  }
}
```

### `GET /api/v1/demo/target-query`
Esegue direttamente la query target predefinita.

### `GET /api/v1/patients/<id>/summary`
Restituisce un riepilogo completo del paziente.

### `POST /api/v1/analyze`
Analizza un testo clinico per estrarre condizioni.

---

## ⚙️ Configurazione

Le variabili d'ambiente possono essere impostate nel file `.env`:

```env
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=false
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=fisiodesk
AI_PROVIDER=mock  # 'openai' per usare GPT
OPENAI_API_KEY=your-api-key
TIMEFRAME_REFERENCE_DATE=2024-12-31
```

---

## 🏗️ Architettura del Sistema

### Componenti Principali

1. **Flask API Layer**
   - Gestisce le richieste HTTP
   - Analizza le query in linguaggio naturale
   - Formatta e restituisce i risultati

2. **AI Service Layer**
   - `AIDataExtractor`: Estrae condizioni cliniche dai testi usando pattern matching
   - `MockAIAnalyzer`: Simula risposte AI (MVP)
   - Supporto per OpenAI GPT (produzione)

3. **Data Service Layer**
   - Interroga MongoDB
   - Aggrega dati da più collections
   - Gestisce la logica di query complesse

4. **MongoDB**
   - 4 collections: pazienti, schede_valutazione, diario_trattamenti, eventi_calendario
   - Indici ottimizzati per performance

### Data Flow

```
Query Naturale → Intent Analysis → Set Intersection → Risultati Arricchiti
     ↓                  ↓                   ↓
  AI/Mock → 3 Parallel Queries → Aggregation → Response
```

---

## 📈 Trade-offs Principali

### 1. Performance vs Accuratezza
- **Decisione**: Pre-calcolare le estrazioni AI per query comuni
- **Trade-off**: Leggera attesa per nuovi dati vs risposta <2s
- **Mitigazione**: Job in background aggiorna i dati entro 5 minuti

### 2. Costo vs Funzionalità
- **Decisione**: Usa pattern matching prima di chiamare AI
- **Trade-off**: Meno preciso su query complesse vs riduzione costi 10x
- **Mitigazione**: Indica chiaramente quando l'AI fornirebbe risultati migliori

### 3. Semplicità vs Flessibilità
- **Decisione**: Supporto iniziale solo per terminologia medica italiana
- **Trade-off**: Limitato supporto multi-lingua vs MVP più veloce
- **Mitigazione**: Facile da estendere con nuovi language pack

---

## 🔮 Roadmap Future

- [ ] Integrazione OpenAI GPT per analisi più sofisticata
- [ ] Supporto multi-lingua (inglese, spagnolo)
- [ ] Pre-processing batch con Celery
- [ ] Redis caching per query frequenti
- [ ] Vector search con MongoDB Atlas
- [ ] Dashboard React/Angular per il frontend

---

## 📝 Licenza

MIT License - Dreambuilders Srl

---

## 👤 Autore

Sviluppato come assignment tecnico per Dreambuilders Srl - Healthcare Management Systems
