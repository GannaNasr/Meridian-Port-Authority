"""
capabilities.py — what the Meridian agent declares to the server during
initialize.

This is one half of the Capability Negotiation concern (the server-side
half — SERVER_CAPABILITIES and session.supports() — lives in
mcp_server/server.py and mcp_server/auth.py). The agent declares real
support for elicitation and sampling because it actually implements both
(see elicitation.py, sampling.py) — declaring a capability you don't back
up would defeat the entire point of negotiation.

session.py checks what the SERVER declared back (e.g.
capabilities.tools.listChanged) before the agent ever relies on
notifications actually arriving, instead of just assuming it.
"""

PROTOCOL_VERSION = "2025-06-18"

CLIENT_INFO = {"name": "meridian-agent", "version": "1.0.0"}

CLIENT_CAPABILITIES = {
    "elicitation": {},
    "sampling": {},
}
