"""
session_tools.py — authenticate.

This is the trigger for the Notifications concern. Before authenticate
succeeds, a session is anonymous: tools/list only shows the public
read-only tools + authenticate itself. The moment authenticate succeeds,
the session's role is set server-side (never trusted from client input —
see auth.Session.login, which reads the role out of the `staff` table by
badge_code, not out of anything the client asserted), and the server
pushes notifications/tools/list_changed so the client knows to re-fetch
tools/list without polling or reconnecting. The actual push call lives in
server.py right after this handler returns, so server.py stays the single
place that owns "when do we tell the client the tool set changed."
"""

from mcp_server import db
from mcp_server.protocol import JSONRPCError, ERR_NOT_FOUND
from mcp_server.tools_impl import text_result


def handle_authenticate(conn, session, ctx, arguments: dict) -> dict:
    badge_code = arguments["badge_code"]

    staff = db.get_staff_by_badge(conn, badge_code)
    if staff is None:
        raise JSONRPCError(ERR_NOT_FOUND, f"No staff member found with badge_code '{badge_code}'.")
    if not staff["active"]:
        raise JSONRPCError(ERR_NOT_FOUND, f"Badge '{badge_code}' belongs to an inactive staff member.")

    session.login(staff)

    return text_result({
        "authenticated": True,
        "name": session.name,
        "role": session.role,
        "note": "Tool set updated for this role — tools/list_changed sent.",
    })
