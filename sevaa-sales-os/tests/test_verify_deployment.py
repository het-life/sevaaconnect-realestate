from __future__ import annotations

import json

from scripts import verify_deployment as vd


def response(status: int, payload) -> vd.Response:
    if isinstance(payload, (dict, list)):
        body = json.dumps(payload).encode("utf-8")
        content_type = "application/json"
    else:
        body = str(payload).encode("utf-8")
        content_type = "text/html"
    return vd.Response(status=status, body=body, content_type=content_type)


def test_verify_happy_path_is_non_mutating_except_permission_probe(monkeypatch):
    calls = []

    def fake_request(base_url, path, *, token=None, method="GET", payload=None, timeout=10.0):
        calls.append((path, token, method, payload))
        if path == "/api/health":
            return response(200, {"status": "ok"})
        if path == "/api/v2/auth/me" and token is None:
            return response(401, {"detail": "bearer token required"})
        if path == "/api/v2/auth/me" and token == "founder":
            return response(200, {"role": "founder"})
        if path == "/api/v2/auth/me" and token == "automation":
            return response(200, {"role": "automation"})
        if path == "/api/v2/approvals/0/decision":
            return response(403, {"detail": "founder role required"})
        if path == "/quote":
            return response(200, "<html>Request a quote enquiry</html>")
        raise AssertionError(f"unexpected request: {path}")

    monkeypatch.setattr(vd, "request", fake_request)

    assert vd.verify("https://example.test", "founder", "automation", 1.0) is True
    assert [c[0] for c in calls] == [
        "/api/health",
        "/api/v2/auth/me",
        "/api/v2/auth/me",
        "/api/v2/auth/me",
        "/api/v2/approvals/0/decision",
        "/quote",
    ]
    assert [c for c in calls if c[2] != "GET"] == [
        (
            "/api/v2/approvals/0/decision",
            "automation",
            "POST",
            {"decision": "rejected", "note": "deployment preflight permission check"},
        )
    ]


def test_main_rejects_equal_tokens(monkeypatch):
    monkeypatch.setenv("SEVAA_FOUNDER_TOKEN", "same")
    monkeypatch.setenv("SEVAA_AUTOMATION_TOKEN", "same")
    assert vd.main(["--base-url", "https://example.test"]) == 2


def test_main_requires_https_by_default(monkeypatch):
    monkeypatch.setenv("SEVAA_FOUNDER_TOKEN", "founder")
    monkeypatch.setenv("SEVAA_AUTOMATION_TOKEN", "automation")
    assert vd.main(["--base-url", "http://example.test"]) == 2
