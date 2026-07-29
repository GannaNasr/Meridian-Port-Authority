# mcp_server/ — MCP Server Core

Owner: Person 2 (server structure, tool specs, capability negotiation,
notifications, defensive tool design, authorization). Resource/prompt
*content* under `resources/` and `prompts/` was authored by Person 1;
`resources.py` / `prompts.py` here are just the thin wiring so the server
runs end-to-end — see the docstring at the top of each file.

No third-party packages are required (`mcp`, `jsonschema`, etc. were not
reachable from this environment, so the protocol framing and schema
validation are hand-rolled against the actual spec — see
`validate.py`'s docstring for why, and how to swap in the real
`jsonschema` package later with a one-line change).

## Run it

```bash
python -m mcp_server.server
```

It's a stdio server: a client subprocesses this command and talks
newline-delimited JSON-RPC 2.0 over stdin/stdout. It expects the database
at `Database/meridian_port.db` to already exist (`python Database/init_db.py`
first if not).

## Where each protocol concern lives

| Concern | File | What to look at |
|---|---|---|
| **Capability negotiation** | `server.py` | `handle_initialize()` stores the client's declared capabilities on the session; `SERVER_CAPABILITIES` is what we declare back. `_tool_visible()` and `context.py`'s `elicit()`/`sample()` both check `session.supports(...)` before relying on a capability. |
| **Notifications** | `tools_impl/session_tools.py` + `server.py` + `notifications.py` | `authenticate` sets `session.role` from the `staff` table (never from client input). `handle_tools_call()` in `server.py` fires `notifications.send_tools_list_changed()` right after a successful `authenticate`. `_tool_visible()` is what makes the next `tools/list` actually differ. |
| **Defensive tool design** | `validate.py` (schema-level) + every handler in `tools_impl/` (business-rule level) | `handle_tools_call()` runs `validate.validate()` before ever calling a handler. Each handler then does its own DB-backed checks (container exists, carrier not suspended, order still Pending, etc.) — see especially `release_tools.py`. |
| **Authorization** | `auth.py` (`Session.require_role`) called at the top of every restricted handler in `tools_impl/` | Never inferred from `tools/list` — a client that calls a tool it wasn't shown still gets a clean `ERR_UNAUTHORIZED`/`ERR_UNAUTHENTICATED` error, not a crash or a silent bypass. |
| **Tool specs** | `schemas.py` | Every tool: typed `inputSchema`, `required`, `additionalProperties: false`, real descriptions, plus `roles` and `requires_capability` gating metadata. |
| Elicitation (call-site; Person 3 owns the client-side answer) | `context.py: ToolContext.elicit()`, used in `tools_impl/release_tools.py: handle_request_container_release()` | |
| Sampling (call-site; Person 3 owns the client-side model call) | `context.py: ToolContext.sample()`, used in `tools_impl/risk_tools.py` | |
| Progress tracking (call-site; Person 3 owns the client-side display) | `context.py: ToolContext.report_progress()`, used in `tools_impl/manifest_tools.py` | |

## Tools at a glance

| Tool | Role required | Write? | Notes |
|---|---|---|---|
| `authenticate` | none | no | Sets session role; triggers `tools/list_changed`. |
| `get_container_status` | none | no | |
| `get_vessel_schedule` | none | no | |
| `list_active_customs_holds` | `customs_officer`, `supervisor` | no | |
| `request_container_release` | `dispatcher` | **yes** | Auto-releases clean containers; elicits confirmation and files a Pending order for hazmat/held ones. Hidden entirely from clients without elicitation support. |
| `approve_container_release` | `supervisor` | **yes** | Refuses to approve while an active hold remains — a supervisor cannot override customs. |
| `clear_customs_hold` | `customs_officer` | **yes** | Clears a hold; does not itself release the container. |
| `assess_container_risk` | any authenticated | no | Uses the client's model via sampling. Hidden from clients without sampling support. |
| `reconcile_vessel_manifest` | `dispatcher`, `supervisor` | no | Long-running; reports progress per manifest line item. |

## What happens if a client connects without a needed capability

- No `elicitation` capability: `request_container_release` is not offered
  in `tools/list` at all (the read-only `get_container_status` fallback is
  still there). If a client calls it anyway, `ToolContext.elicit()`
  raises `ERR_CAPABILITY_UNSUPPORTED` instead of silently proceeding or
  silently failing.
- No `sampling` capability: same treatment for `assess_container_risk`.
