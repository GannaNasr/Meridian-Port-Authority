# Meridian-Port-Authority
A Model Context Protocol (MCP) server for secure container release management, featuring role-based access, interactive workflows, resources, prompts, and protocol-compliant agent communication.

Database

The project uses SQLite as the database engine because it is lightweight, portable, and requires no separate server installation.

### Database Components

- schema.sql: Creates all database tables and defines relationships.
- seed.sql: Inserts sample data, including normal and edge-case scenarios.
- init_db.py: Initializes the database by creating the schema and loading seed data.
- meridian_port.db: The generated SQLite database file.
- ERD.png: Entity Relationship Diagram illustrating the database structure.
- test_relationships.py: Verifies that foreign key relationships between tables work correctly.

### Database Features

- Relational database design using primary and foreign keys.
- Sample data covering both normal operations and edge cases.
- Relationship validation through automated testing.
- ERD documentation for the complete schema.


## Resources & Prompts

### Resources
The system uses external resources to provide the agent with fixed operational knowledge:

- Hazmat Policy: Defines rules for handling hazardous containers and release requirements.
- Customs Policy: Defines procedures for containers under customs hold.
- Vessel Manifest: Provides vessel and container cargo information.

### Prompts
The system provides reusable prompt templates to guide LLM responses:

- Release Justification Prompt: Generates structured explanations for container release decisions.
- Incident Report Prompt: Creates organized incident reports for port operation issues.
- Risk Assessment Prompt: Evaluates container risks and identifies required approvals.
