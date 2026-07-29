"""
db.py — thin SQLite access layer on top of the schema Person 1 built.

Deliberately dumb: no ORM, no query builder. Every tool handler in
tools_impl/ writes its own explicit SQL so a grader can see exactly what
each tool reads or writes. This module only owns the connection and a
couple of shared lookups (staff, containers) used by more than one tool.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "Database" / "meridian_port.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_staff_by_badge(conn, badge_code: str):
    row = conn.execute(
        "SELECT id, name, role, badge_code, active FROM staff WHERE badge_code = ?",
        (badge_code,),
    ).fetchone()
    return row


def get_container_by_number(conn, container_number: str):
    row = conn.execute(
        """
        SELECT c.id, c.container_number, c.container_type, c.hazmat, c.status,
               c.arrival_date, c.vessel_id, c.consignee_id, c.carrier_id,
               v.vessel_name, tc.company_name AS carrier_name, tc.status AS carrier_status
        FROM containers c
        JOIN vessels v ON v.id = c.vessel_id
        JOIN trucking_companies tc ON tc.id = c.carrier_id
        WHERE c.container_number = ?
        """,
        (container_number,),
    ).fetchone()
    return row


def get_active_hold_for_container(conn, container_id: int):
    row = conn.execute(
        """
        SELECT id, container_id, hold_reason, hold_status, officer_id, created_at
        FROM customs_holds
        WHERE container_id = ? AND hold_status = 'Active'
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (container_id,),
    ).fetchone()
    return row
