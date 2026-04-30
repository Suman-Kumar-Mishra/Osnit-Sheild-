# OSNIT Shield

### Open Source Intelligence Threat Monitoring System

OSNIT Shield is an AI-powered **Open Source Intelligence (OSINT) monitoring platform** designed to detect emerging security threats by analyzing publicly available data from multiple sources such as news platforms, social media feeds, and global event databases.

The system ingests real-time data, enriches it using Natural Language Processing (NLP), performs risk scoring, and exposes intelligence analytics through a FastAPI backend and an interactive dashboard.

---

# 🚀 Key Features

## Multi-Source Intelligence Ingestion

The system continuously collects data from multiple open sources:

* Global News APIs
* GDELT Event Database
* Telegram Public Channels
* YouTube RSS Feeds
* Regional News Sources

This ensures broad situational awareness across geopolitical regions.

---

## AI Intelligence Processing Engine

Collected data is processed using NLP techniques to extract structured intelligence:

* Incident Type Classification
* Severity Detection
* Risk Score Calculation
* Country & State Identification
* Keyword Extraction
* AI Generated Summary
* Confidence Scoring

Each record becomes enriched intelligence instead of raw text.

---

## Threat Analytics Engine

The intelligence layer exposes analytics such as:

* Incident distribution by severity
* Country-wise threat patterns
* State-level intelligence summaries
* Incident type analysis
* Risk distribution across regions
* Time-based incident trends

---

## Alert Detection System

The system generates alerts when abnormal activity is detected.

Examples include:

* Keyword spike alerts
* Escalation signals
* High-risk intelligence clusters

Alerts are stored and exposed through the intelligence API.

---

## Intelligence API

The platform exposes a comprehensive API using **FastAPI**.

Example endpoints:

```
/intelligence/summary
/intelligence/countries
/intelligence/states
/intelligence/incident-types
/intelligence/trend
/intelligence/alerts
```

Drill-down endpoints allow deeper analysis:

```
/intelligence/country/{country}
/intelligence/state/{state}
/intelligence/incident-type/{type}
```

---

# 🧠 System Architecture

```
Data Sources
     │
     ▼
Ingestion Layer
     │
     ▼
Raw Intelligence Database
     │
     ▼
AI Processing Engine
     │
     ▼
Enriched Intelligence Records
     │
     ▼
Alert Engine
     │
     ▼
Analytics API (FastAPI)
     │
     ▼
Dashboard Visualization
```

---

# 📂 Project Structure

```
osnit-shield/
│
├── backend/
│   ├── main.py
│   ├── routes/
│   │   ├── intelligence.py
│   │   ├── incidents.py
│   │   └── operations.py
│
├── ingestion/
│   ├── collectors/
│   │   ├── news.py
│   │   ├── gdelt.py
│   │   ├── telegram.py
│   │   └── youtube.py
│   ├── runner.py
│   └── utils.py
│
├── ai_engine/
│   ├── pipeline.py
│   ├── classifier.py
│   ├── geo_detection.py
│   ├── risk_scoring.py
│   └── summarizer.py
│
├── database.py
├── models.py
├── requirements.txt
└── README.md
```

---

# 🗄 Database Schema

## Raw OSINT Records

```
raw_osint
```

Stores all collected intelligence with AI enrichment fields.

Fields include:

* source
* content
* country
* state
* incident_type
* severity
* risk_score
* confidence
* summary
* keyword_vector
* processed

---

## Alerts Table

```
alerts
```

Stores generated intelligence alerts.

Fields include:

* keyword
* state
* country
* spike_ratio
* threat_probability
* confidence
* source_count
* alert_type
* created_at

---

## Ingestion Logs

```
ingestion_logs
```

Tracks ingestion runs and errors.

---

# ⚙️ Installation

Clone the repository:

```
git clone https://github.com/yourusername/osnit-shield.git
cd osnit-shield
```

Create virtual environment:

```
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```
pip install -r requirements.txt
```

---

# 🐘 Database Setup

Start PostgreSQL:

```
docker run -d \
-p 5433:5432 \
--name osnit-postgres \
-e POSTGRES_USER=osnit_user \
-e POSTGRES_PASSWORD=osnit_pass \
-e POSTGRES_DB=osnit_db \
postgres:15
```

---

# ▶ Running the Backend

Start FastAPI server:

```
uvicorn backend.main:app --reload
```

Server will run on:

```
http://127.0.0.1:8000
```

API docs:

```
http://127.0.0.1:8000/docs
```

---

# 📊 Example Intelligence Output

```
{
  "incident_type": "cyber_attack",
  "state": "Maharashtra",
  "country": "India",
  "severity": "high",
  "risk_score": 0.82,
  "confidence": 0.76,
  "summary": "A surge in reported cyberattacks targeting financial institutions in Maharashtra indicates increasing cyber threat activity in the region."
}
```

---

# 🔮 Future Improvements

Planned enhancements include:

* Social media disinformation detection
* Keyword spike detection engine
* Threat escalation prediction models
* Geospatial threat heatmaps
* LLM-based intelligence summarization
* Real-time intelligence dashboard

---

# 👨‍💻 Author
Suman Kumar Mishra

---

# 📜 License

This project is licensed under the MIT License.
