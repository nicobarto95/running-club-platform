# Runner Coaching Platform - MVP

Piattaforma minimalista per gestire richieste di partecipazione alla running community di Dublino.

## 🏗️ Architettura

- **Backend**: FastAPI (Python 3.11)
- **Database**: Google Firestore
- **Hosting**: Google Cloud Run
- **Infrastructure**: Terraform
- **CI/CD**: GitHub Actions

## 💰 Costi Stimati

~€10-15/mese con:
- Cloud Run (pay-per-use)
- Firestore (free tier fino a 1GB)
- Artifact Registry
- Cloud Logging

## 🚀 Setup Iniziale

### 1. Prerequisiti

```bash
# Installa Google Cloud CLI
# https://cloud.google.com/sdk/docs/install

# Installa Terraform
# https://developer.hashicorp.com/terraform/downloads

# Verifica installazioni
gcloud --version
terraform --version
```

### 2. Crea Progetto GCP

```bash
# Login
gcloud auth login
gcloud auth application-default login

# Crea progetto (sostituisci PROJECT_ID con un nome univoco)
export PROJECT_ID="runner-platform-dublin"
gcloud projects create $PROJECT_ID --name="Runner Platform"

# Imposta come progetto corrente
gcloud config set project $PROJECT_ID

# Abilita billing (vai su console.cloud.google.com e collega carta)

# Abilita API necessarie
gcloud services enable run.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 3. Configura Firestore

```bash
# Crea database Firestore in modalità Native
gcloud firestore databases create --location=europe-west1 --type=firestore-native
```

### 4. Deploy Infrastruttura

```bash
cd terraform

# Copia file variabili
cp terraform.tfvars.example terraform.tfvars

# Modifica terraform.tfvars con il tuo PROJECT_ID
nano terraform.tfvars

# Inizializza Terraform
terraform init

# Verifica piano
terraform plan

# Applica
terraform apply
```

### 5. Setup GitHub Actions

```bash
# Crea Service Account per GitHub Actions
gcloud iam service-accounts create github-actions \
    --display-name="GitHub Actions"

# Assegna permessi
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"

# Genera chiave JSON
gcloud iam service-accounts keys create key.json \
    --iam-account=github-actions@${PROJECT_ID}.iam.gserviceaccount.com

# Il contenuto di key.json va in GitHub Secrets come GCP_SA_KEY
cat key.json
```

### 6. Configura GitHub Secrets

Nel tuo repo GitHub, vai su Settings > Secrets and variables > Actions:

- `GCP_PROJECT_ID`: il tuo PROJECT_ID
- `GCP_SA_KEY`: contenuto completo di key.json

### 7. Deploy Locale (Test)

```bash
cd app

# Crea virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Installa dipendenze
pip install -r requirements.txt

# Imposta variabili ambiente
export GCP_PROJECT_ID=$PROJECT_ID
export ENVIRONMENT=development

# Avvia app
uvicorn main:app --reload --port 8000

# Testa
curl http://localhost:8000/health
```

## 📝 Endpoints API

- `GET /` - Health check
- `GET /health` - Status dettagliato
- `POST /api/applications` - Invia richiesta partecipazione
- `GET /api/applications` - Lista richieste (admin)
- `GET /api/applications/{id}` - Dettaglio singola richiesta

## 🧪 Test dell'API

```bash
# Invia richiesta di esempio
curl -X POST http://localhost:8000/api/applications \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mario Rossi",
    "email": "mario@example.com",
    "age": 35,
    "level": "intermediate",
    "goal": "half_marathon",
    "availability": ["monday_evening", "saturday_morning"],
    "dublin_zone": "southside",
    "experience": "Ho corso 2 anni fa con un gruppo",
    "current_pace": "5:30"
  }'
```

## 🌐 Frontend

Il frontend è in `frontend/index.html` - un semplice form HTML/CSS/JS.

Per servire localmente:
```bash
cd frontend
python3 -m http.server 8080
# Vai su http://localhost:8080
```

## 📊 Monitoring

```bash
# Visualizza logs
gcloud run services logs read runner-platform-api \
    --region=europe-west1 \
    --limit=50

# Metriche
gcloud monitoring dashboards list
```

## 🔄 Workflow di Sviluppo

1. Crea feature branch: `git checkout -b feature/nome-feature`
2. Sviluppa e testa localmente
3. Commit e push: `git push origin feature/nome-feature`
4. GitHub Actions fa il deploy automatico al merge su `main`

## 🛠️ Comandi Utili

```bash
# Rebuild e redeploy manuale
gcloud run deploy runner-platform-api \
    --source ./app \
    --region=europe-west1 \
    --allow-unauthenticated

# Distruggi tutto (attenzione!)
cd terraform && terraform destroy
```

## 📚 Prossimi Step

- [ ] Aggiungi autenticazione admin
- [ ] Dashboard web per visualizzare richieste
- [ ] Email notifications (SendGrid free tier)
- [ ] Export CSV richieste
- [ ] Integrazione con Strava (opzionale)

## 🏃‍♂️ Community Running a Dublino

Considera integrazioni future con:
- Parkrun Ireland
- Dublin Running Meetup groups
- Strava Dublin clubs

## 📄 Licenza

MIT