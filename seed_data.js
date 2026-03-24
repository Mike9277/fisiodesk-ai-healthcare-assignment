// Script to import data into MongoDB
// Run with: mongosh mongodb://host:27017/fisiodesk seed_data.js

print("Starting data import...");

// Load JSON data manually
var pazientiData = [
  {"_id": {"$oid": "507f1f77bcf86cd799439011"}, "nome": "Mario", "cognome": "Rossi", "eta": 54, "telefono": "+39 333 123 4567", "email": "mario.rossi@email.com", "professionista_principale": {"$oid": "507f1f77bcf86cd799439021"}, "data_registrazione": {"$date": "2024-06-15T10:00:00Z"}, "stato": "attivo"},
  {"_id": {"$oid": "507f1f77bcf86cd799439012"}, "nome": "Laura", "cognome": "Bianchi", "eta": 42, "telefono": "+39 335 987 6543", "email": "laura.bianchi@email.com", "professionista_principale": {"$oid": "507f1f77bcf86cd799439021"}, "data_registrazione": {"$date": "2024-07-20T14:30:00Z"}, "stato": "attivo"},
  {"_id": {"$oid": "507f1f77bcf86cd799439013"}, "nome": "Giuseppe", "cognome": "Verdi", "eta": 61, "telefono": "+39 338 456 7890", "email": "giuseppe.verdi@email.com", "professionista_principale": {"$oid": "507f1f77bcf86cd799439021"}, "data_registrazione": {"$date": "2024-05-10T09:15:00Z"}, "stato": "attivo"},
  {"_id": {"$oid": "507f1f77bcf86cd799439014"}, "nome": "Anna", "cognome": "Ferrari", "eta": 38, "telefono": "+39 340 111 2222", "email": "anna.ferrari@email.com", "professionista_principale": {"$oid": "507f1f77bcf86cd799439022"}, "data_registrazione": {"$date": "2024-08-22T11:20:00Z"}, "stato": "attivo"},
  {"_id": {"$oid": "507f1f77bcf86cd799439015"}, "nome": "Roberto", "cognome": "Romano", "eta": 49, "telefono": "+39 342 333 4444", "email": "r.romano@email.com", "professionista_principale": {"$oid": "507f1f77bcf86cd799439021"}, "data_registrazione": {"$date": "2024-09-05T15:45:00Z"}, "stato": "attivo"},
  {"_id": {"$oid": "507f1f77bcf86cd799439016"}, "nome": "Francesca", "cognome": "Ricci", "eta": 67, "telefono": "+39 345 555 6666", "email": "f.ricci@email.com", "professionista_principale": {"$oid": "507f1f77bcf86cd799439022"}, "data_registrazione": {"$date": "2024-04-12T08:30:00Z"}, "stato": "sospeso"},
  {"_id": {"$oid": "507f1f77bcf86cd799439017"}, "nome": "Marco", "cognome": "Colombo", "eta": 55, "telefono": "+39 347 777 8888", "email": "marco.colombo@email.com", "professionista_principale": {"$oid": "507f1f77bcf86cd799439023"}, "data_registrazione": {"$date": "2024-03-18T10:00:00Z"}, "stato": "attivo"}
];

db.pazienti.deleteMany({});
db.pazienti.insertMany(pazientiData);
print("Imported " + pazientiData.length + " patients");

// Load schede_valutazione
var schedeData = [
  {"_id": {"$oid": "607f1f77bcf86cd799439101"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439011"}, "data": {"$date": "2024-11-15T09:00:00Z"}, "descrizione": "Paziente riferisce miglioramento significativo del dolore lombare. Scala del dolore da 8/10 a 3/10. Mobilità migliorata, riesce a camminare per 30 minuti senza difficoltà.", "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}},
  {"_id": {"$oid": "607f1f77bcf86cd799439102"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439011"}, "data": {"$date": "2024-12-01T09:00:00Z"}, "descrizione": "Ottimi progressi nella gestione della lombalgia. Il paziente riferisce di riuscire a svolgere le attività quotidiane con minimo fastidio. Dolore residuo solo in flessione completa.", "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}},
  {"_id": {"$oid": "607f1f77bcf86cd799439103"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439012"}, "data": {"$date": "2024-10-20T14:00:00Z"}, "descrizione": "Prima valutazione: paziente lamenta forte dolore alla bassa schiena da circa 3 mesi. Rigidità mattutina presente.", "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}},
  {"_id": {"$oid": "607f1f77bcf86cd799439104"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439012"}, "data": {"$date": "2024-11-10T14:00:00Z"}, "descrizione": "Paziente mostra segni di recupero. La rachialgia lombare è diminuita sensibilmente. Riferisce che il fastidio alla zona lombare è più sopportabile.", "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}},
  {"_id": {"$oid": "607f1f77bcf86cd799439105"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439012"}, "data": {"$date": "2024-12-05T14:00:00Z"}, "descrizione": "Netto miglioramento del quadro clinico. La signora riesce ora a piegarsi senza dolore acuto alla schiena.", "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}},
  {"_id": {"$oid": "607f1f77bcf86cd799439106"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439013"}, "data": {"$date": "2024-10-15T09:30:00Z"}, "descrizione": "Prima valutazione. Paziente presenta cervicalgia acuta con limitazione nei movimenti del collo. Dolore 7/10. Prescritta terapia antinfiammatoria.", "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}},
  {"_id": {"$oid": "607f1f77bcf86cd799439107"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439013"}, "data": {"$date": "2024-11-20T09:30:00Z"}, "descrizione": "Miglioramento della cervicalgia. Il paziente riferisce riduzione del dolore cervicale da 7/10 a 4/10. Mobilità del collo migliorata del 60%.", "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}},
  {"_id": {"$oid": "607f1f77bcf86cd799439108"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439014"}, "data": {"$date": "2024-09-10T11:00:00Z"}, "descrizione": "Paziente con mal di schiena cronico da 6 mesi. Riferisce forte dolore nella zona lombare, soprattutto al mattino. Difficoltà nelle attività quotidiane.", "professionista_id": {"$oid": "507f1f77bcf86cd799439022"}},
  {"_id": {"$oid": "607f1f77bcf86cd799439109"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439014"}, "data": {"$date": "2024-10-25T11:00:00Z"}, "descrizione": "Situazione stazionaria. La lombalgia persiste con intensità invariata. Paziente scoraggiata, consigliato approccio multidisciplinare.", "professionista_id": {"$oid": "507f1f77bcf86cd799439022"}},
  {"_id": {"$oid": "607f1f77bcf86cd799439110"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439014"}, "data": {"$date": "2024-12-10T11:00:00Z"}, "descrizione": "Lieve peggioramento. Il mal di schiena si è esteso anche alla gamba destra. Sospetta sciatalgia. Richiesta RMN urgente.", "professionista_id": {"$oid": "507f1f77bcf86cd799439022"}},
  {"_id": {"$oid": "607f1f77bcf86cd799439111"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439015"}, "data": {"$date": "2024-09-15T16:00:00Z"}, "descrizione": "Valutazione iniziale: forte low back pain con irradiazione glutea bilaterale. Scala VAS 9/10. Paziente molto sofferente, difficoltà a stare seduto.", "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}},
  {"_id": {"$oid": "607f1f77bcf86cd799439112"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439015"}, "data": {"$date": "2024-10-30T16:00:00Z"}, "descrizione": "Ottimi progressi! Il paziente sta molto meglio. Dolore lombare ridotto a 3/10. Riesce a lavorare senza problemi. Continua con esercizi a casa.", "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}},
  {"_id": {"$oid": "607f1f77bcf86cd799439113"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439015"}, "data": {"$date": "2024-12-15T16:00:00Z"}, "descrizione": "Situazione eccellente. Il signor Romano riferisce completa risoluzione della lombalgia. Può fare sport senza limitazioni. Consigliato mantenimento.", "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}},
  {"_id": {"$oid": "607f1f77bcf86cd799439114"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439016"}, "data": {"$date": "2024-06-20T08:45:00Z"}, "descrizione": "Spalla congelata destra. Paziente con grave limitazione articolare, impossibilità ad alzare il braccio oltre i 45°. Dolore notturno importante.", "professionista_id": {"$oid": "507f1f77bcf86cd799439022"}},
  {"_id": {"$oid": "607f1f77bcf86cd799439115"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439017"}, "data": {"$date": "2024-09-25T10:15:00Z"}, "descrizione": "Prima visita per rachialgia lombare acuta insorta dopo sforzo fisico. Paziente riferisce 'colpo della strega' mentre sollevava un peso. VAS 8/10.", "professionista_id": {"$oid": "507f1f77bcf86cd799439023"}},
  {"_id": {"$oid": "607f1f77bcf86cd799439116"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439017"}, "data": {"$date": "2024-11-10T10:15:00Z"}, "descrizione": "Buon recupero dalla lombalgia acuta. Il dolore alla bassa schiena è molto diminuito (VAS 2/10). Ripresa graduale attività lavorativa.", "professionista_id": {"$oid": "507f1f77bcf86cd799439023"}},
  {"_id": {"$oid": "607f1f77bcf86cd799439117"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439017"}, "data": {"$date": "2024-12-18T10:15:00Z"}, "descrizione": "Controllo finale. Il signor Colombo sta benissimo, nessun dolore residuo alla zona lombare. Ha ripreso tutte le attività senza problemi.", "professionista_id": {"$oid": "507f1f77bcf86cd799439023"}}
];

db.schede_valutazione.deleteMany({});
db.schede_valutazione.insertMany(schedeData);
print("Imported " + schedeData.length + " evaluation forms");

// Load diario_trattamenti
var trattamentiData = [
  {"_id": {"$oid": "707f1f77bcf86cd799439201"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439011"}, "data": {"$date": "2024-11-15T09:30:00Z"}, "descrizione": "Seduta completata con successo. Eseguita mobilizzazione lombare e TENS. Paziente risponde bene al trattamento, riferisce sollievo immediato.", "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}},
  {"_id": {"$oid": "707f1f77bcf86cd799439202"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439011"}, "data": {"$date": "2024-12-01T09:30:00Z"}, "descrizione": "Applicata terapia manuale su zona lombare. Il mal di schiena è decisamente diminuito durante la seduta.", "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}},
  {"_id": {"$oid": "707f1f77bcf86cd799439203"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439012"}, "data": {"$date": "2024-11-10T14:30:00Z"}, "descrizione": "Trattamento focalizzato su rachide lombare. Buona risposta alla terapia.", "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}},
  {"_id": {"$oid": "707f1f77bcf86cd799439204"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439013"}, "data": {"$date": "2024-10-15T09:45:00Z"}, "descrizione": "Prima seduta per cervicalgia. Applicata terapia manuale cervicale e TENS. Paziente teso ma collaborativo.", "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}},
  {"_id": {"$oid": "707f1f77bcf86cd799439205"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439013"}, "data": {"$date": "2024-11-20T09:45:00Z"}, "descrizione": "Prosegue trattamento cervicale. Mobilizzazione passiva e attiva. Il paziente riferisce netto miglioramento della sintomatologia.", "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}},
  {"_id": {"$oid": "707f1f77bcf86cd799439206"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439014"}, "data": {"$date": "2024-09-10T11:30:00Z"}, "descrizione": "Iniziato ciclo di terapie per mal di schiena cronico. Applicata tecarterapia sulla zona lombare. Paziente molto dolorante durante il trattamento.", "professionista_id": {"$oid": "507f1f77bcf86cd799439022"}},
  {"_id": {"$oid": "707f1f77bcf86cd799439207"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439014"}, "data": {"$date": "2024-10-25T11:30:00Z"}, "descrizione": "Seduta difficile. La paziente non risponde bene alla terapia. Dolore lombare persistente. Modificato approccio terapeutico.", "professionista_id": {"$oid": "507f1f77bcf86cd799439022"}},
  {"_id": {"$oid": "707f1f77bcf86cd799439208"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439014"}, "data": {"$date": "2024-12-10T11:30:00Z"}, "descrizione": "Situazione complicata. Il mal di schiena non migliora nonostante le terapie. Consigliata valutazione neurologica per sospetta sciatalgia.", "professionista_id": {"$oid": "507f1f77bcf86cd799439022"}},
  {"_id": {"$oid": "707f1f77bcf86cd799439209"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439015"}, "data": {"$date": "2024-09-15T16:30:00Z"}, "descrizione": "Primo trattamento per low back pain acuto. Applicata terapia manuale decontratturante. Il paziente ha trovato immediato sollievo.", "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}},
  {"_id": {"$oid": "707f1f77bcf86cd799439210"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439015"}, "data": {"$date": "2024-10-30T16:30:00Z"}, "descrizione": "Ottima seduta. Eseguiti esercizi di rinforzo del core e stretching lombare. Il paziente sta decisamente meglio, quasi senza dolore.", "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}},
  {"_id": {"$oid": "707f1f77bcf86cd799439211"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439015"}, "data": {"$date": "2024-12-15T16:30:00Z"}, "descrizione": "Ultima seduta del ciclo. Paziente completamente recuperato dalla lombalgia. Forniti esercizi di mantenimento da fare a casa.", "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}},
  {"_id": {"$oid": "707f1f77bcf86cd799439212"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439016"}, "data": {"$date": "2024-06-20T09:00:00Z"}, "descrizione": "Iniziato trattamento per spalla congelata. Mobilizzazione passiva molto limitata. Applicato ultrasuoni e crioterapia.", "professionista_id": {"$oid": "507f1f77bcf86cd799439022"}},
  {"_id": {"$oid": "707f1f77bcf86cd799439213"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439017"}, "data": {"$date": "2024-09-25T10:30:00Z"}, "descrizione": "Trattamento urgente per colpo della strega. Applicata terapia antalgica e decontratturante sulla muscolatura lombare. Paziente trova sollievo.", "professionista_id": {"$oid": "507f1f77bcf86cd799439023"}},
  {"_id": {"$oid": "707f1f77bcf86cd799439214"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439017"}, "data": {"$date": "2024-11-10T10:30:00Z"}, "descrizione": "Prosegue recupero. Eseguita mobilizzazione attiva della colonna lombare. Il dolore alla schiena è quasi completamente risolto.", "professionista_id": {"$oid": "507f1f77bcf86cd799439023"}},
  {"_id": {"$oid": "707f1f77bcf86cd799439215"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439017"}, "data": {"$date": "2024-12-18T10:30:00Z"}, "descrizione": "Seduta conclusiva. Paziente completamente guarito dalla lombalgia. Test funzionali nella norma. Dimesso con consigli posturali.", "professionista_id": {"$oid": "507f1f77bcf86cd799439023"}}
];

db.diario_trattamenti.deleteMany({});
db.diario_trattamenti.insertMany(trattamentiData);
print("Imported " + trattamentiData.length + " treatments");

// Load eventi_calendario
var eventiData = [
  {"_id": {"$oid": "807f1f77bcf86cd799439301"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439011"}, "data": {"$date": "2024-11-15T09:00:00Z"}, "stato": "completato", "durata": 60, "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}, "note": "Controllo mensile"},
  {"_id": {"$oid": "807f1f77bcf86cd799439302"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439011"}, "data": {"$date": "2024-12-01T09:00:00Z"}, "stato": "completato", "durata": 60, "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}, "note": "Follow-up"},
  {"_id": {"$oid": "807f1f77bcf86cd799439303"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439011"}, "data": {"$date": "2024-12-20T09:00:00Z"}, "stato": "no_show", "durata": 60, "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}, "note": "Controllo programmato - Paziente non presentato"},
  {"_id": {"$oid": "807f1f77bcf86cd799439304"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439012"}, "data": {"$date": "2024-12-22T14:00:00Z"}, "stato": "no_show", "durata": 60, "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}, "note": "Follow-up - Non presentato"},
  {"_id": {"$oid": "807f1f77bcf86cd799439305"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439013"}, "data": {"$date": "2024-10-15T09:30:00Z"}, "stato": "completato", "durata": 45, "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}, "note": "Prima valutazione cervicalgia"},
  {"_id": {"$oid": "807f1f77bcf86cd799439306"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439013"}, "data": {"$date": "2024-11-20T09:30:00Z"}, "stato": "completato", "durata": 60, "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}, "note": "Controllo cervicalgia"},
  {"_id": {"$oid": "807f1f77bcf86cd799439307"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439013"}, "data": {"$date": "2024-12-28T09:30:00Z"}, "stato": "prenotato", "durata": 60, "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}, "note": "Controllo finale cervicalgia"},
  {"_id": {"$oid": "807f1f77bcf86cd799439308"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439014"}, "data": {"$date": "2024-09-10T11:00:00Z"}, "stato": "completato", "durata": 60, "professionista_id": {"$oid": "507f1f77bcf86cd799439022"}, "note": "Prima valutazione lombalgia"},
  {"_id": {"$oid": "807f1f77bcf86cd799439309"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439014"}, "data": {"$date": "2024-10-25T11:00:00Z"}, "stato": "completato", "durata": 60, "professionista_id": {"$oid": "507f1f77bcf86cd799439022"}, "note": "Controllo lombalgia - situazione stazionaria"},
  {"_id": {"$oid": "807f1f77bcf86cd799439310"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439014"}, "data": {"$date": "2024-12-10T11:00:00Z"}, "stato": "completato", "durata": 45, "professionista_id": {"$oid": "507f1f77bcf86cd799439022"}, "note": "Valutazione peggioramento - sospetta sciatalgia"},
  {"_id": {"$oid": "807f1f77bcf86cd799439311"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439014"}, "data": {"$date": "2024-12-24T11:00:00Z"}, "stato": "no_show", "durata": 60, "professionista_id": {"$oid": "507f1f77bcf86cd799439022"}, "note": "Follow-up neurologico - Paziente non si è presentato"},
  {"_id": {"$oid": "807f1f77bcf86cd799439312"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439015"}, "data": {"$date": "2024-09-15T16:00:00Z"}, "stato": "completato", "durata": 60, "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}, "note": "Prima valutazione low back pain"},
  {"_id": {"$oid": "807f1f77bcf86cd799439313"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439015"}, "data": {"$date": "2024-10-30T16:00:00Z"}, "stato": "completato", "durata": 60, "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}, "note": "Controllo - ottimi progressi"},
  {"_id": {"$oid": "807f1f77bcf86cd799439314"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439015"}, "data": {"$date": "2024-12-15T16:00:00Z"}, "stato": "completato", "durata": 45, "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}, "note": "Controllo finale - guarigione completa"},
  {"_id": {"$oid": "807f1f77bcf86cd799439315"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439015"}, "data": {"$date": "2024-12-30T16:00:00Z"}, "stato": "no_show", "durata": 30, "professionista_id": {"$oid": "507f1f77bcf86cd799439021"}, "note": "Controllo mantenimento - Non presentato"},
  {"_id": {"$oid": "807f1f77bcf86cd799439316"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439016"}, "data": {"$date": "2024-06-20T08:45:00Z"}, "stato": "completato", "durata": 60, "professionista_id": {"$oid": "507f1f77bcf86cd799439022"}, "note": "Prima valutazione spalla congelata"},
  {"_id": {"$oid": "807f1f77bcf86cd799439317"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439016"}, "data": {"$date": "2024-07-15T08:45:00Z"}, "stato": "cancellato", "durata": 60, "professionista_id": {"$oid": "507f1f77bcf86cd799439022"}, "note": "Cancellato per motivi familiari"},
  {"_id": {"$oid": "807f1f77bcf86cd799439318"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439017"}, "data": {"$date": "2024-09-25T10:15:00Z"}, "stato": "completato", "durata": 45, "professionista_id": {"$oid": "507f1f77bcf86cd799439023"}, "note": "Urgenza - colpo della strega"},
  {"_id": {"$oid": "807f1f77bcf86cd799439319"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439017"}, "data": {"$date": "2024-11-10T10:15:00Z"}, "stato": "completato", "durata": 60, "professionista_id": {"$oid": "507f1f77bcf86cd799439023"}, "note": "Controllo - buon recupero"},
  {"_id": {"$oid": "807f1f77bcf86cd799439320"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439017"}, "data": {"$date": "2024-12-18T10:15:00Z"}, "stato": "completato", "durata": 30, "professionista_id": {"$oid": "507f1f77bcf86cd799439023"}, "note": "Controllo finale - dimissione"},
  {"_id": {"$oid": "807f1f77bcf86cd799439321"}, "paziente_id": {"$oid": "507f1f77bcf86cd799439017"}, "data": {"$date": "2024-12-31T10:15:00Z"}, "stato": "no_show", "durata": 30, "professionista_id": {"$oid": "507f1f77bcf86cd799439023"}, "note": "Controllo preventivo - Non si è presentato"}
];

db.eventi_calendario.deleteMany({});
db.eventi_calendario.insertMany(eventiData);
print("Imported " + eventiData.length + " calendar events");

// Create indexes
db.pazienti.createIndex('professionista_principale');
db.schede_valutazione.createIndex('paziente_id');
db.schede_valutazione.createIndex('data');
db.schede_valutazione.createIndex({'paziente_id': 1, 'data': -1});
db.diario_trattamenti.createIndex('paziente_id');
db.diario_trattamenti.createIndex('data');
db.diario_trattamenti.createIndex({'paziente_id': 1, 'data': -1});
db.eventi_calendario.createIndex('paziente_id');
db.eventi_calendario.createIndex('data');
db.eventi_calendario.createIndex('stato');
db.eventi_calendario.createIndex({'paziente_id': 1, 'data': -1});

print("Database indexes created");
print("Data import completed successfully!");
