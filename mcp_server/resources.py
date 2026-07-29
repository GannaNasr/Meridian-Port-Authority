"""
resources.py — resources/list and resources/read.

Ownership note: the actual resource CONTENT (hazmat_policy.md,
customs_policy.md, vessel_manifest.md) was authored by Person 1 as part
of the database/resources workstream. This module is the thin server-side
wiring that exposes those files through the resources/list and
resources/read protocol methods so the MCP server as a whole is runnable
end-to-end; it lives here only because server.py (Person 2's file) needs
somewhere to dispatch those two methods to.
"""

from pathlib import Path

from mcp_server.protocol import JSONRPCError, ERR_NOT_FOUND

RESOURCES_DIR = Path(__file__).resolve().parent.parent / "resources"

_CATALOG = {
    "policy://hazmat": ("hazmat_policy.md", "Hazmat Handling Policy"),
    "policy://customs": ("customs_policy.md", "Customs Hold Policy"),
    "manifest://ever-glory": ("vessel_manifest.md", "Vessel Manifest Data"),
}


def list_resources() -> dict:
    resources = []
    for uri, (fname, title) in _CATALOG.items():
        resources.append({
            "uri": uri,
            "name": title,
            "mimeType": "text/markdown",
        })
    return {"resources": resources}


def read_resource(uri: str) -> dict:
    entry = _CATALOG.get(uri)
    if entry is None:
        raise JSONRPCError(ERR_NOT_FOUND, f"No resource with uri '{uri}'.")
    fname, title = entry
    path = RESOURCES_DIR / fname
    if not path.exists():
        raise JSONRPCError(ERR_NOT_FOUND, f"Resource file '{fname}' missing on disk.")
    text = path.read_text(encoding="utf-8")
    return {
        "contents": [
            {"uri": uri, "mimeType": "text/markdown", "text": text}
        ]
    }
