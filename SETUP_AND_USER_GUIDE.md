# Unified AI Database Copilot — Setup & User Guide

A natural-language interface for PostgreSQL and MongoDB, powered by AWS Bedrock (or Google Gemini) and a LangGraph pipeline.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Project Structure](#2-project-structure)
3. [Backend Setup](#3-backend-setup)
4. [Frontend Setup](#4-frontend-setup)
5. [Running the Project](#5-running-the-project)
6. [End-to-End Verification Checklist](#6-end-to-end-verification-checklist)
7. [Feature Walkthrough](#7-feature-walkthrough)
8. [API Reference](#8-api-reference)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Prerequisites

| Tool | Minimum Version | Notes |
|------|----------------|-------|
| Python | 3.11 | `match/case` syntax required |
| Node.js | 18 | LTS recommended |
| npm | 9 | Comes with Node 18 |
| PostgreSQL | 14 | Running locally on port 5432 |
| MongoDB | 6 | Running locally on port 27017 |
| AWS CLI | any | Only if using Bedrock — credentials needed |

### AWS Bedrock access

You need an AWS account with Bedrock enabled in your chosen region and the model `openai.gpt-oss-120b-1:0` (or another model ID) enabled in the Bedrock console.  
Alternatively, set `LLM_PROVIDER=gemini` and supply a Gemini API key.

### Create the PostgreSQL database

```sql
-- Run in psql or any PG client
CREATE DATABASE copilot_db;
```

MongoDB does not require pre-creating the database — it is created automatically on first write.

---

## 2. Project Structure

```
sql-bot/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + lifespan (Semantic Twin build)
│   │   ├── config.py            # pydantic-settings — reads .env
│   │   ├── api/routes.py        # All HTTP endpoints
│   │   ├── database/
│   │   │   ├── postgres_service.py
│   │   │   └── mongo_service.py
│   │   ├── llm/
│   │   │   ├── base.py          # LLMProvider ABC
│   │   │   ├── bedrock_provider.py
│   │   │   ├── gemini_provider.py
│   │   │   └── factory.py       # get_llm_provider()
│   │   ├── intent/
│   │   │   ├── models.py        # IntentType, TargetDB, IntentResult
│   │   │   └── classifier.py
│   │   ├── semantic_twin/       # FAISS-backed schema index
│   │   │   ├── models.py        # ColumnMeta, ObjectMeta, DatabaseTwin
│   │   │   ├── sql_introspector.py
│   │   │   ├── mongo_introspector.py
│   │   │   ├── embedding_service.py
│   │   │   ├── vector_store.py
│   │   │   └── twin_service.py
│   │   ├── sql_gen/             # NL → PostgreSQL SQL
│   │   ├── mongo_gen/           # NL → MongoDB find/aggregate
│   │   ├── hybrid/              # Cross-DB fusion queries
│   │   ├── schema_ops/          # DDL generation (CREATE/ALTER/DROP)
│   │   ├── viz/                 # Visualization spec generation
│   │   └── planner/
│   │       ├── state.py         # PipelineState TypedDict
│   │       └── workflow.py      # LangGraph 9-node workflow
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.js
│   │   └── components/
│   │       ├── Upload.js        # Dynamic Forms + NL Query UI
│   │       ├── ChartView.js     # Recharts visualization
│   │       ├── HeroSection.js
│   │       ├── Robot.js
│   │       ├── Navbar.js
│   │       └── ...
│   └── package.json
└── SETUP_AND_USER_GUIDE.md      ← this file
```

---

## 3. Backend Setup

### 3.1 Create and activate a virtual environment

```bash
cd sql-bot/backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3.2 Install Python dependencies

```bash
pip install -r requirements.txt
```

The `sentence-transformers` package downloads a small embedding model (~90 MB) on first run — this is normal.

### 3.3 Create the `.env` file

Copy the example and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# ── LLM Provider ──────────────────────────────────────────────
LLM_PROVIDER=bedrock          # "bedrock" | "gemini"

# ── AWS Bedrock ───────────────────────────────────────────────
BEDROCK_REGION=ap-south-1
BEDROCK_MODEL_ID=openai.gpt-oss-120b-1:0
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...

# ── Gemini (alternative to Bedrock) ──────────────────────────
# LLM_PROVIDER=gemini
# GEMINI_API_KEY=AIza...
# GEMINI_MODEL=gemini-3.6-flash

# ── PostgreSQL ────────────────────────────────────────────────
POSTGRES_URL=postgresql+psycopg://postgres:your_password@localhost:5432/copilot_db

# ── MongoDB ───────────────────────────────────────────────────
MONGO_URL=mongodb://localhost:27017
MONGO_DB_NAME=copilot_db

# ── CORS ──────────────────────────────────────────────────────
FRONTEND_ORIGIN=http://localhost:3000

# ── Self-healing retry limit ──────────────────────────────────
MAX_REPAIR_ATTEMPTS=3
```

> **Security note:** Never commit `.env` to version control. It is already in `.gitignore`.

---

## 4. Frontend Setup

```bash
cd sql-bot/frontend
npm install
```

### 4.1 Optional: set the backend URL

By default the frontend connects to `http://localhost:8000`. To change this, create `frontend/.env`:

```env
REACT_APP_BACKEND_URL=http://localhost:8000
```

---

## 5. Running the Project

Open **two terminals**.

### Terminal 1 — Backend

```bash
cd sql-bot/backend
.venv\Scripts\activate          # (Windows) or source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Expected startup output:
```
[startup] Semantic Twin built: 0 object(s) indexed.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

"0 object(s)" is normal on a fresh database — the twin builds once you create tables.

### Terminal 2 — Frontend

```bash
cd sql-bot/frontend
npm start
```

Opens `http://localhost:3000` automatically.

---

## 6. End-to-End Verification Checklist

Work through each step in order. Every item should pass before moving to the next.

---

### Step 1 — Backend health

Open your browser or use curl:

```
GET http://localhost:8000/api/health
```

Expected response:
```json
{"status": "ok"}
```

---

### Step 2 — Database connectivity

```
GET http://localhost:8000/api/health/connections
```

Expected response (fresh DB, no tables yet):
```json
{
  "overall": "ok",
  "postgresql": {"status": "ok", "table_count": 0, "tables": []},
  "mongodb":    {"status": "ok", "collection_count": 0, "collections": []}
}
```

If either shows `"status": "error"`, check that PostgreSQL and MongoDB services are running and the credentials in `.env` are correct.

---

### Step 3 — Create a table via Natural Language

1. Go to `http://localhost:3000/execute-query`
2. Type: **"create a table called employees with name, department, salary, and hire_date"**
3. Click the search button

Expected: a success message like `"Table created successfully."` The DDL will be visible in the response.

---

### Step 4 — Verify the Semantic Twin was updated

```
GET http://localhost:8000/api/schema
```

Expected: `postgresql_tables` now includes `"employees"`.

---

### Step 5 — Dynamic Form: Select Table mode

1. Go to `http://localhost:3000/upload`
2. The **"Select Table"** tab should be active
3. The dropdown should show `employees` (fetched from the Semantic Twin)
4. Select `employees` → click "Generate Form"
5. A form with fields for name, department, salary, hire_date should appear
6. Fill in values and click Submit

Expected toast: `"Data inserted successfully!"`

---

### Step 6 — Dynamic Form: Custom DDL mode

1. Stay on `/upload`, click the **"Custom DDL"** tab
2. Paste this DDL:
   ```sql
   CREATE TABLE products (
     id SERIAL PRIMARY KEY,
     name VARCHAR(200) NOT NULL,
     price NUMERIC(10,2) NOT NULL,
     in_stock BOOLEAN DEFAULT TRUE
   )
   ```
3. Click "Generate Form" → fill in fields → Submit

Expected: row inserted; table created if it didn't exist.

---

### Step 7 — Natural language SELECT query

1. Go to `/execute-query`
2. Type: **"show all employees with their salary"**
3. Click search

Expected: the SQL is shown, and a result table appears with the row(s) you inserted in Step 5.

---

### Step 8 — Visualization query

1. On `/execute-query`
2. Type: **"show me a bar chart of salary by department for all employees"**
3. Click search

Expected: SQL is shown, result table appears, **and a bar chart** renders below the table with department on X-axis and salary on Y-axis.

---

### Step 9 — Schema management (ALTER TABLE)

1. On `/execute-query`
2. Type: **"add an email column to the employees table"**

Expected: `"Schema updated successfully."` and the DDL is shown.

Verify:
```
GET http://localhost:8000/api/schema/objects/employees
```
The `columns` list should now include `email`.

---

### Step 10 — MongoDB collection creation

1. On `/execute-query`
2. Type: **"create a MongoDB collection called user_logs"**

Expected: `"MongoDB collection 'user_logs' created successfully."`

Verify via health/connections endpoint:
```
GET http://localhost:8000/api/health/connections
```
`mongodb.collections` should include `"user_logs"`.

---

### Step 11 — Intent classification (standalone)

```
POST http://localhost:8000/api/intent
Content-Type: application/json

{"nlQuery": "how many employees are in each department?"}
```

Expected:
```json
{
  "intent": "query",
  "target_db": "postgresql",
  "entities": ["employees"],
  "confidence": 0.95
}
```

---

### Step 12 — Manual schema refresh

If you modified the database outside the app:

```
POST http://localhost:8000/api/schema/refresh
```

Expected:
```json
{"message": "Twin refreshed. N object(s) indexed.", ...}
```

---

## 7. Feature Walkthrough

### Natural Language Query (`/execute-query`)

Type any question in plain English. The LangGraph pipeline will:

1. **Classify intent** — determines whether this is a query, DDL, schema change, MongoDB operation, etc.
2. **Retrieve schema context** — FAISS similarity search finds the most relevant tables/collections
3. **Route** — sends to the right generator (SQL / MongoDB / Hybrid / DDL)
4. **Generate** — LLM produces the query or DDL
5. **Validate** — SQLGlot checks SQL syntax before execution
6. **Self-heal** — up to 3 automatic repair attempts on syntax or execution errors
7. **Return** — results, generated SQL/DDL, and optional chart spec

**Examples by intent type:**

| Query | Intent | What happens |
|-------|--------|-------------|
| "show all products cheaper than 50" | `query` | SQL SELECT |
| "add a new employee John, Engineering, 75000" | `crud` | SQL INSERT |
| "bar chart of revenue by month" | `visualization` | SQL + chart rendered |
| "create a table for blog posts" | `table_creation` | DDL executed |
| "add a phone column to employees" | `schema_management` | ALTER TABLE |
| "create a MongoDB collection for events" | `collection_creation` | PyMongo create |
| "what tables do I have?" | `explanation` | Schema summary |

### Dynamic Forms (`/upload`)

**Select Table mode** — pick any existing PostgreSQL table from the dropdown. The app fetches the schema from the Semantic Twin, reconstructs the column definitions, and asks the LLM to generate appropriate HTML input types (text, number, date, checkbox, select, etc.). Fill in the form and submit to insert a row.

**Custom DDL mode** — paste a full `CREATE TABLE` statement. The app parses the DDL and generates the form. The table is created automatically on first insert if it does not exist.

### Visualization

When you ask a visualization-type question (e.g., "chart", "plot", "bar chart of", "show me a graph"), the backend:

1. Executes the SQL query normally
2. Makes a second LLM call to determine the best chart type (`bar`, `line`, `scatter`, `pie`, `histogram`) and axis mapping
3. Returns a `viz_spec` alongside the data

The frontend renders the chart using **Recharts** — a React-native charting library.

### Self-Healing

SQL and DDL generation uses a two-layer repair loop:
- **Layer 1 (syntax)**: SQLGlot parses the generated SQL before execution. If it fails, the LLM is asked to fix the syntax error.
- **Layer 2 (execution)**: If the database rejects the query, the error message is sent back to the LLM for another repair attempt.

Each layer retries up to `MAX_REPAIR_ATTEMPTS` times (default: 3).

### Semantic Twin

The Semantic Twin is an in-memory FAISS index of all PostgreSQL tables and MongoDB collections, including column names, types, and constraints. It is:
- Built automatically at server startup
- Refreshed automatically after any DDL operation (CREATE TABLE, ALTER, collection creation)
- Refreshed manually via `POST /api/schema/refresh`
- Used to inject only the most relevant schema context into each LLM prompt

---

## 8. API Reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Liveness check |
| GET | `/api/health/connections` | PostgreSQL + MongoDB connectivity |
| GET | `/api/schema` | Current Semantic Twin state |
| POST | `/api/schema/refresh` | Rebuild FAISS index from live DBs |
| GET | `/api/schema/objects/{name}` | Full metadata for one table/collection |
| POST | `/api/intent` | Classify a natural-language request |
| POST | `/api/generate-form` | Form fields from raw DDL string |
| POST | `/api/generate-form-by-table` | Form fields from existing table name |
| POST | `/api/insert-data` | Insert a row into a table |
| POST | `/api/nl-query` | Full NL → execute pipeline |

### `POST /api/nl-query` — request

```json
{"nlQuery": "show all employees hired after 2023"}
```

### `POST /api/nl-query` — response fields

| Field | Type | Description |
|-------|------|-------------|
| `sql` | string \| null | Generated PostgreSQL SQL |
| `ddl` | string \| null | Generated DDL (CREATE/ALTER) |
| `mongo_query_spec` | object \| null | MongoDB find/aggregate spec |
| `hybrid_plan` | object \| null | Cross-DB join plan |
| `viz_spec` | object \| null | Chart type + axis mapping |
| `result` | array | Query result rows |
| `columns` | array | Column names |
| `message` | string | Human-readable status |
| `intent` | object | Classified intent |
| `error` | string \| null | Error message if failed |
| `repair_attempts` | int | Number of self-healing retries |
| `repair_history` | array | Per-attempt repair log |

---

## 9. Troubleshooting

### Backend won't start — `ModuleNotFoundError`

Make sure the virtual environment is activated:
```bash
.venv\Scripts\activate   # Windows
source .venv/bin/activate  # macOS/Linux
```
Then re-run `pip install -r requirements.txt`.

### `postgresql connection refused`

Check that PostgreSQL is running:
```bash
# Windows (Services or):
pg_ctl status -D "C:\Program Files\PostgreSQL\16\data"

# macOS (Homebrew):
brew services list | grep postgresql
```
Also confirm the `POSTGRES_URL` in `.env` has the right password and database name.

### `pymongo ServerSelectionTimeoutError`

MongoDB is not running. Start it:
```bash
# Windows:
net start MongoDB

# macOS (Homebrew):
brew services start mongodb-community
```

### `botocore.exceptions.NoCredentialsError`

AWS credentials are not set. Either:
- Add `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` to `.env`
- Run `aws configure` and set credentials globally
- Or switch to `LLM_PROVIDER=gemini` with a valid `GEMINI_API_KEY`

### `ResourceNotFoundException` from Bedrock

The model ID in `BEDROCK_MODEL_ID` is not enabled in your region. Go to the AWS Bedrock console → Model access → enable the model.

### Semantic Twin shows 0 objects after creating tables

Manually call `POST /api/schema/refresh` or restart the backend. This can happen if the startup refresh ran before the table existed.

### Form generation returns "No form fields generated"

The DDL you pasted may be missing column definitions or use non-standard syntax. Ensure it follows standard PostgreSQL `CREATE TABLE` syntax. Try simplifying to basic types first.

### Chart does not appear after a visualization query

The visualization intent is only triggered when the query mentions chart/graph/plot/visualize keywords. Try rephrasing: *"show me a bar chart of..."* or *"plot the count of..."*.

### CORS error in the browser

Ensure `FRONTEND_ORIGIN=http://localhost:3000` in the backend `.env` matches the actual address where the React app is running (no trailing slash).

---

*Built for Cloud Computing — Semester 7 research prototype.*
