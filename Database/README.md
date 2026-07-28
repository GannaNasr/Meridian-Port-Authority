# Database

## Overview

This folder contains the complete database implementation for the Meridian Port Authority system. The database is built using SQLite to provide a lightweight, portable, and easy-to-use relational database solution.

It manages the core entities of the port, including vessels, containers, consignees, trucking companies, customs holds, release orders, gate transactions, and vessel manifest records.

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

### How to Initialize the Database

Run the following command:

python init_db.py

This command creates the database, builds all tables, and loads the sample data.

---

### Test Database Relationships

Run the following command:

python test_relationships.py

If the setup is correct, the script will verify that all foreign key relationships are working successfully.
