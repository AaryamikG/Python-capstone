import sqlite3
import time
from pathlib import Path

from enterprise_rag.agents.sql_guard import SQLValidationError, validate_sql
from enterprise_rag.llm.gemini_client import GeminiClient
from enterprise_rag.llm.prompts import build_sql_prompt, build_sql_retry_prompt
from enterprise_rag.logging_config import get_logger
from enterprise_rag.schemas import QuantitativeAnswer, SqlGenerationResult

logger = get_logger(__name__)


def _read_only_connection(sqlite_path: str) -> sqlite3.Connection:
    abs_path = Path(sqlite_path).resolve().as_posix()
    conn = sqlite3.connect(f"file:{abs_path}?mode=ro", uri=True)
    conn.execute("PRAGMA query_only = ON;")
    return conn


def introspect_schema(conn: sqlite3.Connection) -> str:
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    lines = []
    for (table,) in tables:
        cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
        col_desc = ", ".join(f"{c[1]} {c[2]}" for c in cols)
        lines.append(f"TABLE {table}({col_desc})")
    return "\n".join(lines)


class QuantitativeSQLAgent:
    """Translates a natural-language question into SQL against the SQLite database and executes it."""

    def __init__(self, llm_client: GeminiClient, sqlite_path: str):
        self._llm = llm_client
        self._sqlite_path = sqlite_path

    def answer(self, question: str) -> QuantitativeAnswer:
        start = time.perf_counter()
        conn = _read_only_connection(self._sqlite_path)
        try:
            schema = introspect_schema(conn)
            sql = self._generate_and_validate_sql(schema, question)

            try:
                columns, rows = self._execute(conn, sql)
            except sqlite3.Error as exc:
                logger.info(
                    "sql_execution_failed_retrying",
                    extra={"event_data": {"sql": sql, "error": str(exc)}},
                )
                sql = self._retry_sql(schema, sql, str(exc))
                try:
                    columns, rows = self._execute(conn, sql)
                except sqlite3.Error as exc2:
                    elapsed = (time.perf_counter() - start) * 1000
                    logger.error(
                        "sql_execution_failed_final",
                        extra={"event_data": {"sql": sql, "error": str(exc2), "execution_time_ms": elapsed}},
                    )
                    return QuantitativeAnswer(
                        answer=f"I couldn't translate that into a valid query: {exc2}",
                        sql=sql,
                        error=str(exc2),
                    )

            elapsed = (time.perf_counter() - start) * 1000
            logger.info(
                "quantitative_query_handled",
                extra={"event_data": {"sql": sql, "row_count": len(rows), "execution_time_ms": elapsed}},
            )
            return QuantitativeAnswer(
                answer=self._summarize(columns, rows),
                sql=sql,
                columns=columns,
                rows=rows,
            )
        except SQLValidationError as exc:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error(
                "sql_validation_failed",
                extra={"event_data": {"error": str(exc), "execution_time_ms": elapsed}},
            )
            return QuantitativeAnswer(
                answer=f"I couldn't generate a safe query for that question: {exc}",
                error=str(exc),
            )
        finally:
            conn.close()

    def _generate_and_validate_sql(self, schema: str, question: str) -> str:
        prompt = build_sql_prompt(schema, question)
        result: SqlGenerationResult = self._llm.generate_json(prompt, SqlGenerationResult)
        return validate_sql(result.sql)

    def _retry_sql(self, schema: str, previous_sql: str, error: str) -> str:
        prompt = build_sql_retry_prompt(schema, previous_sql, error)
        result: SqlGenerationResult = self._llm.generate_json(prompt, SqlGenerationResult)
        return validate_sql(result.sql)

    @staticmethod
    def _execute(conn: sqlite3.Connection, sql: str) -> tuple[list[str], list[list]]:
        cursor = conn.execute(sql)
        columns = [d[0] for d in cursor.description] if cursor.description else []
        rows = [list(row) for row in cursor.fetchall()]
        return columns, rows

    @staticmethod
    def _summarize(columns: list[str], rows: list[list]) -> str:
        if not rows:
            return "The query ran successfully but returned no rows."
        if len(rows) == 1 and len(columns) == 1:
            return f"{columns[0]}: {rows[0][0]}"
        preview = rows[:5]
        lines = [", ".join(columns)]
        lines += [", ".join(str(v) for v in row) for row in preview]
        suffix = f" (+{len(rows) - 5} more rows)" if len(rows) > 5 else ""
        return "\n".join(lines) + suffix
