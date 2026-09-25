import re

_FORBIDDEN_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|ATTACH|DETACH|PRAGMA|REPLACE|VACUUM|GRANT|REVOKE)\b",
    re.IGNORECASE,
)
_SELECT_PREFIX = re.compile(r"^\s*(WITH\b.*?\)\s*SELECT\b|SELECT\b)", re.IGNORECASE | re.DOTALL)


class SQLValidationError(ValueError):
    """Raised when generated SQL is not a safe, single read-only SELECT statement."""


def validate_sql(sql: str) -> str:
    cleaned = sql.strip()
    cleaned = cleaned[:-1].strip() if cleaned.endswith(";") else cleaned

    if ";" in cleaned:
        raise SQLValidationError("Multiple SQL statements are not allowed.")
    if not _SELECT_PREFIX.match(cleaned):
        raise SQLValidationError("Only SELECT (optionally with a WITH clause) statements are permitted.")
    if _FORBIDDEN_KEYWORDS.search(cleaned):
        raise SQLValidationError("Query contains a forbidden keyword.")

    return cleaned
