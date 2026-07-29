"""
_smoke_test.py — NOT part of the graded deliverable. A throwaway driver
that plays the role of a minimal MCP client over a real subprocess/stdio
pipe, so Person 2's server can be sanity-checked before Person 3's real
agent exists. Safe to delete once agent/ is built and does this for real.

Run: python3 mcp_server/_smoke_test.py
"""

import json
import subprocess
import sys


def send(proc, msg):
    proc.stdin.write(json.dumps(msg) + "\n")
    proc.stdin.flush()


def recv(proc):
    line = proc.stdout.readline()
    if not line:
        err = proc.stderr.read()
        raise RuntimeError(f"Server closed stdout. stderr:\n{err}")
    return json.loads(line)


_id = 0


def req(proc, method, params=None):
    global _id
    _id += 1
    send(proc, {"jsonrpc": "2.0", "id": _id, "method": method, "params": params or {}})
    return recv(proc)


def notify(proc, method, params=None):
    send(proc, {"jsonrpc": "2.0", "method": method, "params": params or {}})


def call_tool(proc, name, arguments, progress_token=None, on_server_request=None):
    """Call a tool, transparently answering any elicitation/create or
    sampling/createMessage requests the server sends back mid-call using
    on_server_request(msg) -> result, and printing progress notifications."""
    global _id
    _id += 1
    params = {"name": name, "arguments": arguments}
    if progress_token:
        params["_meta"] = {"progressToken": progress_token}
    send(proc, {"jsonrpc": "2.0", "id": _id, "method": "tools/call", "params": params})
    this_id = _id

    while True:
        msg = recv(proc)
        if "method" in msg and "id" not in msg:
            if msg["method"] == "notifications/progress":
                print("  [progress]", msg["params"])
            elif msg["method"] == "notifications/tools/list_changed":
                print("  [notification] tools/list_changed")
            continue
        if "method" in msg and "id" in msg:
            # server -> client request: elicitation/create or sampling/createMessage
            assert on_server_request is not None, f"unexpected server request: {msg}"
            result = on_server_request(msg)
            send(proc, {"jsonrpc": "2.0", "id": msg["id"], "result": result})
            continue
        if msg.get("id") == this_id:
            return msg
        # response to something else (shouldn't happen in this single-flight demo)


def main():
    proc = subprocess.Popen(
        [sys.executable, "-m", "mcp_server.server"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1,
    )

    print("== initialize (declaring elicitation + sampling support) ==")
    resp = req(proc, "initialize", {
        "protocolVersion": "2025-06-18",
        "capabilities": {"elicitation": {}, "sampling": {}},
        "clientInfo": {"name": "smoke-test-client", "version": "0.0.1"},
    })
    print(json.dumps(resp, indent=2))
    notify(proc, "notifications/initialized")

    print("\n== tools/list (anonymous session) ==")
    resp = req(proc, "tools/list")
    names = [t["name"] for t in resp["result"]["tools"]]
    print(names)
    assert "request_container_release" not in names, "should be hidden pre-auth"

    print("\n== defensive validation: bad input (missing required field) ==")
    resp = req(proc, "tools/call", {"name": "get_container_status", "arguments": {}})
    print(json.dumps(resp, indent=2))
    assert "error" in resp

    print("\n== defensive validation: unknown extra field rejected ==")
    resp = req(proc, "tools/call", {
        "name": "get_container_status",
        "arguments": {"container_number": "MSKU100001", "sneaky": "field"},
    })
    print(json.dumps(resp, indent=2))
    assert "error" in resp

    print("\n== unauthenticated write attempt is rejected by the handler ==")
    resp = req(proc, "tools/call", {
        "name": "request_container_release",
        "arguments": {"container_number": "MSKU100001", "release_reason": "test"},
    })
    print(json.dumps(resp, indent=2))
    assert resp["error"]["code"] == -32601 or "error" in resp  # unknown tool pre-auth OR handler rejection

    print("\n== authenticate as dispatcher -> should fire tools/list_changed ==")
    resp = call_tool(proc, "authenticate", {"badge_code": "BADGE-D01"})
    print(json.dumps(resp, indent=2))

    print("\n== tools/list (now dispatcher) ==")
    resp = req(proc, "tools/list")
    names = [t["name"] for t in resp["result"]["tools"]]
    print(names)
    assert "request_container_release" in names

    print("\n== release a CLEAN container (auto-approved, no elicitation) ==")
    resp = call_tool(proc, "request_container_release",
                      {"container_number": "MSKU100001", "release_reason": "docs verified"})
    print(json.dumps(resp, indent=2))

    print("\n== release a HAZMAT+HELD container -> triggers elicitation, we accept ==")

    def answer_confirm_yes(server_req):
        print("  [server->client request]", server_req["method"], server_req["params"]["message"][:80], "...")
        return {"action": "accept", "content": {"confirm": True}}

    resp = call_tool(proc, "request_container_release",
                      {"container_number": "MSKU100004", "release_reason": "consignee requested"},
                      on_server_request=answer_confirm_yes)
    print(json.dumps(resp, indent=2))

    print("\n== authenticate as customs officer, clear the hold ==")
    call_tool(proc, "authenticate", {"badge_code": "BADGE-C01"})
    resp = req(proc, "tools/call", {
        "name": "clear_customs_hold",
        "arguments": {"hold_id": 2, "resolution_notes": "docs received"},
    })
    print(json.dumps(resp, indent=2))

    print("\n== authenticate as supervisor, approve the pending hazmat release ==")
    call_tool(proc, "authenticate", {"badge_code": "BADGE-S01"})
    resp = req(proc, "tools/call", {
        "name": "approve_container_release",
        "arguments": {"release_order_id": 3, "decision": "Approved", "notes": "hazmat docs verified"},
    })
    print(json.dumps(resp, indent=2))

    print("\n== progress tracking: reconcile_vessel_manifest ==")
    resp = call_tool(proc, "reconcile_vessel_manifest", {"vessel_name": "Ever Glory"},
                      progress_token="tok-1")
    print(json.dumps(resp, indent=2))

    print("\n== sampling: assess_container_risk (mocked client model reply) ==")

    def answer_sample(server_req):
        print("  [server->client request] sampling/createMessage")
        return {
            "role": "assistant",
            "content": {"type": "text", "text": "Risk Level: High\nRisk Factors: hazmat + carrier status\n..."},
        }

    resp = call_tool(proc, "assess_container_risk", {"container_number": "MSKU100002"},
                      on_server_request=answer_sample)
    print(json.dumps(resp, indent=2))

    print("\n== resources/list, resources/read ==")
    print(json.dumps(req(proc, "resources/list"), indent=2))
    print(json.dumps(req(proc, "resources/read", {"uri": "policy://hazmat"})["result"]["contents"][0]["uri"], indent=2))

    print("\n== prompts/list ==")
    print(json.dumps(req(proc, "prompts/list"), indent=2))

    proc.stdin.close()
    proc.terminate()
    print("\nALL SMOKE CHECKS PASSED")


if __name__ == "__main__":
    main()
