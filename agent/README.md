# agent/ — Agent / Client

Owner: Person 3 (agent/client, elicitation, sampling, progress display,
end-to-end testing, final README).

This is a real MCP client: it launches `mcp_server/server.py` as a
subprocess and speaks newline-delimited JSON-RPC 2.0 over its
stdin/stdout, per the stdio transport spec. It never imports anything
from `mcp_server` — the two sides only ever talk over the wire, the same
as they would if the server were remote.

## Files

| File | Responsibility |
|---|---|
| `mcp_client.py` | Raw JSON-RPC/stdio framing + the dispatch loop that lets the server call back into the client mid-`tools/call` (`elicitation/create`, `sampling/createMessage`) while also streaming `notifications/progress`. |
| `capabilities.py` | The client's declared capabilities (`elicitation`, `sampling`) sent in `initialize`. |
| `session.py` | `MeridianAgentSession` — the real `initialize`/`initialized` handshake, `server_supports()` capability checks, and the tool-list cache that invalidates itself on `notifications/tools/list_changed`. |
| `elicitation.py` | Client-side handling of `elicitation/create`: an interactive terminal prompt, or a scripted fixed answer for repeatable demo runs. |
| `sampling.py` | Client-side handling of `sampling/createMessage`: calls the Google Gemini API using `GOOGLE_API_KEY`/`GEMINI_API_KEY` if set, otherwise falls back to a deterministic rule engine over the same container facts (clearly labeled as a fallback). |
| `progress.py` | Renders `notifications/progress` as a live progress bar. |
| `scenarios.py` | The 7 fixed demo scenarios, one function each. |
| `test_inputs.json` | The fixed argument data for those 7 scenarios — what makes the demo repeatable rather than lucky. |
| `client.py` | CLI entry point. |

## Running it

From the project root (the directory containing `Database/`,
`mcp_server/`, `resources/`, `prompts/`, `agent/`):

```bash
python Database/init_db.py          # once, to build/reset the database
python -m agent.client --list
python -m agent.client --scenario capability_negotiation
python -m agent.client --all
```

Add `--interactive` to any run to answer elicitation prompts yourself at
the terminal instead of using the pre-recorded scripted answer.

Optional, for a live model call instead of the offline fallback on
`assess_container_risk`:

```bash
export GOOGLE_API_KEY=AIza...
# or: export GEMINI_API_KEY=AIza...
# optional: export GOOGLE_MODEL=gemini-2.5-flash   (default)
```

## The 7 scenarios

| # | Scenario | Concern(s) demonstrated |
|---|---|---|
| 1 | `capability_negotiation` | Capability Negotiation, Resources, Prompts |
| 2 | `defensive_and_authorization` | Defensive Tool Design, Authorization |
| 3 | `notifications_on_login` | Notifications |
| 4 | `clean_container_release` | Defensive Tool Design (business-rule path) |
| 5 | `hazmat_held_release_with_elicitation` | Elicitation |
| 6 | `sampling_risk_assessment` | Sampling |
| 7 | `progress_manifest_reconciliation` | Progress Tracking |

`--all` runs them in that order against one server subprocess.

## How the handshake and each interactive concern actually work here

- **Handshake**: `session.initialize()` sends a real `initialize` request
  with the client's declared capabilities, reads back the server's
  declared capabilities and stores them, then sends
  `notifications/initialized`. `server_supports("tools.listChanged")` is
  checked before the agent ever assumes a `tools/list_changed`
  notification will show up later — this mirrors the server's own
  `session.supports()` check from the other direction.
- **Elicitation**: when `request_container_release` hits a hazmat and/or
  actively-held container, the server sends an `elicitation/create`
  request mid-call. `mcp_client.MCPClient._handle_server_request` catches
  it, calls the registered `elicitation_handler`, and writes the answer
  back with the matching request id — the tool call on the server side is
  genuinely blocked on this round trip, not polling.
- **Sampling**: `assess_container_risk` sends a `sampling/createMessage`
  request built from the container's live facts + the relevant policy
  text. The same dispatch mechanism routes it to `sampling_handler`,
  which calls the client's own model — Google Gemini, via
  `GOOGLE_API_KEY`/`GEMINI_API_KEY` (or the offline fallback if no key is
  set) — and returns a real assistant message.
- **Progress**: any `tools/call` for `reconcile_vessel_manifest` passes
  `_meta.progressToken` in its params; the server fires one
  `notifications/progress` per manifest line item it checks, which
  `mcp_client.py` routes straight to `progress_handler` for live
  rendering while the call is still in flight.

## A note on `tools_impl/`

`server.py` (Person 2) imports handler modules under
`mcp_server/tools_impl/` (`session_tools.py`, `query_tools.py`,
`release_tools.py`, `risk_tools.py`, `manifest_tools.py`) that implement
each tool's actual database logic. This agent was built entirely against
the documented, stable contracts in `schemas.py`, `context.py`, and
`server.py` (tool names, input schemas, error codes, and the exact
request/response shapes for `elicitation/create`,
`sampling/createMessage`, and `notifications/progress`), so it does not
depend on those handler internals — but they do need to exist on disk for
the server process to actually start and for these scenarios to run
end-to-end.
