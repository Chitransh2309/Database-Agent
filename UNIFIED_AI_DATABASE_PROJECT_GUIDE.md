# Unified AI Database Copilot
## Complete Implementation Specification for Claude Code

**Document purpose:** This is the master implementation specification for extending the existing `sql-bot` project into the complete cloud-computing project described below. Claude Code must read this document together with the entire existing repository before modifying code.

---

# 0. Critical Instructions and Scope

## Project objective

Transform the existing LLM-based SQL bot into a unified natural-language database management system that supports:

- Relational SQL databases, initially PostgreSQL.
- NoSQL document databases, initially MongoDB.
- Natural-language query generation.
- Semantic schema understanding through a Semantic Database Twin.
- Cross-database routing and hybrid query planning.
- Execution-grounded autonomous query repair.
- Natural-language database/table/collection creation.
- CRUD operations.
- Dynamic data-entry forms generated from schemas.
- Result visualization and natural-language explanations.
- Cloud deployment using Docker on AWS EC2 or Azure Virtual Machine.

## Explicit scope exclusions

The application is intended for a single user and is an academic/research prototype. Do **not** add unnecessary enterprise non-functional features.

Do NOT implement unless required for the application to function:

- User authentication.
- IAM.
- Role-based access control.
- Multi-tenant architecture.
- CDN.
- CloudFront.
- Redis/cache infrastructure.
- Kubernetes.
- Auto-scaling.
- Load balancing.
- High availability.
- Enterprise secrets-management infrastructure.
- Complex observability stacks.
- Payment/billing systems.
- Distributed deployment.
- Bedrock for the actual database LLM.
- Microservices unless there is a concrete implementation reason.

Simple `.env` configuration is sufficient for local/cloud secrets.

## LLM provider

Do **not** use Amazon Bedrock for the database assistant.

The database assistant should use the **Gemini API** through Google's current Python SDK (`google-genai`) with a configurable model name. Keep the model configurable through an environment variable so the project is not tied to one model version.

As of the project specification date, Google's model documentation lists Gemini 3.7 Flash as a stable model for complex coding/agentic workflows and Gemini 2.5 Flash as a stable price/performance option. The implementation should use an environment variable such as:

```env
GEMINI_MODEL=gemini-3.7-flash
```

and allow changing it without code changes.

Use the official `google-genai` Python SDK.

Official documentation:
- Gemini API models: https://ai.google.dev/gemini-api/docs/models
- Gemini API getting started: https://ai.google.dev/gemini-api/docs/get-started

---

# 1. Project Identity

## Working title

**Unified AI Database Copilot**

The product name may be changed later for the research paper. The implementation should therefore avoid hard-coding the name into internal module names.

## Research framing

The project is a:

> Semantic multi-agent framework for natural-language interaction and autonomous query processing across heterogeneous SQL and NoSQL databases.

The main research contributions are:

1. Semantic Database Twin.
2. Universal Cross-Database Query Planner.
3. Execution-grounded Autonomous Self-Healing Query Engine.
4. Unified natural-language database management across SQL and NoSQL.

---

# 2. Problem Being Solved

Modern data environments can contain multiple database paradigms. A user may have:

- Customer data in PostgreSQL.
- Transaction data in PostgreSQL/MySQL.
- Logs or activity data in MongoDB.
- Nested product/review data in MongoDB.

The user normally needs knowledge of:

- SQL.
- MongoDB aggregation pipelines.
- Database schemas.
- Relationships.
- Joins.
- Data types.
- Database-specific syntax.

Existing natural-language database systems often focus on one database paradigm and frequently operate as one-shot query generators.

The project addresses:

- Database-specific query-language complexity.
- Poor semantic understanding of schema names.
- Large-schema context problems.
- SQL-only or NoSQL-only limitations.
- Lack of cross-database routing.
- Lack of hybrid SQL + NoSQL execution.
- Query-generation failures.
- Manual error correction.
- Limited natural-language database management.
- Lack of a unified end-to-end architecture.

---

# 3. Core System Concept

The user should be able to type:

> Show all customers from Delhi whose total purchases this year exceed ₹10,000.

The system should determine:

1. What the user wants.
2. Which database contains the required information.
3. Which tables/collections are relevant.
4. Whether the task is SQL, MongoDB, or hybrid.
5. What query/pipeline must be generated.
6. Whether the generated query executes successfully.
7. If it fails, why it failed.
8. How to repair it.
9. How to present the result.
10. Whether a table, chart, summary, or explanation is useful.

The user should not need to write SQL or MongoDB syntax.

---

# 4. Core Features

## Feature A — Natural Language Querying

Support:

- SELECT-style retrieval.
- Filtering.
- Sorting.
- Grouping.
- Aggregation.
- Joins.
- Subqueries where supported.
- MongoDB aggregation pipelines.
- CRUD requests.
- Database metadata questions.

Example:

> Find the top 5 customers by total order value.

---

# 5. Semantic Database Twin

## Purpose

The Semantic Database Twin is an AI-readable representation of the connected databases.

It should NOT merely store raw schema text.

It should represent:

- Database.
- Database type.
- Table/collection.
- Column/field.
- Data type.
- Primary keys.
- Foreign keys.
- Relationships.
- Constraints.
- Indexes where available.
- Sample values.
- Descriptions/semantic labels.
- Nested document structure.
- Relationship mappings.
- Embeddings.

## SQL introspection

Use SQLAlchemy.

Initially support PostgreSQL.

Extract at minimum:

```text
database
schema
table
column
data type
nullable
primary key
foreign key
foreign-key target
unique constraint
index
```

Also collect a small, configurable sample of values for semantic interpretation.

Do not dump entire tables into the LLM.

## MongoDB introspection

Use PyMongo.

Extract:

```text
database
collection
field
inferred type
nested path
array fields
sample values
```

For example:

```text
orders
 ├── order_id
 ├── customer
 │    ├── customer_id
 │    ├── name
 │    └── location
 │         └── city
 └── items[]
      ├── product_id
      ├── quantity
      └── price
```

## Semantic representation

Create normalized metadata records such as:

```json
{
  "source_type": "postgresql",
  "database": "sales_db",
  "object_type": "table",
  "object_name": "orders",
  "description": "Stores customer purchase transactions",
  "fields": [
    {
      "name": "customer_id",
      "type": "integer",
      "semantic_label": "customer identifier"
    }
  ],
  "relationships": [
    {
      "field": "customer_id",
      "target": "customers.customer_id",
      "type": "foreign_key"
    }
  ]
}
```

Equivalent records must exist for MongoDB collections/documents.

## Embeddings

Use:

- Sentence Transformers.
- FAISS.

Create embeddings for:

- Database descriptions.
- Tables.
- Columns.
- Relationships.
- MongoDB collection/field descriptions.
- Useful sample-value context.

The embedding index should map vectors back to structured metadata IDs.

## Retrieval

Given a user query:

```text
Which customers from Delhi spent the most?
```

retrieve relevant semantic context such as:

```text
customers
orders
customers.city
orders.customer_id
orders.amount
```

Do not pass the entire schema if only a small portion is relevant.

---

# 6. Universal Cross-Database Query Planner

## Purpose

The planner determines whether the request requires:

```text
SQL
MongoDB
Hybrid SQL + MongoDB
Schema management
CRUD
Visualization/analysis
```

## Planner output

Use a strict Pydantic model.

Example:

```json
{
  "intent": "analytical_query",
  "execution_mode": "hybrid",
  "sources": [
    {
      "type": "postgresql",
      "objects": ["customers", "orders"]
    },
    {
      "type": "mongodb",
      "objects": ["activity"]
    }
  ],
  "operations": [
    "filter",
    "aggregate",
    "join_results"
  ]
}
```

The actual structure can be improved after examining the existing implementation.

## Planner responsibilities

- Interpret intent.
- Identify required data.
- Select database source(s).
- Select relevant tables/collections.
- Decompose complex requests.
- Decide whether parallel execution is possible.
- Determine how results should be combined.
- Pass structured context to the appropriate generator.

---

# 7. SQL Query Generator

The SQL generator receives:

- User request.
- Intent.
- Relevant Semantic Twin context.
- Planner output.
- Database dialect.

It returns structured output:

```json
{
  "query": "SELECT ...",
  "explanation": "..."
}
```

It must not invent schema elements when the Semantic Twin does not support them.

Use SQLAlchemy for execution.

Use SQLGlot where useful for:

- SQL parsing.
- Syntax validation.
- Dialect-aware analysis.
- Normalization.

Do not treat SQLGlot validation as a replacement for real database execution.

---

# 8. MongoDB Query Generator

The MongoDB generator receives:

- User request.
- Semantic MongoDB schema.
- Planner output.

Generate:

- find queries where appropriate.
- aggregation pipelines for complex analytics.
- insert/update/delete operations.
- collection creation operations where required.

Return structured output.

Example:

```json
{
  "operation": "aggregate",
  "collection": "orders",
  "pipeline": [
    {
      "$match": {
        "customer.city": "Delhi"
      }
    }
  ]
}
```

Execute through PyMongo.

---

# 9. Hybrid SQL + NoSQL Execution

This is one of the most important parts of the project.

Example request:

> Find customers whose MongoDB activity indicates high engagement and whose PostgreSQL purchases exceed ₹10,000.

The planner should produce:

```text
User Request
      |
      v
Intent Analysis
      |
      v
Semantic Twin
      |
      v
Hybrid Planner
   /        \
  v          v
PostgreSQL  MongoDB
  |           |
  v           v
SQL result  Mongo result
   \         /
    \       /
     v     v
 Result Integration
        |
        v
 Final Answer
```

## Important constraint

Do not pretend PostgreSQL and MongoDB can be joined by SQL directly.

The application-level integration layer must:

1. Execute the SQL query.
2. Execute the MongoDB query.
3. Normalize identifiers/fields.
4. Join or intersect results in Python when needed.
5. Produce a unified result.

Use Pandas or explicit Python data structures depending on result size.

For the academic prototype, keep result sizes bounded and configurable.

---

# 10. Autonomous Self-Healing Query Engine

## Core loop

```text
Generate
   |
Execute
   |
Success? ---- YES ---> Return Result
   |
   NO
   |
Capture Error
   |
Classify Error
   |
Retrieve Relevant Schema
   |
Repair Query
   |
Retry
   |
Maximum Attempts?
   |
   YES ---> Return Explainable Failure
```

## Error types to support

SQL:

- Syntax errors.
- Undefined column.
- Undefined table.
- Invalid join.
- Wrong data type.
- Invalid function.
- Ambiguous column.
- Constraint-related failures where relevant.

MongoDB:

- Invalid field/path.
- Invalid aggregation operator.
- Type mismatch.
- Collection mismatch.
- Pipeline errors.
- Invalid update syntax.

## Repair prompt context

The repair model should receive:

```text
Original user request
Generated query
Database type
Relevant schema context
Database error
Attempt number
Previous failed query
```

It should return a corrected structured query.

## Retry policy

Default:

```text
MAX_REPAIR_ATTEMPTS=3
```

Make configurable.

Avoid infinite loops.

## Self-healing state

Use LangGraph state containing:

```text
user_prompt
intent
semantic_context
plan
generated_query
execution_result
error
repair_attempt
final_result
```

---

# 11. Natural Language Database Management

This feature extends the project beyond Text-to-SQL.

## Database/table/collection creation

User:

> Create a student database with students, courses, attendance and marks.

The system should:

1. Infer entities.
2. Infer fields.
3. Infer data types.
4. Infer relationships.
5. Produce a structured schema plan.
6. Show/validate the plan.
7. Generate DDL or MongoDB creation operations.
8. Execute them.

## Table creation example

User:

> Create an employee table with employee ID, name, department, salary and joining date.

Generate a structured table definition first.

Example internal representation:

```json
{
  "table": "employees",
  "columns": [
    {"name": "employee_id", "type": "INTEGER", "primary_key": true},
    {"name": "name", "type": "TEXT"},
    {"name": "department", "type": "TEXT"},
    {"name": "salary", "type": "NUMERIC"},
    {"name": "joining_date", "type": "DATE"}
  ]
}
```

Then generate executable SQL.

## Dynamic forms

Once a table/collection schema exists, the frontend can automatically render a form.

Example:

```text
Employee
----------------------
Employee ID [______]
Name        [______]
Department  [______]
Salary      [______]
Joining Date[______]

        [Add Record]
```

The form must be generated from the schema, not manually coded per table.

## CRUD

Natural language:

- Add a student named Ravi with ID 101.
- Update Ravi's marks to 92.
- Delete student 101.
- Show all students in CSE.

The planner routes the operation.

---

# 12. Visualization and Explanation

After successful analytical queries, the system should determine whether a visualization is appropriate.

Possible outputs:

- Table.
- Bar chart.
- Line chart.
- Pie chart where appropriate.
- KPI/summary.
- Natural-language explanation.

Use Plotly in the frontend.

The backend should return structured result data and visualization metadata rather than returning raw HTML.

Example:

```json
{
  "columns": ["month", "revenue"],
  "rows": [
    ["Jan", 12000],
    ["Feb", 14500]
  ],
  "visualization": {
    "type": "line",
    "x": "month",
    "y": "revenue"
  },
  "summary": "Revenue increased from January to February."
}
```

---

# 13. Frontend

The attached existing README confirms that the current frontend is a **Create React App** project and currently supports:

```bash
npm start
npm test
npm run build
```

Do not blindly migrate the frontend to Vite or another framework. First inspect the actual repository and preserve useful existing work.

## Required frontend areas

### Chat interface

- Prompt input.
- Conversation history.
- Generated query display.
- Execution status.
- Repair attempt display.
- Final result.

### Database connection/setup

Because this is a single-user academic prototype, a simple configuration interface is sufficient.

Allow:

- PostgreSQL connection details.
- MongoDB connection details.
- Database/collection discovery.

Do not implement user accounts.

### Schema explorer

Show:

```text
PostgreSQL
 ├── customers
 ├── orders
 └── products

MongoDB
 ├── activity
 └── reviews
```

Allow viewing semantic metadata.

### Dynamic forms

Render based on returned schema.

### Results

- Data table.
- Generated SQL/Mongo query.
- Explanation.
- Repair history.
- Visualization.

---

# 14. Backend Architecture

Recommended backend structure:

```text
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   │
│   ├── api/
│   │   ├── routes_chat.py
│   │   ├── routes_databases.py
│   │   ├── routes_schema.py
│   │   ├── routes_crud.py
│   │   └── routes_visualization.py
│   │
│   ├── agents/
│   │   ├── intent_agent.py
│   │   ├── planner_agent.py
│   │   ├── sql_agent.py
│   │   ├── mongo_agent.py
│   │   ├── repair_agent.py
│   │   └── response_agent.py
│   │
│   ├── semantic_twin/
│   │   ├── sql_introspector.py
│   │   ├── mongo_introspector.py
│   │   ├── metadata_models.py
│   │   ├── embedding_service.py
│   │   ├── vector_store.py
│   │   └── retriever.py
│   │
│   ├── planner/
│   │   ├── graph.py
│   │   ├── state.py
│   │   └── routing.py
│   │
│   ├── execution/
│   │   ├── sql_executor.py
│   │   ├── mongo_executor.py
│   │   ├── hybrid_executor.py
│   │   └── error_classifier.py
│   │
│   ├── database_management/
│   │   ├── schema_builder.py
│   │   ├── ddl_generator.py
│   │   ├── collection_builder.py
│   │   └── crud_service.py
│   │
│   ├── visualization/
│   │   └── recommendation.py
│   │
│   └── models/
│       └── schemas.py
│
├── tests/
├── requirements.txt
├── Dockerfile
└── .env.example
```

This is a target architecture, not a command to duplicate folders blindly. Claude Code must adapt it to the actual repository.

---

# 15. API Design

Recommended endpoints:

## Health

```text
GET /health
```

## Chat

```text
POST /api/chat
```

Input:

```json
{
  "message": "Show top customers by revenue"
}
```

Output should include structured fields such as:

```json
{
  "answer": "...",
  "intent": "...",
  "plan": {},
  "generated_queries": [],
  "results": {},
  "visualization": {},
  "repair_attempts": []
}
```

## Database connections

```text
POST /api/databases/connect
GET  /api/databases
DELETE /api/databases/{id}
```

For a single-user prototype, an in-memory/runtime registry or simple local configuration is acceptable.

## Schema

```text
POST /api/schema/refresh
GET  /api/schema
GET  /api/schema/{database}
```

## CRUD

```text
POST   /api/data/insert
PATCH  /api/data/update
DELETE /api/data/delete
GET    /api/data
```

## Database management

```text
POST /api/database/plan
POST /api/database/create-table
POST /api/database/create-collection
```

Exact endpoint naming can be changed after repository inspection.

---

# 16. LangGraph Workflow

Use LangGraph to represent the reasoning/execution workflow rather than creating one giant prompt.

Target graph:

```text
START
  |
  v
Intent Analysis
  |
  v
Semantic Retrieval
  |
  v
Universal Planner
  |
  +--------------------+
  |                    |
  v                    v
SQL Generator      Mongo Generator
  |                    |
  +---------+----------+
            |
            v
      Execution Router
            |
            v
       SQL/Mongo/Hybrid
            |
            v
     Execution Successful?
        /             \
      YES              NO
       |                |
       v                v
 Result Integration   Error Classifier
       |                |
       v                v
 Visualization      Repair Agent
       |                |
       v                v
 Response          Retry Planner/Generator
                        |
                        +----> Execution
```

For hybrid queries, SQL and Mongo branches may execute independently before the result integration node.

---

# 17. Pydantic Structured Outputs

Use Pydantic models for every important LLM boundary.

Recommended models:

```text
IntentResult
SemanticContext
QueryPlan
SQLQueryResult
MongoQueryResult
RepairResult
ExecutionResult
VisualizationSpec
DatabaseSchemaPlan
TableSchemaPlan
CRUDOperation
FinalResponse
```

Do not rely on parsing arbitrary natural-language LLM output when structured output can be used.

---

# 18. LLM Prompt Architecture

Do not use one giant prompt.

Create separate prompts for:

1. Intent analysis.
2. Semantic interpretation.
3. Query planning.
4. SQL generation.
5. MongoDB generation.
6. Query repair.
7. Schema/table generation.
8. CRUD generation.
9. Visualization recommendation.
10. Natural-language response.

Each prompt should receive only the information it needs.

## Important rule

The model must be explicitly told:

> Only use database objects supplied in the retrieved schema context. Do not invent tables, columns, collections, fields, relationships, or values.

---

# 19. Database Connection Design

Use:

### PostgreSQL

```text
SQLAlchemy
psycopg
```

Connection string:

```env
POSTGRES_URL=postgresql+psycopg://user:password@host:5432/database
```

### MongoDB

```text
PyMongo
```

Connection:

```env
MONGO_URL=mongodb://user:password@host:27017/
MONGO_DATABASE=database_name
```

For local development, Docker Compose should be able to start PostgreSQL and MongoDB.

---

# 20. Local Development Environment

Recommended:

```text
Windows / Linux / WSL
        |
        +-- Node.js
        +-- Python 3.x
        +-- Docker Desktop
        +-- Git
        +-- PostgreSQL
        +-- MongoDB
```

Use Docker for PostgreSQL and MongoDB if practical so all teammates have reproducible databases.

---

# 21. Docker

Use containers for:

- Backend.
- Frontend if desired for production.
- PostgreSQL.
- MongoDB.

Development can use:

```text
docker-compose.yml
```

Example architecture:

```text
docker compose
├── frontend
├── backend
├── postgres
└── mongodb
```

FAISS can remain inside the backend container initially.

Do not introduce Kubernetes.

---

# 22. Cloud Deployment

## Preferred simple AWS deployment

```text
Internet
   |
   v
AWS EC2
Ubuntu
   |
   v
Docker Compose
   |
   +-------------------+
   |                   |
   v                   v
Backend             Frontend
FastAPI             React
   |
   +--------+---------+
   |        |         |
   v        v         v
Postgres MongoDB    FAISS
```

For the academic prototype, it is acceptable to run the complete stack on one EC2 instance.

## AWS components

Required:

- AWS account.
- EC2 instance.
- Ubuntu.
- Docker.
- Docker Compose.
- Security-group rules sufficient for the application to function.
- SSH access for deployment.

Do not add:

- IAM architecture beyond what AWS itself requires for the account/instance.
- CloudFront.
- CDN.
- ECS.
- EKS.
- Auto Scaling.
- Load Balancer.
- Redis.
- RDS unless you later decide you need managed PostgreSQL.

## Alternative Azure deployment

```text
Azure VM
   |
Docker Compose
   |
Frontend + Backend + PostgreSQL + MongoDB + FAISS
```

Use one VM for simplicity.

---

# 23. Cloud Deployment Steps

## Step 1

Create EC2 Ubuntu instance.

## Step 2

Install:

```text
Docker
Docker Compose
Git
```

## Step 3

Clone repository.

## Step 4

Create production `.env`.

## Step 5

Build containers.

```bash
docker compose build
```

## Step 6

Start:

```bash
docker compose up -d
```

## Step 7

Verify:

```text
GET /health
```

## Step 8

Open the frontend.

## Step 9

Connect PostgreSQL/MongoDB.

## Step 10

Run end-to-end test queries.

---

# 24. Environment Variables

Create `.env.example`:

```env
# LLM
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.7-flash

# PostgreSQL
POSTGRES_URL=

# MongoDB
MONGO_URL=
MONGO_DATABASE=

# Application
BACKEND_URL=
FRONTEND_URL=

# Semantic retrieval
EMBEDDING_MODEL=
FAISS_INDEX_PATH=
TOP_K_SCHEMA_RESULTS=8

# Self healing
MAX_REPAIR_ATTEMPTS=3

# Query limits
MAX_RESULT_ROWS=1000
QUERY_TIMEOUT_SECONDS=30
```

Never commit real API keys.

---

# 25. Important Runtime Constraints

Because this is a single-user academic prototype:

- Keep maximum query result sizes bounded.
- Use configurable query timeouts.
- Limit repair attempts.
- Avoid loading entire databases into memory.
- Avoid sending full datasets to the LLM.
- Retrieve schema context rather than raw database contents.
- Keep embeddings local.
- Keep architecture simple.

---

# 26. Safety/Correctness for Database-Modifying Operations

The project does not need enterprise security.

However, database correctness still matters.

For destructive or schema-changing natural-language operations, the application should use a confirmation step.

Example:

> Delete all students who graduated before 2020.

Show:

```text
Operation: DELETE
Target: students
Condition: graduation_year < 2020

[Confirm] [Cancel]
```

This is a usability/correctness feature, not an authentication/security system.

For read-only SELECT/aggregation requests, execute directly.

---

# 27. Database Creation Workflow

```text
Natural Language Request
        |
        v
Intent = Schema Management
        |
        v
Schema Planner
        |
        v
Structured Schema
        |
        v
Validation
        |
        v
SQL DDL / Mongo Creation
        |
        v
Execution
        |
        v
Refresh Semantic Twin
        |
        v
Generate Dynamic Forms
```

Important:

After a successful schema change, the Semantic Database Twin must be refreshed so the new tables/fields immediately become queryable.

---

# 28. Dynamic Form Workflow

```text
Database Schema
      |
      v
Schema Parser
      |
      v
Form Specification
      |
      v
React Dynamic Form
      |
      v
User Data
      |
      v
CRUD API
      |
      v
Database
```

Example form field mapping:

```text
INTEGER  -> number input
NUMERIC  -> number input
TEXT     -> text input
BOOLEAN  -> checkbox
DATE     -> date picker
ENUM     -> select
FOREIGN KEY -> select/autocomplete
```

Mongo nested objects should be represented recursively.

---

# 29. Semantic Twin Refresh Strategy

At minimum implement:

```text
Manual refresh
```

and automatically refresh after:

- table creation.
- collection creation.
- schema alteration.
- database reconnection.

For the prototype, do not build a complex event-driven metadata synchronization system.

---

# 30. Research Evaluation

This project is intended to become a conference/journal paper as well as the cloud-computing project.

The paper should not claim that the individual components were invented from scratch.

The research contribution is the integrated framework and its evaluated behavior.

## Primary research question

> Can semantic schema understanding combined with autonomous cross-database query planning and execution-grounded repair improve the reliability and usability of natural-language interaction across heterogeneous SQL and NoSQL databases?

## Metrics

Measure:

### Query execution success rate

```text
successful generated queries / total queries
```

### First-attempt success rate

```text
successful first execution / total queries
```

### Self-healing success rate

```text
failed initial queries successfully repaired / repair-triggering queries
```

### Average repair attempts

```text
total repair attempts / repaired queries
```

### Schema retrieval precision

How often retrieved schema objects are relevant.

### Hybrid query success rate

Percentage of cross-database tasks successfully completed.

### Latency

Measure:

- Intent analysis.
- Retrieval.
- Generation.
- Execution.
- Repair.
- End-to-end latency.

### Token/API usage

Record model calls and token usage where the API exposes it.

---

# 31. Ablation Studies

These are important for publication.

Compare:

## Baseline A

Original SQL bot.

## Baseline B

LLM + raw schema prompt.

## Experiment C

LLM + Semantic Database Twin.

## Experiment D

Semantic Twin + Query Planner.

## Experiment E

Semantic Twin + Planner + Self-Healing.

## Experiment F

Full SQL + MongoDB + hybrid system.

This lets the paper show which component actually improves performance.

---

# 32. Test Dataset Strategy

Use several categories rather than only a few demo prompts.

## SQL tasks

- Simple retrieval.
- Filtering.
- Aggregation.
- Multi-table joins.
- Nested queries.
- Ambiguous natural-language questions.
- Schema synonym questions.

## MongoDB tasks

- Simple document retrieval.
- Nested fields.
- Arrays.
- Aggregation.
- Filtering.
- Grouping.

## Hybrid tasks

- Shared customer ID.
- SQL transaction + Mongo activity.
- SQL product + Mongo reviews.
- SQL customer + Mongo behavior.

## Self-healing tasks

Intentionally create prompts that cause:

- Wrong column.
- Wrong table.
- Wrong field path.
- Wrong Mongo operator.
- Invalid join.
- Ambiguous field.
- Data-type mismatch.

Record whether the system repairs them.

---

# 33. Example Demonstrations

## Demo 1 — SQL

User:

> Which five customers spent the most this year?

System:

```text
Intent: Analytical query
Source: PostgreSQL
Tables: customers, orders
Operation: JOIN + GROUP BY + ORDER BY
```

Then:

```sql
SELECT ...
```

Execute -> table + bar chart.

---

## Demo 2 — MongoDB

User:

> Show all users whose activity contains more than 10 sessions this month.

System:

```text
Source: MongoDB
Collection: activity
Operation: aggregation
```

Generate pipeline -> execute -> result.

---

## Demo 3 — Self-healing

Generated query:

```sql
SELECT customer FROM customers;
```

Error:

```text
column "customer" does not exist
```

Repair:

```sql
SELECT customer_name FROM customers;
```

Execute successfully.

UI should show:

```text
Initial query: failed
Repair attempt 1: corrected
Final status: successful
```

---

## Demo 4 — Hybrid

User:

> Find customers with more than ₹10,000 in purchases who were active on the website more than 20 times.

Planner:

```text
PostgreSQL:
customer + purchases

MongoDB:
customer activity

Application-level result fusion:
customer_id
```

Return unified result.

---

## Demo 5 — Table creation

User:

> Create a student table with ID, name, branch, semester and CGPA.

System generates schema plan -> confirms -> executes -> refreshes Semantic Twin -> generates dynamic form.

---

# 34. Detailed Implementation Timeline

## Week 1 — Repository analysis and stabilization

Claude Code must:

- Read every source file.
- Understand current frontend.
- Identify existing backend.
- Run existing application.
- Run existing tests/build.
- Document current behavior.
- Preserve working SQL-bot functionality.

Deliverable:

```text
Working baseline + architecture inventory
```

---

## Week 2 — LLM abstraction and backend foundation

Implement:

- Gemini API adapter.
- Environment configuration.
- Pydantic models.
- Backend API foundation.
- Error handling.

Deliverable:

```text
Existing SQL bot works through clean LLM service abstraction.
```

---

## Week 3 — Semantic Database Twin

Implement:

- PostgreSQL introspection.
- MongoDB introspection.
- Metadata models.
- Sentence Transformers.
- FAISS.
- Retrieval API.
- Refresh mechanism.

Deliverable:

```text
Natural language -> relevant schema context
```

---

## Week 4 — Universal Query Planner

Implement:

- Intent classification.
- Structured QueryPlan.
- SQL routing.
- Mongo routing.
- Hybrid routing.
- LangGraph state.

Deliverable:

```text
Prompt -> semantic context -> execution plan
```

---

## Week 5 — SQL + Mongo execution

Implement:

- SQL generator.
- Mongo generator.
- SQLAlchemy executor.
- PyMongo executor.
- Hybrid executor.
- Result normalization.

Deliverable:

```text
SQL + Mongo + hybrid execution
```

---

## Week 6 — Self-healing

Implement:

- Error capture.
- Error classification.
- Repair agent.
- Retry loop.
- Attempt history.
- LangGraph repair cycle.

Deliverable:

```text
Generate -> execute -> repair -> retry
```

---

## Week 7 — Database management + forms

Implement:

- Table creation.
- Collection creation.
- Schema generation.
- CRUD.
- Dynamic forms.
- Schema refresh after changes.

Deliverable:

```text
Natural-language database management
```

---

## Week 8 — Visualization + cloud

Implement:

- Result visualization.
- Query explanation.
- Docker.
- Docker Compose.
- AWS EC2 deployment.
- Final integration.

Deliverable:

```text
Complete cloud-deployed application
```

If time is available, use the remaining period for benchmarking, ablations, paper writing, and UI polish.

---

# 35. Complexity Ranking

| Component | Complexity |
|---|---:|
| Existing SQL bot integration | ★★☆☆☆ |
| Gemini API abstraction | ★★☆☆☆ |
| PostgreSQL introspection | ★★★☆☆ |
| MongoDB introspection | ★★★☆☆ |
| Semantic Database Twin | ★★★★★ |
| FAISS retrieval | ★★★★☆ |
| Intent analysis | ★★★☆☆ |
| Universal planner | ★★★★★ |
| SQL generator | ★★★☆☆ |
| Mongo generator | ★★★★☆ |
| Hybrid execution | ★★★★★ |
| Self-healing | ★★★★★ |
| Dynamic forms | ★★★☆☆ |
| Database creation | ★★★★☆ |
| Visualization | ★★★☆☆ |
| Docker | ★★★☆☆ |
| AWS deployment | ★★★☆☆ |
| Research evaluation | ★★★★☆ |

---

# 36. Tool Stack

## Required

### Programming

- Python
- JavaScript/TypeScript
- SQL

### Frontend

- React
- Existing Create React App unless repository inspection justifies migration
- Plotly

### Backend

- FastAPI
- Pydantic

### LLM

- Gemini API
- `google-genai`

### Agent orchestration

- LangGraph

### SQL

- SQLAlchemy
- psycopg
- PostgreSQL
- SQLGlot

### NoSQL

- PyMongo
- MongoDB

### Semantic retrieval

- Sentence Transformers
- FAISS

### Data processing

- Pandas

### Deployment

- Docker
- Docker Compose
- AWS EC2 or Azure VM

### Development

- Git
- GitHub
- VS Code
- Python virtual environment

---

# 37. Tools NOT Required

Do not add these simply because they are common in production architectures:

- AWS Bedrock.
- AWS Lambda.
- API Gateway.
- CloudFront.
- ElastiCache/Redis.
- ECS.
- EKS.
- Kubernetes.
- Cognito.
- IAM application roles.
- RDS if PostgreSQL in Docker is sufficient.
- OpenSearch.
- Pinecone.
- Weaviate.
- Kafka.
- Airflow.

FAISS is sufficient for the semantic index.

---

# 38. Target Architecture

```mermaid
flowchart TD
    U[User] --> F[React Web Interface]

    F --> API[FastAPI Backend]

    API --> G[LangGraph Orchestrator]

    G --> I[Intent Analysis]
    I --> T[Semantic Database Twin]

    T --> M[Schema Metadata]
    T --> E[Sentence Transformers + FAISS]
    T --> R[Relationship / Document Mapping]

    M --> P[Universal Cross-Database Query Planner]
    E --> P
    R --> P

    P --> S[SQL Generator]
    P --> N[MongoDB Generator]

    S --> PG[(PostgreSQL)]
    N --> MG[(MongoDB)]

    PG --> X[Execution / Result Layer]
    MG --> X

    X --> D{Execution Successful?}

    D -->|Yes| RI[Result Integration]
    D -->|No| H[Autonomous Self-Healing]

    H --> T
    H --> P

    RI --> V[Visualization + Natural Language Explanation]
    V --> F
```

---

# 39. System Architecture

```mermaid
flowchart LR
    subgraph Client["Client Layer"]
        USER[User]
        FE[React + TypeScript]
    end

    subgraph App["Application Layer"]
        API[FastAPI]
        ORCH[LangGraph]
    end

    subgraph AI["AI Intelligence Layer"]
        INT[Intent Analysis]
        TWIN[Semantic Database Twin]
        PLAN[Universal Query Planner]
        SQL[SQL Generator]
        MONGO[MongoDB Generator]
        HEAL[Self-Healing Engine]
        FUSE[Result Integration]
    end

    subgraph DB["Database Layer"]
        PG[(PostgreSQL)]
        MDB[(MongoDB)]
    end

    subgraph SEM["Semantic Storage"]
        FAISS[(FAISS Index)]
    end

    subgraph OUT["Output Layer"]
        VIS[Plotly / Tables / Explanation]
    end

    USER --> FE
    FE --> API
    API --> ORCH
    ORCH --> INT
    INT --> TWIN
    TWIN --> FAISS
    TWIN --> PLAN
    FAISS --> PLAN
    PLAN --> SQL
    PLAN --> MONGO
    SQL --> PG
    MONGO --> MDB
    PG --> FUSE
    MDB --> FUSE
    FUSE --> VIS
    FUSE --> HEAL
    HEAL --> TWIN
    HEAL --> PLAN
    VIS --> FE
```

---

# 40. Self-Healing State Diagram

```mermaid
stateDiagram-v2
    [*] --> Generate
    Generate --> Execute
    Execute --> Success
    Execute --> Error
    Error --> Diagnose
    Diagnose --> RetrieveSchema
    RetrieveSchema --> Repair
    Repair --> Execute
    Execute --> MaxAttempts: repeated failure
    MaxAttempts --> Failure
    Success --> [*]
    Failure --> [*]
```

---

# 41. Repository Strategy

Before writing new code, Claude Code must:

1. Read the complete repository tree.
2. Read every source file relevant to frontend/backend.
3. Read package files.
4. Read environment/config files.
5. Read existing prompts.
6. Read existing SQL-generation logic.
7. Read README.
8. Identify what is already implemented.
9. Run the current project.
10. Identify what can be reused.
11. Avoid rewriting working components unnecessarily.

The attached README confirms the current frontend uses Create React App, but the exact backend/source tree was not available in the attached documentation. Therefore the actual repository inspection is mandatory.

---

# 42. Recommended Development Order

Never attempt to implement everything simultaneously.

Use this sequence:

```text
Existing project
      |
      v
Stabilize
      |
      v
LLM abstraction
      |
      v
Database connection abstraction
      |
      v
Semantic Twin
      |
      v
Planner
      |
      v
SQL + Mongo generation
      |
      v
Execution
      |
      v
Self-healing
      |
      v
Hybrid execution
      |
      v
Database management
      |
      v
Forms
      |
      v
Visualization
      |
      v
Docker
      |
      v
Cloud deployment
      |
      v
Evaluation
```

---

# 43. Testing Requirements

Create unit tests for:

- SQL schema extraction.
- Mongo schema extraction.
- Embedding/retrieval.
- Planner output validation.
- SQL query parsing.
- Mongo pipeline validation.
- Error classification.
- Repair logic.
- Hybrid result merging.
- Dynamic form generation.

Create integration tests for:

```text
Prompt -> Planner -> Generator -> Database -> Result
```

and:

```text
Prompt -> Bad Query -> Database Error -> Repair -> Successful Result
```

Create end-to-end tests for:

- SQL query.
- Mongo query.
- Hybrid query.
- Table creation.
- CRUD.
- Visualization.
- Self-healing.

---

# 44. Logging

Use simple structured application logs.

Log:

- Request ID.
- Intent.
- Database type.
- Retrieved schema object IDs.
- Generated query.
- Execution duration.
- Error type.
- Repair attempt number.
- Final status.

Do not log:

- API keys.
- Passwords.
- Full connection strings.

This is normal application correctness/debugging, not an enterprise security subsystem.

---

# 45. Performance Considerations

The goal is not massive-scale production deployment.

Optimize only the important bottlenecks:

1. Do not send complete schemas to the LLM.
2. Use top-k semantic retrieval.
3. Limit database result sizes.
4. Avoid unnecessary LLM calls.
5. Use one planner call where possible.
6. Repair only when execution fails.
7. Use local FAISS.
8. Keep model selection configurable.

---

# 46. Research Novelty Framing

Do not claim:

> We invented Text-to-SQL.

Do not claim:

> We invented self-healing SQL.

Do not claim:

> We invented RAG for databases.

Those already exist in the literature.

The project should claim an evaluated **integrated framework** combining:

- Semantic schema representation across relational and document databases.
- Cross-database planning/routing.
- SQL and MongoDB generation.
- Execution-grounded repair across both database paradigms.
- Application-level hybrid result fusion.
- Natural-language schema/database management.
- Dynamic schema-driven forms.
- Cloud deployment and empirical evaluation.

The attached literature review identifies related work including Text2VectorSQL, Bridging the Gap, MAGIC, SQL Query Engine, AWS's RAG/self-correction architecture, SQL-of-Thought, DBCopilot, QCMA-SQL, CHASE-SQL, and ExCoT-DPO. The documented common gaps are single-database scope, limited semantic schema modeling, limited live execution repair, lack of cross-database planning, query-only interaction, and lack of an integrated architecture.

---

# 47. Paper Evaluation Design

The final paper should include:

## Baselines

- Existing/original SQL bot.
- Raw-schema LLM prompting.
- Semantic retrieval without planner.
- Planner without self-healing.
- Full framework.

## Dataset/task groups

```text
SQL
MongoDB
Hybrid
Schema Management
Self-Healing
```

## Report

```text
Accuracy
First-attempt success
Repair success
Hybrid success
Latency
Retrieval precision
LLM calls
Token usage
```

## Ablation

```text
Full system
- Semantic Twin
- Planner
- Self-Healing
- Hybrid execution
```

The goal is to demonstrate which modules contribute to measurable improvements.

---

# 48. Definition of Done

The project is complete when all of the following work:

- [ ] Existing SQL bot functionality still works.
- [ ] Gemini API is integrated through a clean abstraction.
- [ ] PostgreSQL schema introspection works.
- [ ] MongoDB schema introspection works.
- [ ] Semantic Database Twin is generated.
- [ ] FAISS retrieval works.
- [ ] Intent analysis works.
- [ ] Universal Query Planner works.
- [ ] SQL generation works.
- [ ] MongoDB generation works.
- [ ] SQL execution works.
- [ ] MongoDB execution works.
- [ ] Hybrid execution works.
- [ ] Self-healing works for representative SQL errors.
- [ ] Self-healing works for representative MongoDB errors.
- [ ] Repair attempts are bounded.
- [ ] Database/table/collection creation works.
- [ ] CRUD works.
- [ ] Dynamic forms work.
- [ ] Semantic Twin refresh works after schema changes.
- [ ] Results can be visualized.
- [ ] Generated queries can be explained.
- [ ] Docker deployment works.
- [ ] AWS EC2 deployment works.
- [ ] Evaluation dataset exists.
- [ ] Baselines exist.
- [ ] Ablation experiments exist.
- [ ] Results are recorded for the research paper.

---

# 49. Important Implementation Principle

**Do not build features merely because they appear in the architecture diagram.**

Every module must have:

1. A concrete purpose.
2. An input.
3. An output.
4. A test.
5. A connection to another module.

If a component is not needed for the working prototype, do not add it.

---

# 50. Claude Code Working Rules

Claude Code must:

1. Inspect first.
2. Plan second.
3. Implement incrementally.
4. Run tests after each major change.
5. Never replace the existing project blindly.
6. Preserve working functionality.
7. Keep configuration environment-based.
8. Prefer simple architecture.
9. Avoid unnecessary cloud services.
10. Keep the LLM provider replaceable.
11. Use structured Pydantic outputs.
12. Use LangGraph for the multi-step workflow.
13. Keep database operations separate from LLM reasoning.
14. Never let the LLM directly execute arbitrary Python.
15. Never invent schema elements when the Semantic Twin lacks them.
16. Refresh semantic metadata after schema changes.
17. Bound self-healing retries.
18. Document major implementation decisions.
19. Add tests with each major feature.
20. Update the README as the implementation evolves.

---

# 51. Final End-to-End Architecture

```text
                         USER
                           |
                           v
                React Natural Language UI
                           |
                           v
                     FastAPI API
                           |
                           v
                  LangGraph Workflow
                           |
                           v
                  Intent Analysis
                           |
                           v
               Semantic Database Twin
              /           |            \
             /            |             \
      SQL Metadata    Embeddings    Mongo Metadata
                          |
                     FAISS Retrieval
                          |
                          v
              Universal Query Planner
                   /            \
                  /              \
                 v                v
          SQL Generator     Mongo Generator
                 |                |
                 v                v
            PostgreSQL         MongoDB
                 \                /
                  \              /
                   v            v
                 Execution / Result Layer
                           |
                    Success?
                    /      \
                  Yes       No
                   |         |
                   |         v
                   |   Error Classification
                   |         |
                   |         v
                   |   Self-Healing Agent
                   |         |
                   |         v
                   |   Semantic Context
                   |         |
                   |         v
                   |      Re-plan
                   |         |
                   +---------+
                           |
                           v
                  Result Integration
                           |
              +------------+------------+
              |                         |
              v                         v
        Visualization             Explanation
              |                         |
              +------------+------------+
                           |
                           v
                         USER
```

---

# 52. Final Project Definition

The completed system should be a practical cloud-deployed research prototype in which a user can interact with PostgreSQL and MongoDB using natural language. The system should understand the semantic structure of both databases, retrieve relevant schema context, plan the required operation, generate the appropriate SQL or MongoDB operation, execute it, repair failures using real database feedback, combine results for hybrid requests, manage database structures through natural language, generate forms from schemas, and present results through tables, visualizations, and explanations.

The architecture should remain intentionally simple because this is a single-user academic system. The research value comes from the **integration and measurable evaluation of semantic schema understanding, cross-database planning, execution-grounded self-healing, and natural-language database management**, not from adding enterprise infrastructure.
