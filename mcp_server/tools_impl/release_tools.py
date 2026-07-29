"""
release_tools.py — the tools that actually change container state.

These three handlers are where Defensive Tool Design and Authorization
earn their place: every one of them does real, independent-of-schema
validation (does this row exist, is it in a state this action is even
legal from, is the carrier suspended) before writing anything, and every
one calls session.require_role() itself rather than trusting that
tools/list already filtered out the wrong caller.
"""

from mcp_server import db
from mcp_server.protocol import JSONRPCError, ERR_NOT_FOUND, ERR_CONFLICT
from mcp_server.tools_impl import text_result


def handle_request_container_release(conn, session, ctx, arguments: dict) -> dict:
    # --- Authorization (handler-level, not just tools/list filtering) ---
    session.require_role("dispatcher")

    container_number = arguments["container_number"]
    release_reason = arguments["release_reason"]

    # --- Defensive validation: independent of what the schema already
    # checked (types/lengths). These are business rules that only the
    # database can answer. ---
    container = db.get_container_by_number(conn, container_number)
    if container is None:
        raise JSONRPCError(ERR_NOT_FOUND, f"No container '{container_number}' found.")

    if container["status"] == "Released":
        raise JSONRPCError(ERR_CONFLICT, f"Container '{container_number}' is already Released.")

    if container["carrier_status"] == "Suspended":
        raise JSONRPCError(
            ERR_CONFLICT,
            f"Carrier '{container['carrier_name']}' is Suspended; cannot release to a "
            f"suspended trucking company regardless of container status.",
        )

    hold = db.get_active_hold_for_container(conn, container["id"])
    is_hazmat = bool(container["hazmat"])
    is_held = hold is not None

    if is_hazmat or is_held:
        # --- Elicitation: this is the mid-call human-in-the-loop pause. ---
        reasons = []
        if is_hazmat:
            reasons.append("hazardous materials flag")
        if is_held:
            reasons.append(f"active customs hold (reason: {hold['hold_reason']})")

        answer = ctx.elicit(
            message=(
                f"Container {container_number} cannot be auto-released: "
                f"{', '.join(reasons)}. This requires a supervisor-approved "
                f"release order (and, if held, customs must also clear the "
                f"hold separately). Confirm you want to file this as a "
                f"Pending release order awaiting approval?"
            ),
            requested_schema={
                "type": "object",
                "properties": {
                    "confirm": {
                        "type": "boolean",
                        "description": "true to file the Pending release order, false to abort.",
                    }
                },
                "required": ["confirm"],
            },
        )

        accepted = answer.get("action") == "accept" and answer.get("content", {}).get("confirm") is True
        if not accepted:
            return text_result({
                "released": False,
                "release_order_created": False,
                "message": "Release not requested — declined at confirmation step.",
            })

        cur = conn.execute(
            """
            INSERT INTO release_orders (container_id, requested_by, approved_by,
                                         release_status, release_reason)
            VALUES (?, ?, NULL, 'Pending', ?)
            """,
            (container["id"], session.staff_id, release_reason),
        )
        conn.commit()
        return text_result({
            "released": False,
            "release_order_created": True,
            "release_order_id": cur.lastrowid,
            "release_status": "Pending",
            "message": (
                "Filed as Pending. Requires supervisor approval"
                + (", and customs must clear the active hold" if is_held else "")
                + " before the container can move."
            ),
        })

    # --- Clean container: no hazmat, no hold, active carrier. Auto-approve. ---
    cur = conn.execute(
        """
        INSERT INTO release_orders (container_id, requested_by, approved_by,
                                     release_status, release_reason, released_at)
        VALUES (?, ?, ?, 'Approved', ?, CURRENT_TIMESTAMP)
        """,
        (container["id"], session.staff_id, session.staff_id, release_reason),
    )
    conn.execute("UPDATE containers SET status = 'Released' WHERE id = ?", (container["id"],))
    conn.commit()

    return text_result({
        "released": True,
        "release_order_created": True,
        "release_order_id": cur.lastrowid,
        "release_status": "Approved",
        "message": f"Container {container_number} released.",
    })


def handle_approve_container_release(conn, session, ctx, arguments: dict) -> dict:
    session.require_role("supervisor")

    release_order_id = arguments["release_order_id"]
    decision = arguments["decision"]
    notes = arguments.get("notes")

    order = conn.execute(
        """
        SELECT ro.id, ro.container_id, ro.release_status, c.container_number, c.hazmat
        FROM release_orders ro
        JOIN containers c ON c.id = ro.container_id
        WHERE ro.id = ?
        """,
        (release_order_id,),
    ).fetchone()
    if order is None:
        raise JSONRPCError(ERR_NOT_FOUND, f"No release order #{release_order_id} found.")
    if order["release_status"] != "Pending":
        raise JSONRPCError(
            ERR_CONFLICT,
            f"Release order #{release_order_id} is '{order['release_status']}', not Pending.",
        )

    if decision == "Approved":
        # A supervisor cannot override customs — this is a business rule
        # the schema/type system cannot express, checked here explicitly.
        hold = db.get_active_hold_for_container(conn, order["container_id"])
        if hold is not None:
            raise JSONRPCError(
                ERR_CONFLICT,
                f"Container {order['container_number']} still has an active customs hold "
                f"(#{hold['id']}: {hold['hold_reason']}). Customs must clear it before a "
                f"supervisor can approve release.",
            )
        conn.execute(
            """
            UPDATE release_orders
            SET release_status = 'Approved', approved_by = ?, released_at = CURRENT_TIMESTAMP,
                release_reason = COALESCE(release_reason, '') || CASE WHEN ? IS NOT NULL
                                  THEN ' | supervisor notes: ' || ? ELSE '' END
            WHERE id = ?
            """,
            (session.staff_id, notes, notes, release_order_id),
        )
        conn.execute(
            "UPDATE containers SET status = 'Released' WHERE id = ?",
            (order["container_id"],),
        )
        conn.commit()
        return text_result({
            "release_order_id": release_order_id,
            "decision": "Approved",
            "container_number": order["container_number"],
            "message": "Release approved; container marked Released.",
        })

    # Rejected
    conn.execute(
        "UPDATE release_orders SET release_status = 'Rejected', approved_by = ? WHERE id = ?",
        (session.staff_id, release_order_id),
    )
    conn.commit()
    return text_result({
        "release_order_id": release_order_id,
        "decision": "Rejected",
        "container_number": order["container_number"],
        "message": "Release order rejected.",
    })


def handle_clear_customs_hold(conn, session, ctx, arguments: dict) -> dict:
    session.require_role("customs_officer")

    hold_id = arguments["hold_id"]
    resolution_notes = arguments["resolution_notes"]

    hold = conn.execute(
        "SELECT id, container_id, hold_status FROM customs_holds WHERE id = ?",
        (hold_id,),
    ).fetchone()
    if hold is None:
        raise JSONRPCError(ERR_NOT_FOUND, f"No customs hold #{hold_id} found.")
    if hold["hold_status"] != "Active":
        raise JSONRPCError(ERR_CONFLICT, f"Customs hold #{hold_id} is already '{hold['hold_status']}'.")

    conn.execute(
        """
        UPDATE customs_holds
        SET hold_status = 'Released', released_at = CURRENT_TIMESTAMP,
            hold_reason = hold_reason || ' | resolved: ' || ?
        WHERE id = ?
        """,
        (resolution_notes, hold_id),
    )
    conn.commit()

    return text_result({
        "hold_id": hold_id,
        "hold_status": "Released",
        "message": (
            "Hold cleared. Note: this does not release the container by itself — "
            "a hazmat container still needs a supervisor-approved release order."
        ),
    })
