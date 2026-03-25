# FisioDesk - MongoDB Development Environment

A Docker-based MongoDB Atlas Local development environment for FisioDesk, a physiotherapy patient management system with built-in vector search capabilities.

## Features

- **MongoDB Atlas Local** with vector search support
- **Pre-loaded sample data** for development
- **MongoDB Express UI** for database visualization
- **Automatic data import** on startup
- **Vector search ready** for AI-powered features

## Prerequisites

- Docker Desktop 4.31+ (macOS/Windows) or Docker Engine 27.0+ (Linux)
- Docker Compose
- 4GB RAM minimum
- Network connection for pulling Docker images

## Quick Start

1. Clone or download repository:
```bash
git clone <repository-url>
cd ai-healthcare-assignment
```

2. Start the services:
```bash
docker-compose up
```

3. Access the services:
- **MongoDB**: `localhost:27017`
- **MongoDB Express UI**: `http://localhost:8081`
- **MongoDB Compass**: `mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000`

4. Verify data import:
```bash
docker logs fisiodesk-mongodb-seed
```

## Project Structure

```
.
├── docker-compose.yml            # Docker services configuration
├── data/                         # Sample data files
│   ├── pazienti.json            # Patient records
│   ├── schede_valutazione.json  # Evaluation forms
│   ├── diario_trattamenti.json  # Treatment logs
│   └── eventi_calendario.json   # Calendar events
├── ai_integration_homework_v2.md # Original assignment document
├── USE_CASES_AND_TESTS.md       # Detailed test cases and use cases
└── README.md                    # This file
```

## Database Collections

### pazienti
Patient records containing:
- Personal information (name, age, contact)
- Assigned physiotherapist
- Registration date and status

### schede_valutazione
Patient evaluation forms for tracking assessments

### diario_trattamenti
Treatment diary entries documenting patient sessions

### eventi_calendario
Calendar events for scheduling appointments

## Vector Search Capabilities

MongoDB Atlas Local includes built-in vector search capabilities for AI-powered features.

## Common Commands

### Start Services
```bash
# Start all services in background
docker-compose up -d

# Start with logs visible
docker-compose up
```

### Stop Services
```bash
# Stop containers
docker-compose down

# Stop and remove volumes (deletes all data)
docker-compose down -v
```

### Database Operations
```bash
# Connect to MongoDB shell
docker exec -it fisiodesk-mongodb mongosh

# Re-import sample data
docker-compose restart mongodb-seed

# View import logs
docker logs fisiodesk-mongodb-seed
```

### Troubleshooting
```bash
# Check service status
docker-compose ps

# View MongoDB logs
docker logs fisiodesk-mongodb

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Development Workflow

1. **Start the environment**: `docker-compose up -d`
2. **Develop your application** connecting to `mongodb://localhost:27017/fisiodesk`
3. **Inspect data** using:
   - MongoDB Express: `http://localhost:8081`
   - MongoDB Compass (client locale): `mongodb://127.0.0.1:27017/?directConnection=true`
4. **Stop when done**: `docker-compose down`

## Support

For issues or questions:
1. Check container logs: `docker logs <container-name>`
2. Verify Docker resources in Docker Desktop settings
3. Ensure ports 27017 and 8081 are not in use

---

## 🎯 Challenge per il Candidato

Questo repository è preparato per testare le tue competenze di **system design** e **AI integration** in un contesto reale di gestionale sanitario.

### Il Compito: Sistema di Query Intelligenti

Devi implementare un sistema che permetta ai professionisti sanitari di fare query complesse sui loro dati usando linguaggio naturale e AI.

**🎯 Query Target da Implementare:**
> *"Mostra pazienti con dolore lombare che hanno mostrato miglioramento negli ultimi 3 mesi ma hanno saltato l'ultimo appuntamento"*

### Perché è Complessa?
- Richiede **AI** per interpretare "miglioramento" dai testi liberi
- Combina **multiple collections** MongoDB (schede_valutazione, eventi_calendario, pazienti)  
- Filtra per **timeframe** specifico
- Correla **compliance paziente** con **progressi clinici**

### Vincoli Operativi
- ⚡ **Performance**: <2 secondi con 50+ professionisti concorrenti
- 💰 **Budget limitato** per API calls AI
- 🔄 **Integrazione** con sistema esistente (SpringBoot + MongoDB)
- 📊 **Accuratezza** per decisioni cliniche

### I Tuoi Deliverable
1. **Diagramma architettura** della tua soluzione
2. **MVP funzionante** con Docker Compose
3. **README** con setup e demo della query target
4. **Documentazione** dei trade-offs principali

### Dati di Test Disponibili
Il database contiene casi realistici che supportano la query target:
Nota: i dati coprono Marzo-Dicembre 2024; per il filtro "ultimi 3 mesi" usa una data di riferimento esplicita (es. 2024-12-31 o la data massima nel dataset).

- **Mario Rossi**: Dolore lombare con miglioramento + no_show (caso positivo ✅)
- **Laura Bianchi**: Dolore lombare con miglioramento + no_show (caso positivo ✅) 
- **Roberto Romano**: Low back pain con miglioramento + no_show (caso positivo ✅)
- **Marco Colombo**: Lombalgia con miglioramento + no_show (caso positivo ✅)
- **Anna Ferrari**: Lombalgia SENZA miglioramento + no_show (caso negativo ❌)
- **Giuseppe Verdi**: Solo cervicalgia, niente lombare (caso negativo ❌)

### Struttura Collections MongoDB

```javascript
// pazienti - 7 pazienti con professionisti diversi
{ _id, nome, cognome, eta, telefono, email, professionista_principale, stato }

// schede_valutazione - 18 valutazioni con variabilità linguistica
{ _id, paziente_id, data, descrizione, professionista_id }
// Contiene: "dolore lombare", "mal di schiena", "lombalgia", "rachialgia", "low back pain"
// E indicatori di miglioramento: "miglioramento", "sta meglio", "progressi", "risoluzione"

// diario_trattamenti - 16 trattamenti con outcome diversi  
{ _id, paziente_id, data, descrizione, professionista_id }

// eventi_calendario - 21 appuntamenti con stati variegati
{ _id, paziente_id, data, stato, durata, professionista_id, note }
// Stati: "completato", "no_show", "cancellato", "prenotato"
```

Per i casi di test dettagliati vedi `USE_CASES_AND_TESTS.md` 🚀
