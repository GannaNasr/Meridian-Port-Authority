"""
prompts.py — prompts/list and prompts/get.

Ownership note: same as resources.py — the prompt template CONTENT
(release_justification_prompt.md, incident_report_prompt.md,
risk_assessment_prompt.md) was authored by Person 1. This is the thin
server-side wiring so prompts/list and prompts/get actually work end to
end.
"""

from pathlib import Path

from mcp_server.protocol import JSONRPCError, ERR_NOT_FOUND

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

_CATALOG = {
    "release_justification": ("release_justification_prompt.md", "Release Justification"),
    "incident_report": ("incident_report_prompt.md", "Incident Report"),
    "risk_assessment": ("risk_assessment_prompt.md", "Container Risk Assessment"),
}


def list_prompts() -> dict:
    prompts = []
    for name, (fname, title) in _CATALOG.items():
        prompts.append({"name": name, "title": title, "arguments": []})
    return {"prompts": prompts}


def get_prompt(name: str) -> dict:
    entry = _CATALOG.get(name)
    if entry is None:
        raise JSONRPCError(ERR_NOT_FOUND, f"No prompt named '{name}'.")
    fname, title = entry
    path = PROMPTS_DIR / fname
    if not path.exists():
        raise JSONRPCError(ERR_NOT_FOUND, f"Prompt file '{fname}' missing on disk.")
    text = path.read_text(encoding="utf-8")
    return {
        "description": title,
        "messages": [
            {"role": "user", "content": {"type": "text", "text": text}}
        ],
    }
