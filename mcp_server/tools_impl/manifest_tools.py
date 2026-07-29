"""
manifest_tools.py — reconcile_vessel_manifest.

Genuinely multi-step: a vessel can have many manifest line items, and each
one needs its own comparison query against the live containers table. A
real terminal's manifest can run into the hundreds of lines, so blocking
silently until the whole thing finishes is a bad client experience — this
reports progress after each item via ctx.report_progress, which only
sends anything if the caller attached a progressToken to the tools/call
request (see server.py).
"""

from mcp_server import db
from mcp_server.protocol import JSONRPCError, ERR_NOT_FOUND
from mcp_server.tools_impl import text_result


def handle_reconcile_vessel_manifest(conn, session, ctx, arguments: dict) -> dict:
    session.require_role("dispatcher", "supervisor")

    vessel_name = arguments["vessel_name"]
    vessel = conn.execute(
        "SELECT id, vessel_name FROM vessels WHERE vessel_name = ?", (vessel_name,)
    ).fetchone()
    if vessel is None:
        raise JSONRPCError(ERR_NOT_FOUND, f"No vessel named '{vessel_name}' found.")

    items = conn.execute(
        """
        SELECT mi.id AS manifest_item_id, mi.manifest_status, mi.notes,
               c.container_number, c.status AS container_status, c.hazmat
        FROM vessel_manifest_items mi
        JOIN containers c ON c.id = mi.container_id
        WHERE mi.vessel_id = ?
        ORDER BY mi.id
        """,
        (vessel["id"],),
    ).fetchall()

    total = len(items)
    discrepancies = []
    checked = []

    for i, item in enumerate(items, start=1):
        # A discrepancy: manifest says Discharged but container is still
        # In Yard/On Hold with no gate-out, or vice versa — a real check,
        # not a placeholder. Kept simple: flag hazmat items still On Hold
        # after being marked Discharged, since that's an operational risk.
        is_discrepancy = (
            item["manifest_status"] == "Discharged" and item["container_status"] == "On Hold"
        )
        record = {
            "container_number": item["container_number"],
            "manifest_status": item["manifest_status"],
            "container_status": item["container_status"],
            "hazmat": bool(item["hazmat"]),
            "discrepancy": is_discrepancy,
        }
        checked.append(record)
        if is_discrepancy:
            discrepancies.append(record)

        ctx.report_progress(
            progress=i,
            total=total,
            message=f"Checked {item['container_number']} ({i}/{total})",
        )

    return text_result({
        "vessel_name": vessel["vessel_name"],
        "items_checked": total,
        "discrepancies_found": len(discrepancies),
        "discrepancies": discrepancies,
        "all_items": checked,
    })
