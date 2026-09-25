"""Generates and seeds data/enterprise.db with synthetic sales/customer/employee data.

Fixed random seed so the dataset (and therefore query results) is reproducible across runs.
Run with: python scripts/generate_sql_data.py
"""

import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

RANDOM_SEED = 42
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "enterprise.db"

REGIONS = [
    ("North America", "USA"),
    ("North America", "Canada"),
    ("Europe", "Germany"),
    ("Europe", "United Kingdom"),
    ("Asia Pacific", "Australia"),
    ("Asia Pacific", "Japan"),
]

INDUSTRIES = ["Retail", "Healthcare", "Finance", "Manufacturing", "Technology", "Education"]
PLAN_TIERS = ["Starter", "Growth", "Enterprise"]
PRODUCTS = ["Core Platform", "Analytics Add-on", "Premium Support", "Integration Suite"]
DEPARTMENTS = ["Engineering", "Sales", "Support", "Marketing", "Product", "Operations"]
CHURN_REASONS = ["Price", "Missing features", "Poor support experience", "Switched to competitor", "Budget cuts"]

SCHEMA_SQL = """
CREATE TABLE regions (
    region_id INTEGER PRIMARY KEY,
    region_name TEXT NOT NULL,
    country TEXT NOT NULL
);

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    region_id INTEGER NOT NULL REFERENCES regions(region_id),
    industry TEXT NOT NULL,
    signup_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'churned')),
    plan_tier TEXT NOT NULL
);

CREATE TABLE sales (
    sale_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    sale_date TEXT NOT NULL,
    amount REAL NOT NULL,
    product TEXT NOT NULL,
    quarter TEXT NOT NULL,
    year INTEGER NOT NULL
);

CREATE TABLE churn_events (
    event_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    churn_date TEXT NOT NULL,
    reason TEXT NOT NULL
);

CREATE TABLE employee_satisfaction_scores (
    id INTEGER PRIMARY KEY,
    department TEXT NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    avg_score REAL NOT NULL,
    industry_benchmark REAL NOT NULL
);
"""


def quarter_of(d: date) -> str:
    return f"Q{(d.month - 1) // 3 + 1}"


def random_date(rng: random.Random, start: date, end: date) -> date:
    delta_days = (end - start).days
    return start + timedelta(days=rng.randint(0, delta_days))


def build_database(rng: random.Random, conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)

    conn.executemany(
        "INSERT INTO regions (region_id, region_name, country) VALUES (?, ?, ?)",
        [(i + 1, name, country) for i, (name, country) in enumerate(REGIONS)],
    )

    start_signup = date(2023, 1, 1)
    end_signup = date(2025, 6, 30)
    customers = []
    for customer_id in range(1, 201):
        region_id = rng.randint(1, len(REGIONS))
        signup = random_date(rng, start_signup, end_signup)
        status = "churned" if rng.random() < 0.2 else "active"
        customers.append(
            (
                customer_id,
                f"Customer {customer_id:03d}",
                region_id,
                rng.choice(INDUSTRIES),
                signup.isoformat(),
                status,
                rng.choice(PLAN_TIERS),
            )
        )
    conn.executemany(
        "INSERT INTO customers (customer_id, name, region_id, industry, signup_date, status, plan_tier) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        customers,
    )

    sale_start = date(2024, 1, 1)
    sale_end = date(2025, 12, 31)
    sales = []
    sale_id = 1
    for customer_id in range(1, 201):
        num_sales = rng.randint(5, 15)
        for _ in range(num_sales):
            sale_date = random_date(rng, sale_start, sale_end)
            amount = round(rng.uniform(200, 5000), 2)
            sales.append(
                (
                    sale_id,
                    customer_id,
                    sale_date.isoformat(),
                    amount,
                    rng.choice(PRODUCTS),
                    quarter_of(sale_date),
                    sale_date.year,
                )
            )
            sale_id += 1
    conn.executemany(
        "INSERT INTO sales (sale_id, customer_id, sale_date, amount, product, quarter, year) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        sales,
    )

    churned_customer_ids = [c[0] for c in customers if c[5] == "churned"]
    churn_events = []
    for event_id, customer_id in enumerate(churned_customer_ids, start=1):
        churn_date = random_date(rng, date(2024, 6, 1), date(2025, 12, 31))
        churn_events.append((event_id, customer_id, churn_date.isoformat(), rng.choice(CHURN_REASONS)))
    conn.executemany(
        "INSERT INTO churn_events (event_id, customer_id, churn_date, reason) VALUES (?, ?, ?, ?)",
        churn_events,
    )

    satisfaction_rows = []
    row_id = 1
    for dept in DEPARTMENTS:
        for year in (2024, 2025):
            for quarter in (1, 2, 3, 4):
                score = round(rng.uniform(6.0, 9.2), 1)
                benchmark = round(rng.uniform(7.0, 8.0), 1)
                satisfaction_rows.append((row_id, dept, year, quarter, score, benchmark))
                row_id += 1
    conn.executemany(
        "INSERT INTO employee_satisfaction_scores (id, department, year, quarter, avg_score, industry_benchmark) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        satisfaction_rows,
    )

    conn.commit()


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    rng = random.Random(RANDOM_SEED)
    conn = sqlite3.connect(DB_PATH)
    try:
        build_database(rng, conn)
    finally:
        conn.close()

    print(f"Seeded {DB_PATH}")


if __name__ == "__main__":
    main()
