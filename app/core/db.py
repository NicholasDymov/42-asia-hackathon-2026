import sqlite3
import time
from pathlib import Path
from typing import Dict, Any, List

DB_PATH = Path(__file__).resolve().parent.parent / "enterprise.db"

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initializes real relational enterprise database tables."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Infrastructure Servers & Services
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS servers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            service_type TEXT NOT NULL,
            status TEXT NOT NULL,
            cpu_percent REAL DEFAULT 15.0,
            active_connections INTEGER DEFAULT 20,
            max_connections INTEGER DEFAULT 500,
            region TEXT NOT NULL,
            last_remediated_at TEXT
        )
        """)

        # 2. Financial Ledger & Invoices
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_no TEXT PRIMARY KEY,
            vendor TEXT NOT NULL,
            amount_yen INTEGER NOT NULL,
            po_number TEXT NOT NULL,
            approved_budget_yen INTEGER NOT NULL,
            tax_id TEXT,
            status TEXT NOT NULL,
            department TEXT NOT NULL,
            compliance_notes TEXT
        )
        """)

        # 3. Departmental Cloud Budgets
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            department TEXT PRIMARY KEY,
            monthly_allocation_yen INTEGER NOT NULL,
            spent_yen INTEGER NOT NULL,
            emergency_fund_cap_yen INTEGER NOT NULL
        )
        """)

        # 4. Jira Tickets
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id TEXT PRIMARY KEY,
            summary TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT NOT NULL,
            assignee TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)

        # 5. Immutable Audit Events
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_events (
            event_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            actor TEXT NOT NULL,
            role TEXT NOT NULL,
            status TEXT NOT NULL,
            details_json TEXT NOT NULL
        )
        """)

        # Seed initial data if empty
        cursor.execute("SELECT COUNT(*) FROM servers")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
            INSERT INTO servers (id, name, service_type, status, cpu_percent, active_connections, max_connections, region)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                ("srv-tokyo-01", "Payment Gateway API", "API", "HEALTHY", 18.5, 34, 500, "ap-northeast-1"),
                ("srv-tokyo-02", "User Auth Microservice", "AUTH", "HEALTHY", 22.0, 48, 500, "ap-northeast-1"),
                ("srv-tokyo-db", "Postgres Primary DB", "DATABASE", "HEALTHY", 25.0, 52, 500, "ap-northeast-1")
            ])

        cursor.execute("SELECT COUNT(*) FROM budgets")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            INSERT INTO budgets (department, monthly_allocation_yen, spent_yen, emergency_fund_cap_yen)
            VALUES ('Infrastructure', 2000000, 1780000, 200000)
            """)

        cursor.execute("SELECT COUNT(*) FROM invoices")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
            INSERT INTO invoices (invoice_no, vendor, amount_yen, po_number, approved_budget_yen, tax_id, status, department)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                ("INV-TYO-901", "Sakura Cloud Solutions K.K.", 142000, "PO-2026-88", 100000, "T1010001001234", "PENDING_REVIEW", "Infrastructure"),
                ("INV-TYO-902", "Shinjuku Office Supplies", 35000, "PO-2026-89", 40000, "T2010001005678", "APPROVED", "Operations")
            ])

        conn.commit()

init_database()
