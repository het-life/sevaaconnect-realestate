from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OpenClawClientError(RuntimeError):
    """Raised when the Sales OS rejects or cannot complete an automation request."""


Transport = Callable[[str, str, dict[str, str], dict[str, Any] | None], Any]


class OpenClawClient:
    """Narrow automation client for the hardened SEVAA v2 API.

    The client intentionally has no founder approval-decision operation. It is
    designed for the automation credential only and verifies that identity
    before a workflow proceeds.
    """

    def __init__(
        self,
        base_url: str,
        token: str,
        actor: str = "openclaw",
        transport: Transport | None = None,
    ) -> None:
        if not token:
            raise ValueError("automation token is required")
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.actor = actor.strip() or "openclaw"
        self._transport = transport or self._http_transport
        self._identity: dict[str, Any] | None = None

    @classmethod
    def from_env(cls, actor: str = "openclaw") -> "OpenClawClient":
        token = os.getenv("SEVAA_AUTOMATION_TOKEN", "").strip()
        if not token:
            raise OpenClawClientError("SEVAA_AUTOMATION_TOKEN is required")
        base_url = os.getenv("SEVAA_BASE_URL", "http://127.0.0.1:8000").strip()
        return cls(base_url=base_url, token=token, actor=actor)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "X-Actor": self.actor,
            "Accept": "application/json",
        }

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> Any:
        headers = self._headers()
        if extra_headers:
            headers.update(extra_headers)
        return self._transport(method, path, headers, payload)

    def _http_transport(
        self,
        method: str,
        path: str,
        headers: dict[str, str],
        payload: dict[str, Any] | None,
    ) -> Any:
        body = None
        if payload is not None:
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            headers = {**headers, "Content-Type": "application/json"}
        request = Request(
            f"{self.base_url}{path}",
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=20) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                data = json.loads(raw)
                detail = data.get("detail", data)
            except json.JSONDecodeError:
                detail = raw or exc.reason
            raise OpenClawClientError(f"HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise OpenClawClientError(f"connection failed: {exc.reason}") from exc
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise OpenClawClientError("server returned non-JSON response") from exc

    def ensure_automation_identity(self) -> dict[str, Any]:
        identity = self._request("GET", "/api/v2/auth/me")
        if not isinstance(identity, dict) or identity.get("role") != "automation":
            role = identity.get("role") if isinstance(identity, dict) else None
            raise OpenClawClientError(
                f"automation credential required; server resolved role={role!r}"
            )
        self._identity = identity
        return identity

    def _ready(self) -> None:
        if self._identity is None:
            self.ensure_automation_identity()

    def daily_brief(self) -> dict[str, Any]:
        self._ready()
        return self._request("GET", "/api/v2/internal/daily-brief")

    def list_approvals(self, status: str = "pending") -> list[dict[str, Any]]:
        self._ready()
        return self._request("GET", f"/api/v2/approvals?status={status}")

    def list_followups(self, state: str = "all") -> list[dict[str, Any]]:
        self._ready()
        return self._request("GET", f"/api/v2/followups?state={state}")

    def create_lead(
        self,
        payload: dict[str, Any],
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        self._ready()
        key = idempotency_key or f"openclaw-{uuid.uuid4()}"
        return self._request(
            "POST",
            "/api/v2/leads",
            payload,
            {"Idempotency-Key": key},
        )

    def create_proposal(
        self,
        lead_id: int,
        amount: int,
        scope_summary: str,
    ) -> dict[str, Any]:
        self._ready()
        return self._request(
            "POST",
            f"/api/v2/leads/{lead_id}/proposals",
            {"amount": amount, "scope_summary": scope_summary},
        )

    def submit_proposal(self, proposal_id: int) -> dict[str, Any]:
        self._ready()
        return self._request("POST", f"/api/v2/proposals/{proposal_id}/submit")

    def schedule_followup(
        self,
        lead_id: int,
        due_at: str,
        channel: str = "manual",
        draft_message: str | None = None,
    ) -> dict[str, Any]:
        self._ready()
        return self._request(
            "POST",
            f"/api/v2/leads/{lead_id}/followups",
            {
                "due_at": due_at,
                "channel": channel,
                "draft_message": draft_message,
            },
        )

    def complete_followup(self, followup_id: int, note: str | None = None) -> dict[str, Any]:
        self._ready()
        return self._request(
            "POST",
            f"/api/v2/followups/{followup_id}/complete",
            {"note": note},
        )


def _json_payload(value: str) -> dict[str, Any]:
    try:
        payload = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"invalid JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise argparse.ArgumentTypeError("JSON payload must be an object")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Authenticated OpenClaw client for SEVAA Sales OS")
    parser.add_argument("--actor", default="openclaw", help="Audit actor label")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("me")
    sub.add_parser("brief")

    approvals = sub.add_parser("approvals")
    approvals.add_argument("--status", choices=["pending", "approved", "rejected", "all"], default="pending")

    followups = sub.add_parser("followups")
    followups.add_argument("--state", choices=["all", "pending", "overdue", "completed"], default="all")

    lead = sub.add_parser("create-lead")
    lead.add_argument("--json", required=True, type=_json_payload, dest="payload")
    lead.add_argument("--idempotency-key")

    proposal = sub.add_parser("create-proposal")
    proposal.add_argument("lead_id", type=int)
    proposal.add_argument("--amount", required=True, type=int)
    proposal.add_argument("--scope", required=True)

    submit = sub.add_parser("submit-proposal")
    submit.add_argument("proposal_id", type=int)

    schedule = sub.add_parser("schedule-followup")
    schedule.add_argument("lead_id", type=int)
    schedule.add_argument("--due-at", required=True, help="ISO-8601 timestamp")
    schedule.add_argument("--channel", choices=["manual", "phone", "email", "whatsapp"], default="manual")
    schedule.add_argument("--draft-message")

    complete = sub.add_parser("complete-followup")
    complete.add_argument("followup_id", type=int)
    complete.add_argument("--note")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        client = OpenClawClient.from_env(actor=args.actor)
        if args.command == "me":
            result = client.ensure_automation_identity()
        elif args.command == "brief":
            result = client.daily_brief()
        elif args.command == "approvals":
            result = client.list_approvals(args.status)
        elif args.command == "followups":
            result = client.list_followups(args.state)
        elif args.command == "create-lead":
            result = client.create_lead(args.payload, args.idempotency_key)
        elif args.command == "create-proposal":
            result = client.create_proposal(args.lead_id, args.amount, args.scope)
        elif args.command == "submit-proposal":
            result = client.submit_proposal(args.proposal_id)
        elif args.command == "schedule-followup":
            result = client.schedule_followup(
                args.lead_id,
                args.due_at,
                channel=args.channel,
                draft_message=args.draft_message,
            )
        elif args.command == "complete-followup":
            result = client.complete_followup(args.followup_id, args.note)
        else:  # pragma: no cover - argparse guarantees a known command
            raise OpenClawClientError(f"unknown command: {args.command}")
    except (OpenClawClientError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
