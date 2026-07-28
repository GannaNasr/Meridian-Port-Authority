# Database

## Overview

This folder contains the complete database implementation for the Meridian Port Authority system. The database is built using SQLite to provide a lightweight, portable, and easy-to-use relational database solution.

It manages the core entities of the port, including staff, vessels, containers, consignees, trucking companies, customs holds, release orders, gate transactions, and vessel manifest records.

---

## Staff Table & Authorization Model

Previously, fields like `requested_by`, `approved_by`, and `officer_name` were free-text columns — anyone could type any name, with no way to verify that person existed or had the right role. This blocked the role-based access the assignment requires (different tools/permissions for dispatchers, customs officers, and supervisors), since there was no source of truth for who is actually staff and what their role is.

A `staff` table was added to fix this:

- `id` – primary key.
- `name` – staff member's name.
- `role` – one of `dispatcher`, `customs_officer`, `supervisor` (enforced with a `CHECK` constraint).
- `badge_code` – unique badge/login code identifying the staff member.
- `active` – whether the staff member is currently active.

The following columns were converted from free text to foreign keys referencing `staff.id`:

- `customs_holds.officer_id` (was `officer_name`) – the customs officer who placed the hold.
- `release_orders.requested_by` – the staff member who requested the release.
- `release_orders.approved_by` – the staff member who approved it (nullable, since a release can be pending).
- `gate_transactions.processed_by` – the staff member who processed the gate transaction.

This means the MCP server can now check a caller's `role` against the `staff` table before exposing or executing role-restricted tools (e.g., only a `customs_officer` can clear a customs hold, only a `supervisor` can approve a hazmat release) — this is what the Authorization and Notifications protocol concerns are built on top of.

---

## Project Structure

- schema.sql – Creates all database tables, constraints, primary keys, and foreign keys.
- seed.sql – Inserts sample data, including normal and edge-case scenarios.
- init_db.py – Initializes the database by executing the schema and seed scripts.
- meridian_port.db – The generated SQLite database.
- ERD.png – Entity Relationship Diagram (ERD) showing the database design.
- test_relationships.py – Tests and validates the relationships between tables.

---

## Features

- SQLite relational database.
- Well-designed schema with primary and foreign keys.
- Sample data for testing and demonstration.
- Edge cases to validate business rules.
- Entity Relationship Diagram (ERD).
- Relationship validation through automated tests.

---

## How to Initialize the Database

Run the following command:

python init_db.py

This command creates the database, builds all tables, and loads the sample data.

---

## Test Database Relationships

Run the following command:

python test_relationships.py

If the setup is correct, the script will verify that all foreign key relationships are working successfully, including:

- containers ↔ vessels
- customs_holds ↔ containers
- release_orders ↔ containers
- customs_holds.officer_id ↔ staff
- release_orders.requested_by / approved_by ↔ staff
- gate_transactions.processed_by ↔ staff
- all three required staff roles (dispatcher, customs_officer, supervisor) exist and are active