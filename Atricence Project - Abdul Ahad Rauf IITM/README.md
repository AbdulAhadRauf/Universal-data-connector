# 🔌 Universal Data Connector — Voice-Enabled Business Data Assistant

A production-quality **Universal Data Connector** built with FastAPI, LangGraph, and FastRTC that provides a unified interface for an AI assistant to access CRM, Support Ticket, and Analytics data — through both a REST API and a real-time voice conversation interface powered by Groq.

---
pip install ffmpeg-downloader
ffdl install --add-path
---

## ✨ Key Features

| Feature                        | Description                                                                                       |
|-------------------------------|---------------------------------------------------------------------------------------------------|
| **REST API**                  | FastAPI server with dedicated endpoints for CRM, Support, and Analytics data                      |
| **Voice Interface**           | Real-time voice conversations via FastRTC + Groq (STT → LLM → TTS)                              |
| **LLM Tool Calling**         | LangGraph ReAct agent with 7 data-querying tools callable by natural language                    |
| **Smart Data Filtering**     | Automatic pagination, priority sorting, status filtering, and date-range queries                  |
| **Voice Optimization**       | Concise, spoken-language summaries optimized for TTS playback instead of raw data dumps          |
| **Business Rules Engine**    | Priority ordering, recency sorting, voice-friendly result caps, and contextual metadata          |
| **Data Type Detection**      | Auto-classifies responses as tabular, time-series, hierarchical, or summary                      |
| **Docker Ready**             | Single-command deployment with `docker-compose up`                                                |
| **Tested**                   | pytest suite covering connectors, business rules, and all API endpoints                           |

---
### 🎥 Demo Video
[Click here to watch the demo video](https://drive.google.com/file/d/1wHItFra8Ww5NHv9KZFSXq1YyAZJHrDrk/view?usp=drive_link)


---
## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT INTERFACES                            │
│                                                                     │
│   ┌──────────────────┐         ┌──────────────────────────────┐    │
│   │  REST API Client │         │  Voice Client (Microphone)   │    │
│   │   (curl / Swagger)│         │  via Gradio UI / FastPhone  │    │
│   └────────┬─────────┘         └──────────────┬───────────────┘    │
└────────────┼──────────────────────────────────┼─────────────────────┘
             │                                  │
             ▼                                  ▼
┌────────────────────────┐      ┌──────────────────────────────────┐
│   FastAPI REST Server  │      │   FastRTC Voice Stream Server    │
│   (app/main.py)        │      │   (src/fastrtc_data_stream.py)   │
│                        │      │                                  │
│  • /data/crm           │      │  Audio In → Groq Whisper (STT)  │
│  • /data/support       │      │         → LangGraph Agent        │
│  • /data/analytics     │      │         → Groq Orpheus (TTS)     │
│  • /tools/schema       │      │         → Audio Out              │
│  • /health             │      │                                  │
└────────────┬───────────┘      └───────────────┬──────────────────┘
             │                                  │
             └──────────────┬───────────────────┘
                            │  Both use the same connectors
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     DATA CONNECTOR LAYER                            │
│                                                                     │
│  ┌────────────────┐ ┌──────────────────┐ ┌──────────────────────┐  │
│  │ CRM Connector  │ │ Support Connector│ │ Analytics Connector  │  │
│  │ (crm_connector │ │ (support_        │ │ (analytics_          │  │
│  │  .py)          │ │  connector.py)   │ │  connector.py)       │  │
│  └───────┬────────┘ └────────┬─────────┘ └──────────┬───────────┘  │
│          │                   │                      │              │
│          ▼                   ▼                      ▼              │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    JSON Data Files (data/)                     │ │
│  │  customers.json  │  support_tickets.json  │  analytics.json   │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
Atricence Project/
├── app/                           # FastAPI REST Application
│   ├── main.py                    # Application entry point, CORS, router mounting
│   ├── config.py                  # Pydantic Settings (env vars, model configs)
│   ├── connectors/                # Data source adapters
│   │   ├── base.py                # Abstract BaseConnector interface
│   │   ├── crm_connector.py       # CRM: fetch, search, get_by_id, tool defs
│   │   ├── support_connector.py   # Support tickets: priority/status filters
│   │   └── analytics_connector.py # Analytics: date-range, aggregation, summaries
│   ├── models/                    # Pydantic data models
│   │   ├── common.py              # DataResponse, Metadata, DataType enum
│   │   ├── crm.py                 # Customer model
│   │   ├── support.py             # SupportTicket model
│   │   └── analytics.py           # MetricEntry model
│   ├── routers/                   # API route handlers
│   │   ├── health.py              # GET /health
│   │   └── data.py                # GET /data/crm, /data/support, /data/analytics, /tools/schema
│   ├── services/                  # Business logic
│   │   ├── business_rules.py      # Pagination, priority sort, context strings
│   │   ├── data_identifier.py     # Auto-detects data type (tabular/time-series/etc.)
│   │   ├── llm_service.py         # Collects tool definitions for /tools/schema
│   │   └── voice_optimizer.py     # Generates TTS-friendly summaries & hints
│   └── utils/
│       └── logging.py             # Structured logging setup
├── src/                           # Voice Agent (separate entry point)
│   ├── data_connector_agent.py    # LangGraph ReAct agent — delegates to app/connectors/
│   ├── fastrtc_data_stream.py     # FastRTC WebRTC audio stream (Gradio UI / phone)
│   └── process_groq_tts.py        # Groq TTS WAV → numpy array converter
├── data/                          # Sample JSON datasets
│   ├── customers.json             # 50 CRM customer records
│   ├── support_tickets.json       # 50 support tickets
│   └── analytics.json             # 30 daily_active_users data points
├── tests/                         # pytest test suite
│   ├── test_api.py                # FastAPI endpoint integration tests
│   ├── test_business_rules.py     # Business rules unit tests
│   └── test_connectors.py        # Connector unit tests
├── Dockerfile                     # Python 3.11 slim container
├── docker-compose.yml             # Single-service compose with .env & data volume
├── requirements.txt               # All Python dependencies
├── .env.example                   # Environment variable template
└── README.md                      # This file
```

---

## 🛠️ Tech Stack

| Category             | Technology                                              |
|---------------------|---------------------------------------------------------|
| **Web Framework**   | FastAPI + Uvicorn                                       |
| **Data Validation** | Pydantic v2 + pydantic-settings                        |
| **LLM Framework**   | LangChain + LangGraph (ReAct agent pattern)            |
| **LLM Provider**    | Groq Cloud — Llama 4 Scout 17B (chat completions)      |
| **Speech-to-Text**  | Groq Whisper Large v3 Turbo                            |
| **Text-to-Speech**  | Groq Canopy Labs Orpheus v1 English                    |
| **Real-time Voice** | FastRTC (WebRTC streaming)                             |
| **Logging**         | Loguru (voice agent) + Python stdlib logging (REST API) |
| **Testing**         | pytest + httpx + FastAPI TestClient                    |
| **Containerization**| Docker + Docker Compose                                |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- A [Groq API key](https://console.groq.com/keys) (free tier available)

### 1. Clone & Install

```bash
git clone <repository-url>
cd "Atricence Project"
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and set your GROQ_API_KEY
```

### 3. Run the REST API

```bash
uvicorn app.main:app --reload
```

The Swagger API docs are available at **http://localhost:8000/docs**

### 4. Run the Voice Agent

```bash
cd src
python fastrtc_data_stream.py          # Opens Gradio UI in browser
python fastrtc_data_stream.py --phone  # Gets a temporary phone number
```

### 5. Run with Docker

```bash
docker-compose up --build
```

### 6. Run Tests

```bash
pytest tests/ -v
```
## 📡 API Endpoints

| Method | Endpoint                    | Description                              | Key Parameters                              |
|--------|-----------------------------|------------------------------------------|---------------------------------------------|
| GET    | `/health`                   | Health check                             | —                                           |
| GET    | `/data/crm`                 | Query CRM customers                      | `status`, `search`, `limit`, `page`         |
| GET    | `/data/support`             | Query support tickets                    | `priority`, `status`, `customer_id`, `limit`, `page` |
| GET    | `/data/analytics`           | Query analytics metrics                  | `metric`, `days`, `limit`, `page`           |
| GET    | `/data/analytics/summary`   | Voice-friendly analytics summary         | `metric`, `days`                            |
| GET    | `/data/{source}`            | Generic data query (crm/support/analytics)| `limit`, `page`                            |
| GET    | `/tools/schema`             | All LLM tool/function definitions        | —                                           |

### Example API Calls

```bash
# Get all active customers
curl "http://localhost:8000/data/crm?status=active&limit=5"

# Search customers by name
curl "http://localhost:8000/data/crm?search=Customer%201"

# Get high-priority open tickets
curl "http://localhost:8000/data/support?priority=high&status=open"

# Get analytics summary for last 7 days
curl "http://localhost:8000/data/analytics/summary?days=7"

# Get LLM tool definitions
curl "http://localhost:8000/tools/schema"
```

### Response Format

Every data endpoint returns a unified `DataResponse` envelope:

```json
{
  "data": [ ... ],
  "metadata": {
    "total_results": 50,
    "returned_results": 5,
    "page": 1,
    "total_pages": 10,
    "data_type": "tabular",
    "data_freshness": "Data as of 2026-02-22 15:30 UTC",
    "voice_hint": "There are 45 more results. Ask me to show more if you'd like.",
    "query_context": "Showing 5 of 50 CRM records (filtered by status=active)"
  },
  "voice_summary": "I found 50 customers in the CRM. 24 are active. Showing the first 5."
}
```

---

## 🗣️ Voice Agent — LLM Tools

The LangGraph ReAct agent has **7 tools** available for data querying:

| Tool Name               | Description                                       |
|--------------------------|---------------------------------------------------|
| `search_customers`       | Search CRM customers by name or email             |
| `get_customers`          | List customers, optionally filtered by status     |
| `get_customer_by_id`     | Get a single customer by ID                       |
| `get_support_tickets`    | List tickets with priority/status/customer filters |
| `get_ticket_by_id`       | Get a single ticket by ID                         |
| `get_analytics`          | Fetch analytics data points by metric and date range |
| `get_analytics_summary`  | Get aggregated stats (avg, min, max, trend)       |

The agent is prompted to give **short, conversational, voice-friendly** responses — summarizing rather than dumping raw data.

---

## ⚙️ Configuration

All settings are managed via `.env` (loaded by `pydantic-settings`):

| Variable          | Default                                      | Description                  |
|-------------------|----------------------------------------------|------------------------------|
| `APP_NAME`        | `Universal Data Connector`                   | Application display name     |
| `MAX_RESULTS`     | `10`                                         | Default voice result cap     |
| `LOG_LEVEL`       | `INFO`                                       | Logging verbosity            |
| `GROQ_API_KEY`    | —                                            | Your Groq API key            |
| `GROQ_STT_MODEL`  | `whisper-large-v3-turbo`                    | Speech-to-text model         |
| `GROQ_LLM_MODEL`  | `meta-llama/llama-4-scout-17b-16e-instruct` | Chat LLM model              |
| `GROQ_TTS_MODEL`  | `canopylabs/orpheus-v1-english`             | Text-to-speech model         |
| `GROQ_TTS_VOICE`  | `troy`                                      | TTS voice name               |

---

## 🧪 Testing

The test suite covers three areas:

- **`test_connectors.py`** — Unit tests for CRM, Support, and Analytics connectors (fetch, filter, search, pagination, tool definitions)
- **`test_business_rules.py`** — Tests for voice limits, priority sorting, recency sorting, context strings, freshness labels
- **`test_api.py`** — Integration tests for all REST API endpoints, filter correctness, error handling (404 on unknown source), and tool schema

```bash
pytest tests/ -v
```

---

## 📜 License

This project was built as part of the Atricence assignment.
