# Interactive Recipe & Grocery A2UI Multi-Agent System

An end-to-end multi-agent conversational culinary concierge system built using **Google Agent Development Kit (ADK)**, **Agent-to-Agent (A2A)** protocol, and **A2UI v0.9** rich interactive Material Design cards for **Gemini Enterprise**.

---

## Architecture Overview

```
                                  +-----------------------------------------------+
                                  |            Gemini Enterprise / Web            |
                                  |     (User Interaction & A2UI Renderer)       |
                                  +-----------------------+-----------------------+
                                                          |
                                                          | HTTP / A2A JSON-RPC
                                                          v
                                  +-----------------------------------------------+
                                  |                  main_chatbot                 |
                                  |           (Primary Concierge Router)          |
                                  |  - Recipe Catalog Grid with Category Filter   |
                                  |  - Client-side Material Accordions            |
                                  +-----------------------+-----------------------+
                                                          |
                                                          | A2A Protocol (message/send)
                                                          v
                                  +-----------------------------------------------+
                                  |                  recipe_agent                 |
                                  |      (Culinary & Grocery Specialist Agent)    |
                                  |  - Recipe Parsing & Instruction Formatting    |
                                  |  - Dynamic Servings Slider (1-10 people)      |
                                  |  - Ingredient Scaling Engine                  |
                                  +-----------------------+-----------------------+
                                                          |
                                                          | REST /products/match
                                                          v
                                  +-----------------------------------------------+
                                  |              grocery_db_service               |
                                  |        (FreshMarket Grocery DB API)           |
                                  |  - Fuzzy Search & Ingredient Matcher          |
                                  |  - Pricing, Promos, Pack Sizes, & Images      |
                                  |  - SQLite Database (`groceries.db`)           |
                                  +-----------------------------------------------+
```

---

## Key Features

1. **Rich Interactive A2UI v0.9 Interfaces**:
   - **Recipe Catalog Grid**: 2-column Material Design catalog cards with thumbnail images, category tags, prep/cook times, and client-side expandable ingredient accordions.
   - **Category Filter Bar**: Filter by *All*, *Appetisers*, *Mains*, and *Desserts*.
   - **Interactive Servings Slider**: Real-time slider (1–10 people) that recalculates ingredient quantities and basket totals dynamically.
   - **Grocery Shopping Cards**: Product cards featuring matched grocery items, pack sizes, dietary tags, promotional badges, and direct buy links.

2. **Agent-to-Agent (A2A) Delegation**:
   - Standard JSON-RPC (`message/send`) protocol compliance with automatic fallback to `/api/chat`.
   - Dual A2A routing (`/a2a/app` and root `/`) compatible with Google ADK.
   - Service-to-service Cloud Run authentication support via Google ID tokens.

3. **Dual-Mode Recipe Loading**:
   - Direct Google Drive document integration with local cache fallback (`recipes_cache.json`).
   - Supports both curated catalog recipes and user-submitted custom dishes.

---

## Repository Structure

```
git_recipe_agent/
├── .env.example                     # Global environment variables template
├── .gitignore                       # Git ignore rules (secrets, venvs, DBs)
├── README.md                        # Documentation
├── grocery_db_service/              # Standalone Grocery Database API
│   ├── .env.example
│   ├── Dockerfile
│   ├── main.py                      # FastAPI application & ingredient matching logic
│   ├── requirements.txt
│   └── seed_db.py                   # SQLite schema & product seeder
├── recipe_agent/                    # Recipe & Grocery Specialist A2A Agent
│   ├── .env.example
│   ├── Dockerfile
│   ├── a2ui_builder.py              # A2UI v0.9 JSON message generator
│   ├── a2ui_helpers.py              # A2A / A2UI conversion helpers
│   ├── agent.py                     # ADK LlmAgent definition & prompt
│   ├── agent_executor.py            # A2A AgentExecutor implementation
│   ├── main.py                      # FastAPI + A2A server entrypoint
│   ├── recipes_cache.json           # Sample recipe catalog cache
│   ├── requirements.txt
│   └── tools.py                     # Recipe retrieval & grocery matching tools
└── main_chatbot/                    # Main Gemini Enterprise Chatbot
    ├── .env.example
    ├── Dockerfile
    ├── a2ui_builder.py              # A2UI catalog grid builder
    ├── a2ui_helpers.py              # A2A / A2UI conversion helpers
    ├── agent.py                     # Primary ADK agent & instructions
    ├── agent_executor.py            # A2A AgentExecutor implementation
    ├── main.py                      # FastAPI + A2A server entrypoint
    ├── recipes_cache.json           # Catalog cache
    ├── requirements.txt
    └── tools.py                     # Catalog browser & A2A delegator
```

---

## Configuration & Secrets Management

This project follows standard security practices for managing configuration and secrets:
- **Never commit `.env` files** to version control. The `.gitignore` file is configured to exclude all `.env` files.
- Each service includes a `.env.example` file documenting required environment variables.
- Copy `.env.example` to `.env` in each service folder:

```bash
cp .env.example .env
```

### Key Environment Variables

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `GOOGLE_GENAI_USE_VERTEXAI` | Enables Vertex AI backend for ADK | `TRUE` |
| `GOOGLE_CLOUD_PROJECT` | GCP Project ID for Vertex AI | `your-project-id` |
| `GOOGLE_CLOUD_LOCATION` | GCP Region for Vertex AI models | `us-central1` |
| `GEMINI_MODEL` | Gemini model identifier | `gemini-2.5-flash` |
| `GROCERY_DB_SERVICE_URL` | URL of the Grocery Database service | `http://localhost:8001` |
| `RECIPE_AGENT_URL` | URL of the Recipe Specialist A2A agent | `http://localhost:8002` |

---

## Running Locally

### Prerequisites
- Python 3.11+
- Google Cloud credentials configured (`gcloud auth application-default login`)

### 1. Start the Grocery Database Service (Port 8001)

```bash
cd grocery_db_service
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python3 seed_db.py
uvicorn main:app --host 0.0.0.0 --port 8001
```

Verify:
```bash
curl http://localhost:8001/health
```

### 2. Start the Recipe Specialist Agent (Port 8002)

```bash
cd recipe_agent
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export GROCERY_DB_SERVICE_URL="http://localhost:8001"
export PORT=8002
uvicorn main:app --host 0.0.0.0 --port 8002
```

Verify:
```bash
curl http://localhost:8002/health
```

### 3. Start the Main Chatbot (Port 8000)

```bash
cd main_chatbot
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export RECIPE_AGENT_URL="http://localhost:8002"
export PORT=8000
uvicorn main:app --host 0.0.0.0 --port 8000
```

Verify:
```bash
curl http://localhost:8000/health
```

---

## Deployment (Google Cloud Run)

Each service contains a containerized `Dockerfile` ready for deployment to Cloud Run.

### Deploying with Google Cloud CLI:

```bash
# 1. Deploy Grocery DB Service
gcloud run deploy grocery-db-service \
    --source ./grocery_db_service \
    --region us-central1 \
    --allow-unauthenticated

# 2. Deploy Recipe Specialist Agent
gcloud run deploy recipe-grocery-agent \
    --source ./recipe_agent \
    --region us-central1 \
    --set-env-vars GROCERY_DB_SERVICE_URL="https://grocery-db-service-<HASH>.run.app",GOOGLE_CLOUD_PROJECT="your-project-id" \
    --allow-unauthenticated

# 3. Deploy Main Chatbot
gcloud run deploy main-chatbot-agent \
    --source ./main_chatbot \
    --region us-central1 \
    --set-env-vars RECIPE_AGENT_URL="https://recipe-grocery-agent-<HASH>.run.app",GOOGLE_CLOUD_PROJECT="your-project-id" \
    --allow-unauthenticated
```

---

## Result Images

### Listing Recipes in Catalogue (Main Agent)

<img width="633" height="842" alt="image" src="https://github.com/user-attachments/assets/85b7d0c5-915e-4f49-bafc-0b291994b5c0" />

### Recipe Guide Section

<img width="658" height="1057" alt="image" src="https://github.com/user-attachments/assets/dfcdf85b-35f1-4abf-b429-1409a7de28e6" />

### Grocery Section

<img width="658" height="748" alt="image" src="https://github.com/user-attachments/assets/431b19ca-f29c-456a-8f65-c49f547de72b" />

---

## License

This project is licensed under the Apache 2.0 License.
