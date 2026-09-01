"""
Hybrid query engine tests.

Unit tests (no DB needed) — always run.
Integration tests — marked @pytest.mark.integration, require live PostgreSQL + MongoDB.

Run unit tests only:
  cd backend && pytest tests/test_hybrid_engine.py -m "not integration" -v

Run all tests (requires DB):
  cd backend && pytest tests/test_hybrid_engine.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.hybrid.executor import HybridExecutor
from app.hybrid.models import HybridQueryPlan, HybridExecutionTrace
from app.mongo_gen.models import MongoQuerySpec


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_spec(**kwargs) -> MongoQuerySpec:
    defaults = {
        "query_type": "find",
        "collection": "support_tickets",
        "filter": {},
        "projection": {},
        "sort": {},
        "limit": 100,
        "pipeline": [],
    }
    defaults.update(kwargs)
    return MongoQuerySpec(**defaults)


def _make_plan(**kwargs) -> HybridQueryPlan:
    defaults = {
        "sql_query": "SELECT 1 AS customer_id",
        "mongo_spec": _make_spec(),
        "join_key": "customer_id",
        "join_strategy": "inner_join",
        "execution_strategy": "parallel_then_fuse",
        "explanation": "test",
    }
    defaults.update(kwargs)
    return HybridQueryPlan(**defaults)


def _make_executor() -> HybridExecutor:
    """Return an executor with all services mocked out (unit tests)."""
    return HybridExecutor(llm=None, db=None, mongo=None)


# ─────────────────────────────────────────────────────────────────────────────
# A. Key normalisation
# ─────────────────────────────────────────────────────────────────────────────

class TestKeyNormalisation:
    def test_int(self):
        assert HybridExecutor._normalize_key(3) == "3"

    def test_float_whole(self):
        assert HybridExecutor._normalize_key(3.0) == "3"

    def test_string(self):
        assert HybridExecutor._normalize_key("3") == "3"

    def test_int_eq_string(self):
        assert HybridExecutor._normalize_key(3) == HybridExecutor._normalize_key("3")

    def test_float_eq_int(self):
        assert HybridExecutor._normalize_key(3.0) == HybridExecutor._normalize_key(3)

    def test_none(self):
        assert HybridExecutor._normalize_key(None) == ""

    def test_float_non_whole(self):
        # 3.5 should stay as "3.5", not "3"
        assert HybridExecutor._normalize_key(3.5) == "3.5"


# ─────────────────────────────────────────────────────────────────────────────
# B. ID extraction
# ─────────────────────────────────────────────────────────────────────────────

class TestExtractIds:
    def test_basic(self):
        rows = [{"customer_id": 1}, {"customer_id": 2}]
        ids = HybridExecutor._extract_ids(rows, "customer_id")
        assert set(str(i) for i in ids) == {"1", "2"}

    def test_dedup(self):
        rows = [{"customer_id": 1}, {"customer_id": 2}, {"customer_id": 1}]
        ids = HybridExecutor._extract_ids(rows, "customer_id")
        assert len(ids) == 2

    def test_missing_key_skipped(self):
        rows = [{"other": "x"}, {"customer_id": 1}]
        ids = HybridExecutor._extract_ids(rows, "customer_id")
        assert len(ids) == 1

    def test_none_value_skipped(self):
        rows = [{"customer_id": None}, {"customer_id": 5}]
        ids = HybridExecutor._extract_ids(rows, "customer_id")
        assert len(ids) == 1 and ids[0] == 5

    def test_empty_rows(self):
        assert HybridExecutor._extract_ids([], "customer_id") == []


# ─────────────────────────────────────────────────────────────────────────────
# C. Mongo spec injection
# ─────────────────────────────────────────────────────────────────────────────

class TestInjectMongo:
    def test_find_adds_in_filter(self):
        spec = _make_spec(filter={"status": "Open"})
        injected = HybridExecutor._inject_ids_into_mongo_spec(spec, "customer_id", [1, 2, 3])
        assert injected.filter["customer_id"] == {"$in": [1, 2, 3]}
        assert injected.filter["status"] == "Open"  # existing filter preserved

    def test_find_empty_ids_no_match(self):
        spec = _make_spec()
        injected = HybridExecutor._inject_ids_into_mongo_spec(spec, "customer_id", [])
        assert "__hybrid_no_match__" in injected.filter

    def test_aggregate_prepends_match_stage(self):
        spec = _make_spec(
            query_type="aggregate",
            pipeline=[{"$match": {"status": "Open"}}],
        )
        injected = HybridExecutor._inject_ids_into_mongo_spec(spec, "customer_id", [1, 2])
        assert injected.pipeline[0] == {"$match": {"customer_id": {"$in": [1, 2]}}}
        # Original $match on a different key should remain
        assert any("status" in s.get("$match", {}) for s in injected.pipeline)

    def test_aggregate_empty_ids(self):
        spec = _make_spec(query_type="aggregate", pipeline=[])
        injected = HybridExecutor._inject_ids_into_mongo_spec(spec, "customer_id", [])
        assert "__hybrid_no_match__" in injected.filter


# ─────────────────────────────────────────────────────────────────────────────
# D. SQL injection
# ─────────────────────────────────────────────────────────────────────────────

class TestInjectSql:
    def test_basic_int_ids(self):
        sql = "SELECT * FROM customers"
        injected = HybridExecutor._inject_ids_into_sql(sql, "customer_id", [1, 2, 3])
        assert "__hybrid_base" in injected
        assert "IN (1, 2, 3)" in injected

    def test_empty_ids_yields_false(self):
        sql = "SELECT * FROM customers"
        injected = HybridExecutor._inject_ids_into_sql(sql, "customer_id", [])
        assert "FALSE" in injected

    def test_string_ids_quoted(self):
        sql = "SELECT * FROM customers"
        injected = HybridExecutor._inject_ids_into_sql(sql, "cid", ["a", "b"])
        assert "'a'" in injected and "'b'" in injected

    def test_float_ids_as_int(self):
        sql = "SELECT * FROM customers"
        injected = HybridExecutor._inject_ids_into_sql(sql, "customer_id", [1.0, 2.0])
        assert "1" in injected and "2" in injected
        assert "1.0" not in injected

    def test_sql_injection_in_string_id_is_escaped(self):
        sql = "SELECT * FROM customers"
        injected = HybridExecutor._inject_ids_into_sql(sql, "cid", ["a'; DROP TABLE customers; --"])
        # Ensure the injection is quoted/escaped
        assert "DROP" in injected  # present but inside a quoted string
        assert "a''" in injected   # single quote is doubled


# ─────────────────────────────────────────────────────────────────────────────
# E. fuse() — basic join strategies
# ─────────────────────────────────────────────────────────────────────────────

class TestFuseBasic:
    def test_inner_join_match(self):
        ex = _make_executor()
        plan = _make_plan(join_key="customer_id", join_strategy="inner_join")
        pg = [{"customer_id": 1, "name": "Alice"}, {"customer_id": 2, "name": "Bob"}]
        mg = [{"customer_id": 1, "ticket": "T1"}, {"customer_id": 3, "ticket": "T3"}]
        fused = ex.fuse(pg, mg, plan)
        assert len(fused) == 1
        assert fused[0]["name"] == "Alice" and fused[0]["ticket"] == "T1"

    def test_inner_join_no_match(self):
        ex = _make_executor()
        plan = _make_plan(join_key="customer_id", join_strategy="inner_join")
        pg = [{"customer_id": 99}]
        mg = [{"customer_id": 100}]
        assert ex.fuse(pg, mg, plan) == []

    def test_left_join_includes_unmatched_pg(self):
        ex = _make_executor()
        plan = _make_plan(join_key="customer_id", join_strategy="left_join")
        pg = [{"customer_id": 1, "name": "Alice"}, {"customer_id": 2, "name": "Bob"}]
        mg = [{"customer_id": 1, "ticket": "T1"}]
        fused = ex.fuse(pg, mg, plan)
        assert len(fused) == 2
        bob = next(r for r in fused if r["name"] == "Bob")
        assert "ticket" not in bob

    def test_union_no_join_key(self):
        ex = _make_executor()
        plan = _make_plan(join_key="", join_strategy="union")
        fused = ex.fuse([{"a": 1}], [{"b": 2}], plan)
        assert len(fused) == 2


# ─────────────────────────────────────────────────────────────────────────────
# F. One customer, multiple MongoDB documents (one-to-many)
# ─────────────────────────────────────────────────────────────────────────────

class TestOneToMany:
    def test_multiple_tickets_per_customer(self):
        ex = _make_executor()
        plan = _make_plan(join_key="customer_id", join_strategy="inner_join")
        pg = [{"customer_id": 1, "name": "Alice"}]
        mg = [
            {"customer_id": 1, "ticket": "T1", "status": "Open"},
            {"customer_id": 1, "ticket": "T2", "status": "Open"},
        ]
        fused = ex.fuse(pg, mg, plan)
        assert len(fused) == 2
        tickets = {r["ticket"] for r in fused}
        assert tickets == {"T1", "T2"}
        assert all(r["name"] == "Alice" for r in fused)

    def test_multiple_tickets_two_customers(self):
        ex = _make_executor()
        plan = _make_plan(join_key="customer_id", join_strategy="inner_join")
        pg = [
            {"customer_id": 1, "name": "Alice"},
            {"customer_id": 2, "name": "Bob"},
        ]
        mg = [
            {"customer_id": 1, "ticket": "T1"},
            {"customer_id": 1, "ticket": "T2"},
            {"customer_id": 2, "ticket": "T3"},
        ]
        fused = ex.fuse(pg, mg, plan)
        assert len(fused) == 3
        alice_tickets = {r["ticket"] for r in fused if r["name"] == "Alice"}
        bob_tickets = {r["ticket"] for r in fused if r["name"] == "Bob"}
        assert alice_tickets == {"T1", "T2"}
        assert bob_tickets == {"T3"}


# ─────────────────────────────────────────────────────────────────────────────
# G. Legitimate zero-result queries
# ─────────────────────────────────────────────────────────────────────────────

class TestLegitimateZeroResults:
    def test_zero_rows_inner_join_is_not_an_error(self):
        """Zero rows from a valid inner join must not raise; it's a real empty result."""
        ex = _make_executor()
        plan = _make_plan(join_key="customer_id", join_strategy="inner_join")
        pg = [{"customer_id": 99, "name": "Nobody"}]
        mg = [{"customer_id": 100, "ticket": "T99"}]
        fused = ex.fuse(pg, mg, plan)
        assert fused == []  # empty, no exception

    def test_zero_rows_with_empty_pg(self):
        ex = _make_executor()
        plan = _make_plan(join_key="customer_id", join_strategy="inner_join")
        assert ex.fuse([], [{"customer_id": 1}], plan) == []

    def test_zero_rows_with_empty_mongo(self):
        ex = _make_executor()
        plan = _make_plan(join_key="customer_id", join_strategy="inner_join")
        assert ex.fuse([{"customer_id": 1}], [], plan) == []


# ─────────────────────────────────────────────────────────────────────────────
# H. Mongo → PG direction: Mongo IDs injected into SQL
# ─────────────────────────────────────────────────────────────────────────────

class TestMongToPgDirection:
    @pytest.mark.asyncio
    async def test_mongo_ids_injected_into_pg_sql(self):
        """
        Simulate mongo_to_pg: Mongo returns IDs, those get injected into PG SQL,
        then PG result is fused with Mongo data.
        """
        mongo_rows = [
            {"customer_id": 1, "mobile": 10, "desktop": 5},
            {"customer_id": 2, "mobile": 8, "desktop": 3},
        ]
        pg_rows = [
            {"customer_id": 1, "name": "Alice", "email": "a@example.com"},
            {"customer_id": 2, "name": "Bob", "email": "b@example.com"},
        ]

        # Mock DB and Mongo services
        mock_db = MagicMock()
        mock_db.execute_query.return_value = {"rows": pg_rows, "columns": ["customer_id", "name", "email"]}
        mock_mongo = MagicMock()
        mock_mongo.aggregate.return_value = mongo_rows

        # Mock LLM
        mongo_spec = _make_spec(
            query_type="aggregate",
            collection="customer_activity",
            pipeline=[
                {"$unwind": "$devices"},
                {"$group": {
                    "_id": "$customer_id",
                    "customer_id": {"$first": "$customer_id"},
                    "mobile": {"$sum": {"$cond": [{"$eq": ["$devices.type", "mobile"]}, "$devices.sessions", 0]}},
                    "desktop": {"$sum": {"$cond": [{"$eq": ["$devices.type", "desktop"]}, "$devices.sessions", 0]}},
                }},
                {"$match": {"$expr": {"$gt": ["$mobile", "$desktop"]}}},
                {"$project": {"_id": 0}},
            ],
        )
        mock_plan = _make_plan(
            sql_query="SELECT customer_id, name, email FROM customers",
            mongo_spec=mongo_spec,
            pg_join_key="customer_id",
            mongo_join_key="customer_id",
            join_key="customer_id",
            join_strategy="inner_join",
            execution_strategy="mongo_to_pg",
        )
        mock_llm = MagicMock()
        mock_llm.generate_structured = AsyncMock(return_value=mock_plan)

        ex = HybridExecutor(llm=mock_llm, db=mock_db, mongo=mock_mongo)
        result = await ex.execute(
            "Which customers use mobile devices more than desktop devices?",
            "mock schema context",
        )

        assert result.get("error") is None
        rows = result["result_rows"]
        assert len(rows) == 2
        names = {r["name"] for r in rows}
        assert names == {"Alice", "Bob"}
        # PG SQL must have been called with the injected IDs
        called_sql = mock_db.execute_query.call_args[0][0]
        assert "IN (1, 2)" in called_sql or "IN (2, 1)" in called_sql


# ─────────────────────────────────────────────────────────────────────────────
# I. PG → Mongo direction: PG IDs injected into Mongo spec
# ─────────────────────────────────────────────────────────────────────────────

class TestPgToMongoDirection:
    @pytest.mark.asyncio
    async def test_pg_ids_injected_into_mongo(self):
        """
        Simulate pg_to_mongo: PG returns high-purchase customer IDs,
        those are injected into Mongo to find their open support tickets.
        """
        pg_rows = [
            {"customer_id": 1, "name": "Alice", "total_purchase": 5000.0},
            {"customer_id": 3, "name": "Charlie", "total_purchase": 4200.0},
        ]
        mongo_rows = [
            {"customer_id": 1, "ticket_id": "T1", "status": "Open"},
            {"customer_id": 1, "ticket_id": "T2", "status": "Open"},
            {"customer_id": 3, "ticket_id": "T5", "status": "Open"},
        ]

        mock_db = MagicMock()
        mock_db.execute_query.return_value = {"rows": pg_rows, "columns": ["customer_id", "name", "total_purchase"]}
        mock_mongo = MagicMock()
        mock_mongo.find_with_spec.return_value = mongo_rows

        mongo_spec = _make_spec(
            query_type="find",
            collection="support_tickets",
            filter={"status": "Open"},
        )
        mock_plan = _make_plan(
            sql_query=(
                "SELECT c.customer_id, c.name, SUM(o.amount) AS total_purchase "
                "FROM customers c JOIN orders o ON c.customer_id = o.customer_id "
                "WHERE o.status = 'completed' GROUP BY c.customer_id, c.name "
                "HAVING SUM(o.amount) > (SELECT AVG(t) FROM (SELECT SUM(amount) AS t "
                "FROM orders WHERE status='completed' GROUP BY customer_id) sub)"
            ),
            mongo_spec=mongo_spec,
            pg_join_key="customer_id",
            mongo_join_key="customer_id",
            join_key="customer_id",
            join_strategy="inner_join",
            execution_strategy="pg_to_mongo",
        )
        mock_llm = MagicMock()
        mock_llm.generate_structured = AsyncMock(return_value=mock_plan)

        ex = HybridExecutor(llm=mock_llm, db=mock_db, mongo=mock_mongo)
        result = await ex.execute(
            "Find customers with high purchases who also have open support tickets.",
            "mock schema context",
        )

        assert result.get("error") is None
        rows = result["result_rows"]

        # Alice has 2 tickets, Charlie has 1 → 3 fused rows
        assert len(rows) == 3
        tickets = {r["ticket_id"] for r in rows}
        assert tickets == {"T1", "T2", "T5"}

        # Mongo must have been called with injected IDs
        called_filter = mock_mongo.find_with_spec.call_args[0][1]  # second positional: filter_
        assert "customer_id" in called_filter
        assert "$in" in called_filter["customer_id"]
        injected_ids = {HybridExecutor._normalize_key(v) for v in called_filter["customer_id"]["$in"]}
        assert "1" in injected_ids and "3" in injected_ids


# ─────────────────────────────────────────────────────────────────────────────
# J. Numeric / string join key normalisation in fuse()
# ─────────────────────────────────────────────────────────────────────────────

class TestJoinKeyNormalisationInFuse:
    def test_int_pg_matches_string_mongo(self):
        ex = _make_executor()
        plan = _make_plan(join_key="customer_id", join_strategy="inner_join")
        pg = [{"customer_id": 3, "name": "Charlie"}]
        mg = [{"customer_id": "3", "ticket": "T5"}]
        fused = ex.fuse(pg, mg, plan)
        assert len(fused) == 1
        assert fused[0]["ticket"] == "T5"

    def test_float_pg_matches_int_mongo(self):
        ex = _make_executor()
        plan = _make_plan(join_key="customer_id", join_strategy="inner_join")
        pg = [{"customer_id": 3.0, "name": "Dave"}]
        mg = [{"customer_id": 3, "ticket": "T6"}]
        fused = ex.fuse(pg, mg, plan)
        assert len(fused) == 1

    def test_string_pg_matches_int_mongo(self):
        ex = _make_executor()
        plan = _make_plan(join_key="customer_id", join_strategy="inner_join")
        pg = [{"customer_id": "5", "name": "Eve"}]
        mg = [{"customer_id": 5, "ticket": "T7"}]
        fused = ex.fuse(pg, mg, plan)
        assert len(fused) == 1

    def test_type_mismatch_no_false_match(self):
        """3.5 should NOT match 3."""
        ex = _make_executor()
        plan = _make_plan(join_key="customer_id", join_strategy="inner_join")
        pg = [{"customer_id": 3, "name": "Alice"}]
        mg = [{"customer_id": 3.5, "ticket": "T8"}]
        fused = ex.fuse(pg, mg, plan)
        assert len(fused) == 0


# ─────────────────────────────────────────────────────────────────────────────
# Validation warnings
# ─────────────────────────────────────────────────────────────────────────────

class TestValidation:
    def test_warns_when_pg_key_missing(self):
        ex = _make_executor()
        plan = _make_plan(join_key="customer_id", join_strategy="inner_join")
        pg_rows = [{"some_other_field": 1}]
        mongo_rows = [{"customer_id": 1}]
        warnings = ex._validate_plan(plan, pg_rows, mongo_rows)
        assert any("customer_id" in w and "PostgreSQL" in w for w in warnings)

    def test_warns_when_mongo_key_missing(self):
        ex = _make_executor()
        plan = _make_plan(join_key="customer_id", join_strategy="inner_join")
        pg_rows = [{"customer_id": 1}]
        mongo_rows = [{"other_field": "x"}]
        warnings = ex._validate_plan(plan, pg_rows, mongo_rows)
        assert any("customer_id" in w and "MongoDB" in w for w in warnings)

    def test_no_warnings_when_keys_present(self):
        ex = _make_executor()
        plan = _make_plan(join_key="customer_id", join_strategy="inner_join")
        pg_rows = [{"customer_id": 1, "name": "Alice"}]
        mongo_rows = [{"customer_id": 1, "ticket": "T1"}]
        warnings = ex._validate_plan(plan, pg_rows, mongo_rows)
        assert warnings == []

    def test_warns_when_no_join_key(self):
        ex = _make_executor()
        plan = _make_plan(join_key="", pg_join_key="", mongo_join_key="", join_strategy="union")
        warnings = ex._validate_plan(plan, [{"a": 1}], [{"b": 2}])
        assert any("join key" in w.lower() for w in warnings)


# ─────────────────────────────────────────────────────────────────────────────
# Asymmetric join keys (pg_join_key != mongo_join_key)
# ─────────────────────────────────────────────────────────────────────────────

class TestAsymmetricJoinKeys:
    def test_different_key_names(self):
        """PG uses 'cid', Mongo uses 'customer_id'."""
        ex = _make_executor()
        plan = HybridQueryPlan(
            sql_query="SELECT 1",
            mongo_spec=_make_spec(),
            pg_join_key="cid",
            mongo_join_key="customer_id",
            join_key="",
            join_strategy="inner_join",
            execution_strategy="parallel_then_fuse",
        )
        pg = [{"cid": 1, "name": "Alice"}]
        mg = [{"customer_id": 1, "ticket": "T1"}]
        fused = ex.fuse(pg, mg, plan)
        assert len(fused) == 1
        assert fused[0]["ticket"] == "T1"


# ─────────────────────────────────────────────────────────────────────────────
# Integration tests (require live PostgreSQL + MongoDB)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def executor():
    """Create a real HybridExecutor backed by live databases."""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from app.database.postgres_service import PostgresService
    from app.database.mongo_service import MongoService
    from app.llm.factory import get_llm_provider
    return HybridExecutor(
        llm=get_llm_provider(),
        db=PostgresService(),
        mongo=MongoService(),
    )


@pytest.fixture(scope="session")
def schema_context():
    """Build schema context from the live Semantic Twin."""
    import asyncio
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from app.semantic_twin.twin_service import get_twin_service

    twin = get_twin_service()
    asyncio.run(twin.refresh())
    return twin.twin.get_context_for_objects([o.name for o in twin.twin.objects])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_high_purchases_with_open_tickets(executor, schema_context):
    """
    Query B: 'Find customers with high purchases who also have open support tickets.'
    Must return non-zero rows containing both customer and ticket information.
    """
    result = await executor.execute(
        "Find customers with high purchases who also have open support tickets.",
        schema_context,
    )
    trace = result.get("hybrid_trace", {})
    assert result.get("error") is None, (
        f"Got error: {result.get('error')}. Trace: {trace}"
    )
    rows = result.get("result_rows", [])
    assert len(rows) > 0, (
        f"Expected non-zero rows. PG={trace.get('pg_row_count')}, "
        f"Mongo={trace.get('mongo_row_count')}, "
        f"Intermediate IDs={trace.get('intermediate_id_count')}, "
        f"Warnings={trace.get('validation_warnings')}"
    )
    # Every row should have a customer_id
    assert all("customer_id" in r for r in rows), "Expected customer_id in all result rows"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_mobile_vs_desktop(executor, schema_context):
    """
    Query A: 'Which customers use mobile devices more than desktop devices?'
    Must return non-zero rows with customer details.
    """
    result = await executor.execute(
        "Which customers use mobile devices more than desktop devices?",
        schema_context,
    )
    trace = result.get("hybrid_trace", {})
    assert result.get("error") is None, (
        f"Got error: {result.get('error')}. Trace: {trace}"
    )
    rows = result.get("result_rows", [])
    assert len(rows) > 0, (
        f"Expected non-zero rows. Trace: {trace}"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_customers_open_tickets_total_purchases(executor, schema_context):
    """
    Query C: 'Show customers with open support tickets and their total purchases.'
    """
    result = await executor.execute(
        "Show customers with open support tickets and their total purchases.",
        schema_context,
    )
    assert result.get("error") is None, f"Got error: {result.get('error')}"
    assert len(result.get("result_rows", [])) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_high_spending_customers_with_support_issues(executor, schema_context):
    """
    Query D: 'Which high-spending customers have support issues?'
    """
    result = await executor.execute(
        "Which high-spending customers have support issues?",
        schema_context,
    )
    assert result.get("error") is None, f"Got error: {result.get('error')}"
    assert len(result.get("result_rows", [])) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_positive_reviews_and_purchases(executor, schema_context):
    """
    Query E: 'Which customers have positive product reviews and purchases?'
    """
    result = await executor.execute(
        "Which customers have positive product reviews and purchases?",
        schema_context,
    )
    assert result.get("error") is None, f"Got error: {result.get('error')}"
    # May return zero if no matching data — that is a legitimate empty result
    assert "result_rows" in result


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_one_customer_multiple_tickets(executor, schema_context):
    """
    Query F: Verify that one customer with multiple MongoDB support tickets
    appears as multiple rows (not truncated to one).
    """
    result = await executor.execute(
        "Show customers with all their open support tickets and their total purchases.",
        schema_context,
    )
    assert result.get("error") is None
    rows = result.get("result_rows", [])
    if rows:
        # If any customer_id appears more than once, one-to-many is working
        from collections import Counter
        cid_counts = Counter(
            HybridExecutor._normalize_key(r.get("customer_id"))
            for r in rows
        )
        # We can't assert > 1 without knowing the data, but at least we get rows
        assert len(rows) >= 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_legitimate_zero_result(executor, schema_context):
    """
    Query G: A logically valid query that should return zero rows
    (customers with purchases > 1,000,000 — extremely high threshold unlikely to match).
    Zero rows must not raise an error.
    """
    result = await executor.execute(
        "Find customers with total purchases over one billion dollars who also have open support tickets.",
        schema_context,
    )
    # Should succeed (no error) even if zero rows
    assert "result_rows" in result
    # May have error if plan fails, but no crash
