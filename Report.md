# REPORT — FisioDesk AI Query System

## Contesto

Questo documento descrive l'analisi, la progettazione e l'implementazione del sistema di query intelligenti sviluppato come assignment tecnico per **Dreambuilders Srl**.

---

## 1. Il Problema

L'esercizio richiede di costruire un sistema in grado di rispondere a questa query clinica complessa:

> *"Mostra pazienti con dolore lombare che hanno mostrato miglioramento negli ultimi 3 mesi ma hanno saltato l'ultimo appuntamento"*

La complessità è semantica: i dati clinici rilevanti sono scritti in testo libero, con terminologia variabile e sfumature linguistiche. Nessun campo strutturato nel database contiene "dolore lombare" o "miglioramento" — questi segnali vanno estratti dal testo.

I vincoli operativi sono:

- Risposta in meno di 2 secondi con 50+ utenti concorrenti
- Budget limitato per chiamate AI
- Integrazione con lo stack esistente (SpringBoot + MongoDB)
- Accuratezza sufficiente per decisioni cliniche

---

## 2. Architettura della Soluzione

### 2.1 Stack tecnologico scelto

L'esercizio lascia libertà di scelta sul linguaggio. Si è optato per **Python + Flask** anziché Java/SpringBoot per tre ragioni pratiche:

- Prototipazione più rapida.
- Ecosistema maturo per NLP e pattern matching (regex, futura integrazione LLM)
- Facilità di integrazione con le API di OpenAI/Anthropic

In un contesto di produzione, la logica di estrazione sarebbe esposta come microservizio, consumabile dallo stack SpringBoot esistente via REST.

### 2.2 Componenti principali

```
Flask API (app.py)
    │
    ├── MockAIAnalyzer          → analisi intent della query in linguaggio naturale
    │       (ai_service.py)
    │
    ├── AIDataExtractor         → estrazione segnali clinici dal testo libero
    │       (ai_service.py)
    │
    └── DataService             → query MongoDB + aggregazione risultati
            (data_service.py)
```

### 2.3 Flusso di una query

```
Query naturale
    │
    ▼
analyze_query_intent()          → rileva: lombare? miglioramento? peggioramento? no-show?
    │
    ▼
execute_complex_query()         → costruisce candidate_sets per ogni segnale attivo
    │
    ├── get_patients_with_lombare_pain()     → scansione storica (tutti i record nel timeframe)
    ├── get_patients_with_miglioramento()    → scansione storica (tutti i record nel timeframe)
    ├── get_patients_with_worsening()        → stato attuale (solo ultima valutazione)
    └── get_patients_with_no_show()          → ultimo appuntamento nel calendario
    │
    ▼
Intersezione AND dei set → result_ids
    │
    ▼
Arricchimento per ogni paziente (dettagli, valutazioni, appuntamenti, trattamenti)
    │
    ▼
Risposta JSON formattata
```

---

## 3. Estrazione dei Segnali Clinici

### 3.1 Approccio ibrido

Il sistema usa un approccio **ibrido rule-based + AI-ready**:

- Fase 1 (MVP): pattern matching su dizionari di terminologia medica italiana
- Fase 2 (produzione): le stesse interfacce sono predisposte per chiamate a GPT/Claude

Questo rispetta il vincolo di budget: le query comuni vengono gestite con costo zero, e l'AI reale viene invocata solo per frasi ambigue o non coperte dai pattern.

### 3.2 Pattern di estrazione (config.py)

**Dolore lombare** — termini espliciti con word boundary:
```
dolore lombare, lombalgia, low back pain,
mal di schiena, rachialgia lombare,
dolore alla bassa schiena, colpo della strega
```

**Miglioramento** — termini positivi e di risoluzione:
```
miglioramento, migliorato, progressi, ottimi progressi,
recupero, recuperato, netto miglioramento, situazione eccellente,
completa risoluzione, buon recupero, quasi senza dolore,
sta benissimo, nessun dolore residuo, completamente guarito
```

**Peggioramento** — solo deterioramento esplicito:
```
peggioramento, peggiorato, peggiora,
non migliora, deterioramento, invariato, lieve peggioramento
```

> **Nota:** `situazione stazionaria` e `persistente` sono stati rimossi dai pattern di peggioramento perché causavano falsi positivi — descrivono assenza di miglioramento, non deterioramento attivo.

**Negation patterns** — sopprimono il segnale lombare quando il dolore è assente:
```
nessun dolore, senza dolore, assenza di dolore,
non presenta dolore, dolore risolto/scomparso
```

**Resolution patterns** — paziente dimesso/guarito:
```
controllo finale, fine trattamento, dimesso,
nessun dolore residuo, completa risoluzione, completamente guarito
```

### 3.3 Modalità historical vs. current-state

Il parametro `historical=True` in `extract_conditions()` è la chiave che distingue due domande clinicamente diverse:

| Modalità | Domanda | Usa resolution? |
|---|---|---|
| `historical=False` (default) | Il paziente **ha attualmente** questo problema? | Sì → sopprime lombare se guarito |
| `historical=True` | Il paziente **ha mai avuto** questo problema nel periodo? | No → lombare rimane True anche se poi risolto |

Questa distinzione è necessaria per la query target: Marco Colombo e Roberto Romano sono stati dimessi guariti, ma la query chiede comunque chi "ha avuto dolore lombare e ha migliorato" — non chi lo ha ancora adesso.

---

## 4. Logica delle Query

### 4.1 Scansione storica vs. stato attuale

| Filtro | Strategia | Motivazione |
|---|---|---|
| `has_lombare_pain` | Tutti i record nel timeframe (historical=True) | Il paziente deve aver avuto la condizione, anche se poi guarito |
| `has_miglioramento` | Tutti i record nel timeframe | Un miglioramento intermedio è valido anche se l'ultima nota è di dimissione |
| `has_worsening` | Solo ultima valutazione | Il peggioramento è uno stato corrente, non storico |
| `has_no_show` | Ultimo appuntamento nel calendario | Si vuole sapere se l'ultimo appuntamento è stato saltato |

### 4.2 Intent recognition

`MockAIAnalyzer.analyze_query_intent()` classifica ogni query in uno di tre intent:

- `list_all` — nessun filtro rilevato → restituisce tutti i pazienti
- `find_by_name` — nome proprio rilevato → ricerca per nome/cognome
- `complex_query` — uno o più filtri clinici → pipeline completa

Il rilevamento del nome proprio usa una regex semplice su token con iniziale maiuscola (`[A-Z][a-z]+ [A-Z][a-z]+`), sufficiente per l'italiano.

### 4.3 Intersezione AND

I filtri attivi producono set di ID paziente che vengono intersecati:

```python
result_ids = candidate_sets[0]
for s in candidate_sets[1:]:
    result_ids = result_ids & s
```

Se nessun filtro è attivo, si restituiscono tutti i pazienti (`get_all_patients()`).

---

## 5. Dataset di Test

Il dataset copre marzo–dicembre 2024 con 7 pazienti, 18 schede di valutazione, 16 record di trattamento e 21 eventi calendario. È progettato per testare casi positivi, negativi e casi limite.

### 5.1 Risultati attesi per query

| Query | Pazienti restituiti |
|---|---|
| Mostra tutti | Rossi, Bianchi, Ferrari, Romano, Colombo, Verdi, Ricci |
| Mostra [nome specifico] | Solo il paziente cercato |
| Dolore lombare | Rossi, Bianchi, Ferrari, Romano, Colombo |
| In miglioramento | Rossi, Bianchi, Romano, Colombo, Verdi |
| In peggioramento | Ferrari |
| Hanno saltato l'ultimo appuntamento | Rossi, Bianchi, Ferrari, Romano, Colombo |
| **Query target** (lombare + miglioramento + no-show) | **Rossi, Bianchi, Romano, Colombo** |

### 5.2 Casi negativi e perché sono esclusi

**Anna Ferrari** — ha dolore lombare e no-show, ma la sua ultima valutazione mostra peggioramento. Nessun record nel timeframe contiene segnali di miglioramento → esclusa.

**Giuseppe Verdi** — ha miglioramento, ma la sua condizione è cervicalgia, non lombare. L'ultimo appuntamento è "prenotato" (non no-show) → escluso su entrambi i filtri.

**Francesca Ricci** — spalla congelata, nessun record negli ultimi 3 mesi, ultimo appuntamento "cancellato" → esclusa.

---

## 6. API Endpoints

| Metodo | Endpoint | Descrizione |
|---|---|---|
| GET | `/api/v1/health` | Stato sistema e connessione MongoDB |
| POST | `/api/v1/query` | Query in linguaggio naturale |
| GET | `/api/v1/demo/target-query` | Esegue la query target predefinita |
| GET | `/api/v1/patients` | Lista tutti i pazienti |
| GET | `/api/v1/patients/<id>/summary` | Dettaglio completo paziente |
| POST | `/api/v1/analyze` | Analizza un testo clinico |
| POST | `/api/v1/data/import` | Importa i dati di test |

---

## 7. Setup e Deployment

Il sistema è containerizzato con Docker Compose. Un unico comando avvia l'intero stack:

```bash
docker-compose up -d
```

Servizi avviati:
- **MongoDB 7.0** su porta 27017
- **mongodb-seed** — container one-shot che importa i dati JSON al primo avvio
- **Mongo Express** su porta 8081 — UI per esplorare il database
- **Flask API** su porta 5000 — backend + frontend HTML servito staticamente

---

## 8. Trade-off Principali

### 8.1 Pattern matching vs. LLM

**Scelta:** pattern matching italiano come layer primario, LLM come layer opzionale.

**Pro:** costo zero per query, latenza <50ms per l'estrazione, nessuna dipendenza esterna.

**Contro:** falsi negativi su frasi non coperte dai dizionari, sensibile a formulazioni inattese.

**Mitigazione:** i pattern sono configurabili in `config.py` senza toccare il codice.

### 8.2 Scansione record storici vs. solo ultima valutazione

**Scelta:** lombare e miglioramento scansionano tutti i record nel timeframe; peggioramento usa solo l'ultima valutazione.

**Pro:** corrisponde alla semantica clinica della query target (il paziente "ha avuto" la condizione).

**Contro:** più query MongoDB per paziente, più lento su dataset grandi.

**Mitigazione:** in produzione si risolve con una collection pre-calcolata (`analisi_cliniche`) aggiornata in background al salvataggio di ogni nuova scheda.

### 8.3 Flask vs. SpringBoot

**Scelta:** Flask per l'MVP.

**Pro:** prototipazione rapida, ecosistema Python per NLP.

**Contro:** non integrato nello stack SpringBoot esistente.

**Mitigazione:** il microservizio Python è esposto come API REST; SpringBoot lo chiama via HTTP. In alternativa, la logica di estrazione può essere riscritta in Java usando la stessa logica, mantenendo l'architettura monolitica.

---

## 9. Percorso di Debug

Durante lo sviluppo sono stati identificati e risolti i seguenti problemi:

### 9.1 Pazienti guariti esclusi dalla query target

**Problema:** Marco Colombo e Roberto Romano non comparivano nella query target perché la loro ultima valutazione mostrava la risoluzione del dolore ("controllo finale", "nessun dolore residuo"), facendo sì che `has_lombare_pain` risultasse False.

**Causa:** il sistema analizzava solo l'ultima valutazione per tutti i filtri, confondendo "stato attuale" con "storia clinica nel periodo".

**Fix:** introdotta la modalità `historical=True` in `extract_conditions()`. Per il filtro lombare, la resolution logic non sopprime il segnale — il paziente ha avuto dolore lombare nel periodo, anche se poi guarito.

### 9.2 Filtro peggioramento restituiva tutti i pazienti

**Problema:** la query "mostra pazienti in peggioramento" restituiva tutti i pazienti invece della sola Anna Ferrari.

**Causa:** `app.py` passava valori hardcoded (`has_improvement=True`, `has_no_show=True`) a `execute_complex_query()` ignorando completamente l'output dell'analizzatore di intent. Il flag `has_worsening` non veniva mai passato.

**Fix:** la route `/api/v1/query` ora legge tutti i flag direttamente da `analysis`:
```python
results = data_service.execute_complex_query(
    has_condition   = analysis.get('has_condition', False),
    has_improvement = analysis.get('has_improvement', False),
    has_worsening   = analysis.get('has_worsening', False),
    has_no_show     = analysis.get('has_no_show', False),
    ...
)
```

### 9.3 Falsi positivi nel filtro peggioramento

**Problema:** `situazione stazionaria` e `persistente` nei `WORSENING_PATTERNS` causavano falsi positivi — pazienti in condizione stabile venivano classificati come "in peggioramento".

**Fix:** rimossi entrambi i termini. Descrivono assenza di miglioramento, non deterioramento attivo. Aggiunto invece `lieve peggioramento` come pattern esplicito.

---