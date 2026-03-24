# FisioDesk AI Query System - Architecture

## Overview
Sistema di query intelligenti che permette ai professionisti sanitari di interrogare dati clinici usando linguaggio naturale con supporto AI.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                      React/Angular Frontend                             │ │
│  │  - Natural Language Query Input                                        │ │
│  │  - Results Display with Filters                                         │ │
│  │  - Patient Cards with Clinical Summary                                  │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                      Flask/FastAPI Backend                              │ │
│  │  - Query Parser (Rule-based + AI hybrid)                               │ │
│  │  - Intent Recognition                                                  │ │
│  │  - Response Formatter                                                   │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌─────────────────────────┐ ┌─────────────────┐ ┌─────────────────────────┐
│   AI ANALYSIS LAYER     │ │   DATA LAYER    │ │   CACHE LAYER           │
│  ┌───────────────────┐  │ │ ┌─────────────┐ │ │ ┌───────────────────┐    │
│  │ OpenAI/GPT Mock  │  │ │ │  MongoDB    │ │ │ │   Redis Cache     │    │
│  │ Intent Analysis   │  │ │ │  (Existing) │ │ │ │ - Pre-computed    │    │
│  │ Text Extraction   │  │ │ └─────────────┘ │ │ │   embeddings      │    │
│  └───────────────────┘  │ │                 │ │ │ - Query results   │    │
│  ┌───────────────────┐  │ │ ┌─────────────┐ │ │ └───────────────────┘    │
│  │ Keyword Extractor │  │ │ │ Pre-processed│ │ │                         │
│  │ (Fallback)        │  │ │ │ Collections │ │ │                         │
│  └───────────────────┘  │ │ └─────────────┘ │ │                         │
└─────────────────────────┘ └─────────────────┘ └─────────────────────────┘

                    ┌───────────────────────────────────────┐
                    │         MONGODB COLLECTIONS           │
                    │  ┌──────────┐  ┌───────────────────┐  │
                    │  │pazienti │  │ analisi_cliniche  │  │
                    │  └──────────┘  │ (pre-processed)  │  │
                    │  ┌──────────┐  └───────────────────┘  │
                    │  │ schede_  │  ┌───────────────────┐  │
                    │  │ valutaz. │  │ pazienti_flags   │  │
                    │  └──────────┘  │ (cached results)  │  │
                    │  ┌──────────┐  └───────────────────┘  │
                    │  │ diario_  │                           │
                    │  │ trattam. │                           │
                    │  └──────────┘                           │
                    │  ┌──────────┐                           │
                    │  │ eventi_  │                           │
                    │  │ calendario│                           │
                    │  └──────────┘                           │
                    └───────────────────────────────────────┘
```

## Data Flow for Query Target

```
Query: "Mostra pazienti con dolore lombare che hanno mostrato miglioramento 
        negli ultimi 3 mesi ma hanno saltato l'ultimo appuntamento"

┌─────────────────────────────────────────────────────────────────────────┐
│ 1. QUERY PARSING                                                         │
│    - Extract intent: "find_patients_with_condition_and_compliance"       │
│    - Extract conditions: {condition, timeframe, compliance}             │
│    - Parameters: {condition: "dolore_lombare", timeframe: "3_mesi",     │
│                   last_appointment: "no_show"}                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 2. DATA RETRIEVAL (3 parallel queries)                                   │
│                                                                          
│    A) Get patients with "dolore lombare" in clinical texts               │
│       - Query: schede_valutazione + diario_trattamenti                    │
│       - Pattern matching: "lombare|low back|lombalgia|m.d.s|schiena"     │
│                                                                          
│    B) Get patients with "miglioramento" in recent period                 │
│       - Query: schede_valutazione (last 3 months)                        │
│       - Pattern: "miglior|progress|recup|risolut|sta megli"              │
│                                                                          
│    C) Get patients with no_show as last appointment                       │
│       - Query: eventi_calendario                                         │
│       - Filter: stato="no_show" AND is_last=true                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌─────────────────────────┐ ┌─────────────────┐ ┌─────────────────────────┐
│   PATIENT SET A         │ │  PATIENT SET B  │ │   PATIENT SET C         │
│   (has lombare)         │ │  (has improve.) │ │   (has no_show)         │
│   - Mario Rossi         │ │  - Mario Rossi  │ │   - Mario Rossi         │
│   - Laura Bianchi       │ │  - Laura Bianchi│ │   - Laura Bianchi       │
│   - Roberto Romano      │ │  - Roberto Romano│ │   - Roberto Romano      │
│   - Marco Colombo       │ │  - Marco Colombo│ │   - Marco Colombo       │
│   - Anna Ferrari        │ │                 │ │   - Anna Ferrari        │
└─────────────────────────┘ └─────────────────┘ └─────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 3. SET INTERSECTION                                                      │
│    Result = A ∩ B ∩ C                                                     │
│                                                                          
│    Expected: Mario Rossi, Laura Bianchi, Roberto Romano, Marco Colombo   │
│    Excluded: Anna Ferrari (no miglioramento)                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 4. RESULT ENRICHMENT                                                     │
│    - Fetch full patient details                                           │
│    - Get latest evaluation summaries                                      │
│    - Include appointment history                                           │
│    - Generate clinical context for each patient                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 5. RESPONSE                                                             │
│    Return structured list of patients with:                               │
│    - Patient info (name, age, contact)                                    │
│    - Clinical summary (condition, improvement timeline)                  │
│    - Last appointment status                                              │
│    - Recommended actions                                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Hybrid AI Approach (Cost Optimization)
```
┌─────────────────────────────────────────────────────────────────┐
│                    QUERY CLASSIFICATION                          │
│                                                                  │
│   ┌──────────────┐    ┌──────────────┐    ┌────────────────┐  │
│   │   SIMPLE     │    │   COMPLEX    │    │   AMBIGUOUS    │  │
│   │   QUERIES    │    │   QUERIES    │    │   QUERIES      │  │
│   └──────┬───────┘    └──────┬───────┘    └───────┬────────┘  │
│          │                    │                    │            │
│          ▼                    ▼                    ▼            │
│   ┌──────────────┐    ┌──────────────┐    ┌────────────────┐  │
│   │ Rule-based   │    │ AI-assisted  │    │ AI (OpenAI)    │  │
│   │ Pattern      │    │ + Rules      │    │ Full analysis  │  │
│   │ Matching     │    │ (fallback)   │    │                │  │
│   └──────────────┘    └──────────────┘    └────────────────┘  │
│                                                                  │
│   < 100ms          100-500ms              500ms-2s             │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Pre-processing Strategy (Performance)
- **Batch Processing**: Run AI analysis on new data during off-peak hours
- **Caching**: Store extracted conditions in dedicated collections
- **Incremental Updates**: Only re-process changed documents

### 3. Collections for Pre-processed Data

```javascript
// analisi_cliniche - AI-extracted conditions from texts
{
  _id: ObjectId(),
  paziente_id: ObjectId(),
  source_document_id: ObjectId(),
  source_collection: "schede_valutazione|diario_trattamenti",
  conditions: [
    { type: "dolore_lombare", confidence: 0.95, terms: ["lombalgia"] },
    { type: "miglioramento", confidence: 0.90, terms: ["migliorato"] }
  ],
  extracted_at: ISODate(),
  embedding: [0.1, 0.2, ...] // for semantic search
}

// pazienti_flags - Aggregated patient status
{
  _id: ObjectId(),
  paziente_id: ObjectId(),
  has_lombare_pain: true,
  has_cervical_pain: false,
  has_miglioramento: true,
  last_no_show_date: ISODate(),
  compliance_score: 0.85,
  last_updated: ISODate()
}
```

## Trade-offs

### Performance vs Accuracy
- **Decision**: Pre-compute AI extractions for common queries
- **Trade-off**: Slight delay in new data availability vs <2s query response
- **Mitigation**: Background job updates within 5 minutes

### Cost vs Functionality
- **Decision**: Use keyword-based fallback before AI
- **Trade-off**: Less accurate on complex queries vs 10x cost reduction
- **Mitigation**: Clear indication when AI provides better results

### Simplicity vs Flexibility
- **Decision**: Start with Italian medical terminology only
- **Trade-off**: Limited multi-language support vs faster MVP
- **Mitigation**: Easy to extend with new language packs

## Scalability Considerations

### For 50+ Concurrent Users
1. **Connection Pooling**: MongoDB connection pool size = 100
2. **Query Caching**: Redis with 5-minute TTL for common queries
3. **Async Processing**: Celery for heavy AI tasks
4. **Horizontal Scaling**: Stateless API servers behind load balancer

### For 10K+ Patients
1. **Index Optimization**: Compound indexes on paziente_id + data
2. **Sharding**: Shard by professionista_id for multi-tenant
3. **Archive Strategy**: Move old data to read-only replicas

## API Endpoints

```
POST /api/v1/query
  Body: { query: "mostra pazienti con dolore lombare..." }
  Response: { results: [...], metadata: {execution_time, ai_used} }

GET /api/v1/patients/{id}/summary
  Response: { patient, conditions, appointments, treatments }

POST /api/v1/analyze
  Body: { text: "clinical note..." }
  Response: { conditions: [...], confidence: float }

GET /api/v1/health
  Response: { status: "ok", mongodb: "ok", cache: "ok" }
```
