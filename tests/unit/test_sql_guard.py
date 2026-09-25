import pytest

from enterprise_rag.agents.sql_guard import SQLValidationError, validate_sql


def test_accepts_plain_select():
    assert validate_sql("SELECT * FROM customers") == "SELECT * FROM customers"


def test_accepts_select_with_trailing_semicolon():
    assert validate_sql("SELECT * FROM customers;") == "SELECT * FROM customers"


def test_accepts_select_with_cte():
    sql = "WITH recent AS (SELECT * FROM sales) SELECT * FROM recent"
    assert validate_sql(sql) == sql


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO customers (name) VALUES ('x')",
        "UPDATE customers SET name = 'x'",
        "DELETE FROM customers",
        "DROP TABLE customers",
        "ALTER TABLE customers ADD COLUMN x TEXT",
        "PRAGMA table_info(customers)",
        "ATTACH DATABASE 'other.db' AS other",
    ],
)
def test_rejects_non_select_statements(sql):
    with pytest.raises(SQLValidationError):
        validate_sql(sql)


def test_rejects_multiple_statements():
    with pytest.raises(SQLValidationError):
        validate_sql("SELECT * FROM customers; DROP TABLE customers;")


def test_rejects_select_hiding_a_forbidden_keyword():
    with pytest.raises(SQLValidationError):
        validate_sql("SELECT * FROM customers WHERE 1=1; DELETE FROM customers")
