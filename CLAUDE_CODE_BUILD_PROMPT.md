# Claude Code Master Build Prompt

You are working on an existing repository that implements an LLM-based SQL bot.

Your task is to transform the existing project into the complete **Unified AI Database Copilot** research prototype described in `UNIFIED_AI_DATABASE_PROJECT_GUIDE.md`.

## FIRST: DO NOT CODE IMMEDIATELY

Before changing anything:

1. Read `UNIFIED_AI_DATABASE_PROJECT_GUIDE.md` completely.
2. Read the repository README completely.
3. Recursively inspect the entire repository.
4. Read all source files, configuration files, package manifests, prompts, and existing database/LLM code.
5. Identify the current frontend architecture and existing backend architecture.
6. Run the current application if possible.
7. Run the current frontend build/test commands.
8. Identify exactly what the existing SQL bot already implements.
9. Create a short implementation plan based on the actual repository.
10. Preserve working functionality instead of rewriting it unnecessarily.

The attached project documentation states that the current frontend was bootstrapped with Create React App. Confirm this from the actual repository before making frontend changes.

## IMPORTANT PROJECT CONSTRAINTS

This is a single-user academic project.

Do NOT add:

- Authentication.
- IAM.
- Role-based access control.
- Multi-tenancy.
- CDN.
- CloudFront.
- Redis.
- Kubernetes.
- ECS/EKS.
- Auto-scaling.
- Load balancing.
- Enterprise security architecture.
- Complex monitoring.
- Bedrock for the database LLM.

The database LLM must use the Gemini API, not AWS Bedrock.

Use the official Python `google-genai` SDK.

Make the model configurable:

```env
GEMINI_MODEL=gemini-3.7-flash
```

Do not hard-code a model in application logic.

Keep the architecture simple and modular.

## TARGET SYSTEM

Build these major capabilities:

1. Natural-language SQL querying.
2. Natural-language MongoDB querying.
3. Semantic Database Twin.
4. FAISS + Sentence Transformers schema retrieval.
5. Universal Cross-Database Query Planner.
6. SQL query generation.
7. MongoDB query/pipeline generation.
8. SQL + MongoDB hybrid execution.
9. Autonomous execution-grounded self-healing.
10. Natural-language database/table/collection creation.
11. CRUD operations.
12. Schema-driven dynamic forms.
13. Result visualization.
14. Natural-language explanations.
15. Docker deployment.
16. AWS EC2 deployment.

## CORE ARCHITECTURE

Implement this logical flow:

```text
User
 |
React UI
 |
FastAPI
 |
LangGraph
 |
Intent Analysis
 |
Semantic Database Twin
 |
FAISS/Sentence Transformers retrieval
 |
Universal Cross-Database Query Planner
 |                    |
SQL Generator     Mongo Generator
 |                    |
PostgreSQL          MongoDB
 \                    /
  \                  /
   Execution / Result Layer
            |
       Success?
       /     \
     Yes      No
      |        |
      |    Error Classification
      |        |
      |    Self-Healing Agent
      |        |
      |      Repair
      |        |
      +---- Re-plan/Execute
      |
Result Integration
 |
Visualization + Explanation
 |
React UI
```

## IMPLEMENTATION ORDER

Implement incrementally in this order.

### Phase 1 — Existing project stabilization

- Inspect current code.
- Run it.
- Preserve existing SQL bot.
- Refactor only where needed.
- Establish a clean backend/LLM abstraction if the current implementation does not already have one.

### Phase 2 — Gemini integration

Create a provider abstraction.

Example conceptual interface:

```python
class LLMProvider:
    def generate_structured(...):
        ...
```

Implement Gemini through `google-genai`.

Use environment variables.

Do not scatter Gemini API calls throughout the codebase.

### Phase 3 — Database abstraction

Implement clean database services for:

- PostgreSQL via SQLAlchemy/psycopg.
- MongoDB via PyMongo.

The execution layer must be independent from the LLM layer.

### Phase 4 — Semantic Database Twin

Implement:

- PostgreSQL introspection.
- MongoDB introspection.
- Unified metadata models.
- Relationship mapping.
- Mongo nested document mapping.
- Semantic descriptions.
- Embedding generation.
- FAISS index.
- Top-k retrieval.
- Refresh operation.

The Semantic Twin must represent both SQL and MongoDB.

Do not send complete schemas to the LLM unnecessarily.

### Phase 5 — Intent Analysis

Create a structured Pydantic `IntentResult`.

Support at least:

```text
query
crud
schema_management
database_creation
table_creation
collection_creation
visualization
explanation
hybrid_query
```

### Phase 6 — Universal Query Planner

Create a structured Pydantic `QueryPlan`.

The planner must decide:

- SQL.
- MongoDB.
- Hybrid.
- Relevant objects.
- Operations.
- Whether result integration is needed.

Use LangGraph to orchestrate the workflow.

### Phase 7 — SQL Generator

Generate SQL using only retrieved schema context.

Support:

- filtering.
- aggregation.
- grouping.
- sorting.
- joins.
- nested queries where appropriate.

Use SQLGlot for parsing/validation where useful, but use actual PostgreSQL execution as the final validation.

### Phase 8 — Mongo Generator

Generate:

- find operations.
- aggregation pipelines.
- CRUD operations.

Use the retrieved Mongo schema.

Handle nested document paths and arrays.

### Phase 9 — Execution

Implement:

```text
SQLExecutor
MongoExecutor
HybridExecutor
```

Hybrid execution must happen at the application level.

Do not pretend PostgreSQL and MongoDB are one database.

### Phase 10 — Self-Healing

Implement:

```text
Generate
 -> Execute
 -> Error
 -> Diagnose
 -> Retrieve schema
 -> Repair
 -> Retry
```

Maximum retries must be configurable and default to 3.

The repair model receives:

- original request.
- generated query.
- database type.
- relevant schema.
- execution error.
- previous attempt.
- attempt number.

Store repair history in the response so the UI can display it.

### Phase 11 — Database Management

Implement natural-language:

- table creation.
- collection creation.
- schema generation.
- CRUD.

For destructive/schema-changing operations, require a simple confirmation in the UI.

This is a correctness feature, not an authentication feature.

### Phase 12 — Dynamic Forms

Generate React forms from returned schema.

Map:

```text
INTEGER -> number
TEXT -> text
BOOLEAN -> checkbox
DATE -> date
ENUM -> select
FOREIGN KEY -> select
```

Handle Mongo nested objects recursively where practical.

### Phase 13 — Visualization

Return structured visualization metadata.

Support at minimum:

- table.
- bar chart.
- line chart.
- KPI/summary.

Use Plotly on the frontend.

### Phase 14 — Docker

Create:

```text
Dockerfile
docker-compose.yml
.env.example
```

Prefer:

```text
frontend
backend
postgres
mongodb
```

FAISS can remain inside backend storage for the prototype.

### Phase 15 — AWS

Deploy to one Ubuntu EC2 instance.

Use Docker Compose.

Do not add ECS, EKS, CloudFront, load balancers, or auto-scaling.

### Phase 16 — Testing

Add:

- unit tests.
- integration tests.
- self-healing tests.
- SQL tests.
- Mongo tests.
- hybrid tests.
- database creation tests.
- dynamic-form tests.

Also create an evaluation dataset for the paper.

## REQUIRED RESEARCH EVALUATION

The final implementation must support experiments for:

- Query success rate.
- First-attempt success.
- Self-healing success.
- Average repair attempts.
- Hybrid query success.
- Schema retrieval relevance.
- Latency.
- LLM calls/token usage if available.

Create ablation modes:

```text
Baseline existing SQL bot
Raw schema + LLM
Semantic Twin only
Semantic Twin + Planner
Semantic Twin + Planner + Self-Healing
Full SQL + Mongo + Hybrid system
```

The system should make these evaluations reproducible.

## IMPORTANT CODE QUALITY RULES

- Use Pydantic for LLM structured outputs.
- Keep LLM calls isolated.
- Keep database execution isolated.
- Do not mix UI logic with database logic.
- Do not let the LLM execute arbitrary Python.
- Never invent database fields when they are absent from retrieved schema.
- Bound all repair loops.
- Keep result sizes bounded.
- Use configurable timeouts.
- Use environment variables for configuration.
- Do not commit secrets.
- Add tests as features are implemented.
- Update README/documentation as the architecture changes.

## IMPORTANT UI REQUIREMENTS

The final frontend should have:

1. Natural-language chat.
2. Database/source selector or database connection/setup.
3. Schema explorer.
4. Generated query display.
5. Execution status.
6. Self-healing/repair status.
7. Result table.
8. Visualization.
9. Natural-language explanation.
10. Dynamic forms for data insertion.
11. Database/table/collection creation workflow.

Do not add authentication pages.

## DATABASE REFRESH REQUIREMENT

Whenever a schema-changing operation succeeds:

```text
Create table/collection
        |
        v
Refresh Semantic Database Twin
        |
        v
Rebuild/update FAISS index
```

The newly created database objects must immediately become available to the planner.

## FAILURE HANDLING

Never return an opaque error such as:

```text
Something went wrong.
```

Return useful structured diagnostics to the UI.

For a failed repair after the retry limit:

```text
Status: Failed
Attempts: 3
Reason: ...
Suggested action: ...
```

## FINAL DELIVERABLES

When implementation is complete, the repository should contain:

- Working frontend.
- Working FastAPI backend.
- Gemini integration.
- SQL support.
- MongoDB support.
- Semantic Database Twin.
- FAISS retrieval.
- LangGraph planner.
- Self-healing workflow.
- Hybrid execution.
- Database management.
- Dynamic forms.
- Visualization.
- Docker configuration.
- AWS deployment instructions.
- Tests.
- Updated README.
- `.env.example`.
- Research evaluation scripts/dataset format.

## VERY IMPORTANT

Do not assume that the target architecture is already present.

The existing repository is the source of truth for what is currently implemented.

The project guide is the source of truth for what must eventually be built.

Therefore:

```text
Existing Code
     +
Project Guide
     |
     v
Inspect -> Plan -> Implement -> Test -> Integrate
```

Do not overwrite working code blindly.

After every major phase:

1. Run tests/build.
2. Fix regressions.
3. Explain what changed.
4. Continue to the next phase.

At the end, provide:

1. Final repository architecture.
2. List of implemented features.
3. Files created/modified.
4. Commands to run locally.
5. Docker commands.
6. AWS deployment commands.
7. Environment variables required.
8. Known limitations.
9. Recommended research experiments.
10. Any feature from the guide that could not be implemented and why.
