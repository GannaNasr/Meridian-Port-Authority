# Meridian-Port-Authority
A Model Context Protocol (MCP) server for secure container release management, featuring role-based access, interactive workflows, resources, prompts, and protocol-compliant agent communication.

Database

The project uses SQLite as the database engine because it is lightweight, portable, and requires no separate server installation.

### Roles & Authorization

Access is scoped to three staff roles, each stored in a `staff` table with a unique `badge_code`:

- **dispatcher**: requests container releases and processes gate transactions.
- **customs_officer**: places and clears customs holds.
- **supervisor**: approves sensitive releases (e.g., hazmat, customs-held containers).

Fields that used to be free text (`requested_by`, `approved_by`, `officer_name`, `processed_by`) are now foreign keys into `staff.id`, so the server can verify a caller's real role before exposing or running a restricted tool, instead of trusting a typed-in name. This is the basis for the Authorization and Notifications protocol concerns.

### Database Components

- schema.sql: Creates all database tables and defines relationships, including the `staff` table and its foreign keys.
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