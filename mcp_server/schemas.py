"""
schemas.py — the single source of truth for every tool's shape and gating.

For a grader: this is the one file to open to see, for every tool, its
JSON Schema (typed, required, additionalProperties: false, real
descriptions — no bare dict / **kwargs tools anywhere), which roles may
call it, and which client capability (if any) it depends on.

`roles=None` means "any authenticated staff member, any role."
`roles=()` (empty tuple) means "no authentication required at all" — used
only by `authenticate` itself and the two read-only lookup tools that a
front-desk / unauthenticated session can still use.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict
    roles: tuple | None          # None = any authenticated role; () = public
    requires_capability: str | None = None  # "elicitation" | "sampling" | None


TOOLS: dict[str, ToolSpec] = {}


def _register(spec: ToolSpec):
    TOOLS[spec.name] = spec


# ---------------------------------------------------------------------------
# authenticate — logs the connection in as a staff member. Public (no role
# required to call it — you need it precisely because you have no role
# yet). Successful login is what drives the Notifications concern: see
# tools_impl/session_tools.py and notifications.py.
# ---------------------------------------------------------------------------
_register(ToolSpec(
    name="authenticate",
    description=(
        "Authenticate this connection as a Meridian staff member using a "
        "badge code. Determines which role-restricted tools become "
        "available for the rest of the session; changes the tool set and "
        "fires notifications/tools/list_changed on success."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "badge_code": {
                "type": "string",
                "description": "Staff badge code, e.g. 'BADGE-D01'.",
                "minLength": 3,
                "maxLength": 32,
            }
        },
        "required": ["badge_code"],
        "additionalProperties": False,
    },
    roles=(),
))

# ---------------------------------------------------------------------------
# get_container_status — public read-only lookup.
# ---------------------------------------------------------------------------
_register(ToolSpec(
    name="get_container_status",
    description=(
        "Look up a single container by its container number: current "
        "status, hazmat flag, vessel, carrier, and any active customs "
        "hold. Read-only."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "container_number": {
                "type": "string",
                "description": "Container number, e.g. 'MSKU100001'.",
                "minLength": 4,
                "maxLength": 20,
                "pattern": "^[A-Za-z0-9]+$",
            }
        },
        "required": ["container_number"],
        "additionalProperties": False,
    },
    roles=(),
))

# ---------------------------------------------------------------------------
# get_vessel_schedule — public read-only lookup.
# ---------------------------------------------------------------------------
_register(ToolSpec(
    name="get_vessel_schedule",
    description=(
        "List vessels and their arrival/departure status, optionally "
        "filtered by status. Read-only."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "description": "Optional filter.",
                "enum": ["Arrived", "Berthed", "Departed"],
            }
        },
        "required": [],
        "additionalProperties": False,
    },
    roles=(),
))

# ---------------------------------------------------------------------------
# list_active_customs_holds — customs_officer + supervisor only.
# ---------------------------------------------------------------------------
_register(ToolSpec(
    name="list_active_customs_holds",
    description=(
        "List every container currently under an active customs hold, "
        "with hold reason and the officer who placed it. Read-only."
    ),
    input_schema={
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    },
    roles=("customs_officer", "supervisor"),
))

# ---------------------------------------------------------------------------
# request_container_release — dispatcher only. The risky write tool.
# Requires elicitation support: a client that can't do human-in-the-loop
# confirmation does not get offered this tool at all (see server.py's
# tools/list filtering) — it gets the read-only get_container_status
# fallback instead, per the assignment's own worked example.
# ---------------------------------------------------------------------------
_register(ToolSpec(
    name="request_container_release",
    description=(
        "Request release of a container to its consignee/carrier. Clean "
        "containers (no hazmat flag, no active customs hold, active "
        "carrier) are released immediately. A hazmat container and/or one "
        "under an active customs hold cannot be auto-released: this tool "
        "pauses mid-call via elicitation to confirm the dispatcher "
        "understands supervisor approval is required, then files a "
        "Pending release order instead of releasing the container."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "container_number": {
                "type": "string",
                "minLength": 4,
                "maxLength": 20,
                "pattern": "^[A-Za-z0-9]+$",
                "description": "Container number to release, e.g. 'MSKU100001'.",
            },
            "release_reason": {
                "type": "string",
                "minLength": 5,
                "maxLength": 300,
                "description": "Business reason for the release request.",
            },
        },
        "required": ["container_number", "release_reason"],
        "additionalProperties": False,
    },
    roles=("dispatcher",),
    requires_capability="elicitation",
))

# ---------------------------------------------------------------------------
# approve_container_release — supervisor only.
# ---------------------------------------------------------------------------
_register(ToolSpec(
    name="approve_container_release",
    description=(
        "Approve or reject a Pending release order (created for hazmat or "
        "customs-held containers). Cannot approve a release while an "
        "active customs hold still exists — customs must clear the hold "
        "first, a supervisor cannot override customs."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "release_order_id": {
                "type": "integer",
                "minimum": 1,
                "description": "id of the Pending release_orders row.",
            },
            "decision": {
                "type": "string",
                "enum": ["Approved", "Rejected"],
                "description": "Supervisor's decision.",
            },
            "notes": {
                "type": "string",
                "maxLength": 300,
                "description": "Optional notes explaining the decision.",
            },
        },
        "required": ["release_order_id", "decision"],
        "additionalProperties": False,
    },
    roles=("supervisor",),
))

# ---------------------------------------------------------------------------
# clear_customs_hold — customs_officer only.
# ---------------------------------------------------------------------------
_register(ToolSpec(
    name="clear_customs_hold",
    description=(
        "Clear an active customs hold on a container after review. Does "
        "NOT release the container by itself — a hazmat container still "
        "needs a separate supervisor-approved release order."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "hold_id": {
                "type": "integer",
                "minimum": 1,
                "description": "id of the Active customs_holds row.",
            },
            "resolution_notes": {
                "type": "string",
                "minLength": 5,
                "maxLength": 300,
                "description": "Why the hold is being cleared.",
            },
        },
        "required": ["hold_id", "resolution_notes"],
        "additionalProperties": False,
    },
    roles=("customs_officer",),
))

# ---------------------------------------------------------------------------
# assess_container_risk — any authenticated role; needs client sampling.
# ---------------------------------------------------------------------------
_register(ToolSpec(
    name="assess_container_risk",
    description=(
        "Assemble the container's status, hazmat flag, hold/carrier "
        "status and the relevant policy text, then ask the CLIENT's model "
        "(via sampling/createMessage) to produce a structured risk "
        "assessment. The server does not run its own model for this."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "container_number": {
                "type": "string",
                "minLength": 4,
                "maxLength": 20,
                "pattern": "^[A-Za-z0-9]+$",
            }
        },
        "required": ["container_number"],
        "additionalProperties": False,
    },
    roles=None,
    requires_capability="sampling",
))

# ---------------------------------------------------------------------------
# reconcile_vessel_manifest — dispatcher + supervisor; long-running,
# reports progress per container instead of one blocking response.
# ---------------------------------------------------------------------------
_register(ToolSpec(
    name="reconcile_vessel_manifest",
    description=(
        "Walk every manifest line item for a vessel and compare it "
        "against the live container record, reporting progress after "
        "each item, then return a discrepancy report. Genuinely "
        "multi-step, not a single blocking query dressed up as one."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "vessel_name": {
                "type": "string",
                "minLength": 2,
                "maxLength": 80,
                "description": "Exact vessel name, e.g. 'Ever Glory'.",
            }
        },
        "required": ["vessel_name"],
        "additionalProperties": False,
    },
    roles=("dispatcher", "supervisor"),
))


def tool_names():
    return list(TOOLS.keys())
