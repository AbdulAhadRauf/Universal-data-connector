# Universal Data Connector

A production-ready FastAPI service that provides a unified interface for
accessing multiple data sources (CRM, Support, Analytics) optimized for
LLM function calling and voice-based AI assistants.

------------------------------------------------------------------------

##  Overview

The Universal Data Connector enables AI assistants to safely and
efficiently query:

-    CRM Customer Data
-    Support Tickets
-   Analytics / Metrics Data

It applies intelligent business rules to ensure responses are:

-   ✅ Voice-optimized (max 10 results by default)
-   ✅ Paginated using cursor-based pagination
-   ✅ Freshness-aware
-   ✅ Structured for LLM reasoning
-   ✅ Consistent across data sources

------------------------------------------------------------------------

## 📡 API Endpoints

### Health Check

GET /health

### Legacy Data Access

GET /data/{source}

### Unified LLM Endpoint (Recommended)

POST /v1/query

------------------------------------------------------------------------

##  LLM Function Calling Example

### OpenAI Function Definition

``` json
{
  "name": "query_data",
  "description": "Query CRM, support, or analytics data",
  "parameters": {
    "type": "object",
    "properties": {
      "source": {
        "type": "string",
        "enum": ["crm", "support", "analytics"]
      },
      "mode": {
        "type": "string",
        "enum": ["full", "voice"]
      },
      "query": { "type": "string" },
      "filters": { "type": "object" },
      "cursor": { "type": "string" },
      "limit": { "type": "integer" }
    },
    "required": ["source"]
  }
}
```

------------------------------------------------------------------------

## 🔹 Example Requests

### CRM (Voice Mode)

``` json
{
  "source": "crm",
  "mode": "voice",
  "limit": 5,
  "filters": {
    "status": "active"
  }
}
```

### Analytics Query

``` json
{
  "source": "analytics",
  "mode": "voice",
  "limit": 3,
  "filters": {
    "metric": "daily_active_users"
  }
}
```

### Pagination Example

``` json
{
  "source": "support",
  "mode": "voice",
  "cursor": "eyJvZmZzZXQiOiA1fQ"
}
```

------------------------------------------------------------------------

## ⚙️ Local Setup

pip install -r requirements.txt\
uvicorn app.main:app --reload

Visit: http://127.0.0.1:8000/docs

------------------------------------------------------------------------

## 🐳 Docker Setup

docker-compose up --build

Visit: http://localhost:8000/docs

------------------------------------------------------------------------

##  Run Tests

pytest -v

------------------------------------------------------------------------

## 🔐 Environment Variables

APP_NAME=Universal Data Connector\
MAX_RESULTS=10

------------------------------------------------------------------------

##  Project Status

✔ API working\
✔ Tests passing\
✔ Docker working\
✔ Voice optimization implemented\
✔ Pagination implemented\
✔ LLM-ready structured responses

------------------------------------------------------------------------

Built as part of the Universal Data Connector assignment.
