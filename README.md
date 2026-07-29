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

## MCP Server

The `mcp_server/` folder implements the server side of the protocol — the layer that sits between the LLM agent and the database, enforcing every rule the database itself can't enforce on its own.

No third-party MCP/JSON-Schema libraries were available in the build environment, so the JSON-RPC 2.0 message framing (stdio transport) and tool-input validation are implemented directly against the spec rather than through the `mcp` or `jsonschema` packages — see `mcp_server/protocol.py` and `mcp_server/validate.py` for details.

### Tools

| Tool | Role required | Write? | Notes |
|---|---|---|---|
| `authenticate` | none | no | Logs the connection in by badge code; changes which tools are available for the rest of the session. |
| `get_container_status` | none | no | Container status, hazmat flag, active hold. |
| `get_vessel_schedule` | none | no | Vessel arrival/departure status. |
| `list_active_customs_holds` | customs_officer, supervisor | no | |
| `request_container_release` | dispatcher | **yes** | Auto-releases clean containers; pauses for human confirmation (elicitation) before filing a Pending order for hazmat or customs-held containers. Hidden entirely from a client that doesn't support elicitation. |
| `approve_container_release` | supervisor | **yes** | Cannot approve while an active customs hold remains — a supervisor cannot override customs. |
| `clear_customs_hold` | customs_officer | **yes** | Clears a hold; does not release the container by itself. |
| `assess_container_risk` | any authenticated | no | Uses the connected client's own model (sampling) to reason over policy + container facts. Hidden from clients without sampling support. |
| `reconcile_vessel_manifest` | dispatcher, supervisor | no | Long-running; reports progress after each manifest line item instead of one blocking response. |

Every tool's input schema is typed, lists `required` fields, and sets `additionalProperties: false` — no bare-dict or untyped tools.

### How each protocol concern is implemented

| Concern | Where |
|---|---|
| **Capability negotiation** | `initialize` — server declares `tools.listChanged`, `resources`, `prompts`; client's declared `elicitation`/`sampling` support is checked before those tools are ever offered or called. |
| **Notifications** | A successful `authenticate` call changes the session's role and immediately fires `notifications/tools/list_changed` — no reconnect or polling needed for the tool set to update. |
| **Elicitation** | `request_container_release` pauses mid-call via `elicitation/create` when a container is hazmat and/or under an active customs hold, and only proceeds (filing a Pending release order) on explicit confirmation. |
| **Resources** | Hazmat policy, customs policy, and the vessel manifest are exposed via `resources/list` / `resources/read` as read-only documents, not tools. |
| **Prompts** | Release justification, incident report, and risk assessment templates are exposed via `prompts/list` / `prompts/get`. |
| **Sampling** | `assess_container_risk` sends container facts + policy text to the **client's** model via `sampling/createMessage` — the server never runs its own model for this. |
| **Progress tracking** | `reconcile_vessel_manifest` reports progress after each manifest line item checked, rather than blocking until the whole vessel is done. |
| **Defensive tool design** | Every tool call is checked twice: JSON Schema validation first (shape/type), then independent business-rule validation against the live database inside the handler (container exists, carrier isn't suspended, order is still Pending, etc.). |
| **Authorization** | Enforced inside each restricted handler based on the authenticated session's role — never inferred from what `tools/list` happened to show a given client. |

### Running it

```bash
python -m mcp_server.server
```

Expects `Database/meridian_port.db` to already exist (run `python Database/init_db.py` first if not). It's a stdio server: a client subprocesses this command and exchanges newline-delimited JSON-RPC 2.0 over stdin/stdout.