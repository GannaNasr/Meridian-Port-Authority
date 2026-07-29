"""
risk_tools.py — assess_container_risk.

Why this genuinely needs sampling instead of the server just computing an
answer: "risk" here isn't a lookup, it's a judgment call that weighs
several policy documents against the specific facts of one container
(hazmat + active hold is categorically worse than either alone; a
suspended carrier changes the read even on a clean container). That's
exactly the kind of open-ended reasoning the assignment says belongs to
the CLIENT's model via sampling/createMessage, not a server-side model —
the server's job is to assemble accurate facts and policy text, not to
have its own opinion.
"""

from pathlib import Path

from mcp_server import db
from mcp_server.protocol import JSONRPCError, ERR_NOT_FOUND
from mcp_server.tools_impl import text_result

RESOURCES_DIR = Path(__file__).resolve().parent.parent.parent / "resources"


def _load_policy_text() -> str:
    parts = []
    for fname in ("hazmat_policy.md", "customs_policy.md"):
        path = RESOURCES_DIR / fname
        if path.exists():
            parts.append(path.read_text(encoding="utf-8"))
    return "\n\n---\n\n".join(parts)


def handle_assess_container_risk(conn, session, ctx, arguments: dict) -> dict:
    container_number = arguments["container_number"]
    container = db.get_container_by_number(conn, container_number)
    if container is None:
        raise JSONRPCError(ERR_NOT_FOUND, f"No container '{container_number}' found.")

    hold = db.get_active_hold_for_container(conn, container["id"])

    facts = {
        "container_number": container["container_number"],
        "status": container["status"],
        "hazmat": bool(container["hazmat"]),
        "carrier_name": container["carrier_name"],
        "carrier_status": container["carrier_status"],
        "active_customs_hold": hold["hold_reason"] if hold else None,
    }

    policy_text = _load_policy_text()

    sampling_result = ctx.sample(
        messages=[
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": (
                        "Assess release risk for this container using the policy "
                        "text provided as system context. Respond with: Risk Level "
                        "(Low/Medium/High), Risk Factors, Required Approvals, and "
                        "Recommendation.\n\nContainer facts:\n"
                        f"{facts}"
                    ),
                },
            }
        ],
        system_prompt=(
            "You are assessing container-release risk for Meridian Port Authority. "
            "Use only the following policies as your rules:\n\n" + policy_text
        ),
        max_tokens=500,
    )

    return text_result({
        "container_facts": facts,
        "model_assessment": sampling_result,
    })
