"""
tools_impl/ — one module per family of tools, split by what they touch:

  session_tools.py   authenticate                          (Notifications)
  query_tools.py      get_container_status, get_vessel_schedule,
                       list_active_customs_holds             (read-only)
  release_tools.py    request_container_release,
                       approve_container_release,
                       clear_customs_hold                    (Defensive design,
                                                               Authorization,
                                                               Elicitation call-site)
  risk_tools.py        assess_container_risk                 (Sampling call-site)
  manifest_tools.py    reconcile_vessel_manifest              (Progress tracking)

Every handler has the same signature:

    handler(conn, session, ctx, arguments) -> dict

`conn` is a live sqlite3 connection, `session` is the auth.Session for this
connection, `ctx` is a context.ToolContext (elicit / sample / progress),
`arguments` is the already-schema-validated dict from tools/call.

Handlers still re-validate business rules themselves (existence,
state transitions, active/suspended flags) — the JSON Schema only checked
shape, never checked "does this container exist" or "is this carrier
suspended." That's the point of Defensive Tool Design: schema validation
and business validation are two separate steps, and both are enforced
before anything touches the database.
"""

import json


def text_result(payload: dict) -> dict:
    """Wrap a plain dict as an MCP tools/call result content block."""
    return {"content": [{"type": "text", "text": json.dumps(payload, indent=2, default=str)}]}
