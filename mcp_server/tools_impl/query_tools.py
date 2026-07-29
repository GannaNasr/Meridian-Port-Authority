"""
query_tools.py — public, read-only tools. No role required (session may be
anonymous), so these handlers do NOT call session.require_role(). They
still fully validate their inputs against the database (an unknown
container number is a clean 404, not a stack trace).
"""

from mcp_server import db
from mcp_server.protocol import JSONRPCError, ERR_NOT_FOUND
from mcp_server.tools_impl import text_result


def handle_get_container_status(conn, session, ctx, arguments: dict) -> dict:
    container_number = arguments["container_number"]
    container = db.get_container_by_number(conn, container_number)
    if container is None:
        raise JSONRPCError(ERR_NOT_FOUND, f"No container '{container_number}' found.")

    hold = db.get_active_hold_for_container(conn, container["id"])

    return text_result({
        "container_number": container["container_number"],
        "status": container["status"],
        "hazmat": bool(container["hazmat"]),
        "container_type": container["container_type"],
        "vessel_name": container["vessel_name"],
        "carrier_name": container["carrier_name"],
        "carrier_status": container["carrier_status"],
        "active_customs_hold": {
            "hold_id": hold["id"],
            "hold_reason": hold["hold_reason"],
            "created_at": hold["created_at"],
        } if hold else None,
    })


def handle_get_vessel_schedule(conn, session, ctx, arguments: dict) -> dict:
    status_filter = arguments.get("status")
    if status_filter:
        rows = conn.execute(
            "SELECT vessel_name, imo_number, arrival_date, departure_date, status "
            "FROM vessels WHERE status = ? ORDER BY arrival_date",
            (status_filter,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT vessel_name, imo_number, arrival_date, departure_date, status "
            "FROM vessels ORDER BY arrival_date"
        ).fetchall()

    return text_result({"vessels": [dict(r) for r in rows]})


def handle_list_active_customs_holds(conn, session, ctx, arguments: dict) -> dict:
    # Authorization: customs_officer or supervisor only.
    session.require_role("customs_officer", "supervisor")

    rows = conn.execute(
        """
        SELECT h.id AS hold_id, c.container_number, h.hold_reason, h.created_at,
               s.name AS officer_name
        FROM customs_holds h
        JOIN containers c ON c.id = h.container_id
        JOIN staff s ON s.id = h.officer_id
        WHERE h.hold_status = 'Active'
        ORDER BY h.created_at
        """
    ).fetchall()

    return text_result({"active_holds": [dict(r) for r in rows]})
