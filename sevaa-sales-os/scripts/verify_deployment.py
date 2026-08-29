#!/usr/bin/env python3
"""Read-only deployment verification for SEVAA Sales OS.

This script validates the public deployment boundary without creating leads,
resolving approvals, or touching payment state. It intentionally uses only the
Python standard library so it can run from a clean operator machine.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class Response:
    status: int
    body: bytes
    content_type: str

    def json(self) -> Any:
        return json.loads(self.body.decode("utf-8"))


def request(
    base_url: str,
    path: str,
    *,
    token: str | None = None,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: float = 10.0,
) -> Response:
    headers = {"User-Agent": "sevaa-deployment-preflight/1.0"}
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["X-Actor"] = "deployment-preflight"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = Request(f"{base_url}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as resp:
            return Response(
                status=int(resp.status),
                body=resp.read(),
                content_type=resp.headers.get("Content-Type", ""),
            )
    except HTTPError as exc:
        return Response(
            status=int(exc.code),
            body=exc.read(),
            content_type=exc.headers.get("Content-Type", "") if exc.headers else "",
        )
    except URLError as exc:
        raise RuntimeError(f"request failed for {path}: {exc.reason}") from exc


def expect(label: str, condition: bool, detail: str) -> bool:
    prefix = "PASS" if condition else "FAIL"
    print(f"[{prefix}] {label}: {detail}")
    return condition


def verify(base_url: str, founder_token: str, automation_token: str, timeout: float) -> bool:
    checks: list[bool] = []

    health = request(base_url, "/api/health", timeout=timeout)
    health_payload = None
    if health.status == 200:
        try:
            health_payload = health.json()
        except (json.JSONDecodeError, UnicodeDecodeError):
            health_payload = None
    checks.append(
        expect(
            "health",
            health.status == 200 and isinstance(health_payload, dict) and health_payload.get("status") == "ok",
            f"HTTP {health.status}; status={health_payload.get('status') if isinstance(health_payload, dict) else 'invalid-json'}",
        )
    )

    unauth = request(base_url, "/api/v2/auth/me", timeout=timeout)
    checks.append(expect("unauthenticated v2 blocked", unauth.status == 401, f"HTTP {unauth.status}"))

    founder = request(base_url, "/api/v2/auth/me", token=founder_token, timeout=timeout)
    founder_payload = None
    if founder.status == 200:
        try:
            founder_payload = founder.json()
        except (json.JSONDecodeError, UnicodeDecodeError):
            founder_payload = None
    checks.append(
        expect(
            "founder role",
            founder.status == 200 and isinstance(founder_payload, dict) and founder_payload.get("role") == "founder",
            f"HTTP {founder.status}; role={founder_payload.get('role') if isinstance(founder_payload, dict) else 'invalid-json'}",
        )
    )

    automation = request(base_url, "/api/v2/auth/me", token=automation_token, timeout=timeout)
    automation_payload = None
    if automation.status == 200:
        try:
            automation_payload = automation.json()
        except (json.JSONDecodeError, UnicodeDecodeError):
            automation_payload = None
    checks.append(
        expect(
            "automation role",
            automation.status == 200 and isinstance(automation_payload, dict) and automation_payload.get("role") == "automation",
            f"HTTP {automation.status}; role={automation_payload.get('role') if isinstance(automation_payload, dict) else 'invalid-json'}",
        )
    )

    denial = request(
        base_url,
        "/api/v2/approvals/0/decision",
        token=automation_token,
        method="POST",
        payload={"decision": "rejected", "note": "deployment preflight permission check"},
        timeout=timeout,
    )
    checks.append(
        expect(
            "automation cannot resolve approvals",
            denial.status == 403,
            f"HTTP {denial.status}; expected 403 before resource lookup",
        )
    )

    quote = request(base_url, "/quote", timeout=timeout)
    quote_text = quote.body.decode("utf-8", errors="replace").lower()
    checks.append(
        expect(
            "public quote page",
            quote.status == 200 and ("quote" in quote_text or "enquir" in quote_text),
            f"HTTP {quote.status}; {len(quote.body)} bytes",
        )
    )

    passed = all(checks)
    print(f"\nResult: {'PASS' if passed else 'FAIL'} ({sum(checks)}/{len(checks)} checks passed)")
    return passed


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify a deployed SEVAA Sales OS instance without mutating funnel data.")
    parser.add_argument("--base-url", default=os.getenv("SEVAA_BASE_URL"), help="Public HTTPS base URL (or SEVAA_BASE_URL).")
    parser.add_argument("--timeout", type=float, default=10.0, help="Per-request timeout in seconds.")
    parser.add_argument("--allow-http", action="store_true", help="Allow plain HTTP for local testing only.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if not args.base_url:
        print("ERROR: provide --base-url or SEVAA_BASE_URL", file=sys.stderr)
        return 2

    base_url = args.base_url.rstrip("/")
    parsed = urlparse(base_url)
    if parsed.scheme not in ({"https", "http"} if args.allow_http else {"https"}) or not parsed.netloc:
        requirement = "http(s)" if args.allow_http else "https"
        print(f"ERROR: base URL must be a valid {requirement} URL", file=sys.stderr)
        return 2

    founder_token = os.getenv("SEVAA_FOUNDER_TOKEN")
    automation_token = os.getenv("SEVAA_AUTOMATION_TOKEN")
    if not founder_token or not automation_token:
        print("ERROR: SEVAA_FOUNDER_TOKEN and SEVAA_AUTOMATION_TOKEN must be set in the environment", file=sys.stderr)
        return 2
    if founder_token == automation_token:
        print("ERROR: founder and automation tokens must be different", file=sys.stderr)
        return 2

    try:
        return 0 if verify(base_url, founder_token, automation_token, args.timeout) else 1
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
