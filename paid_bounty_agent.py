#!/usr/bin/env python3
"""Paid Bounty Triage Agent demo for the CROO Agent Hackathon.

The demo intentionally uses a mock settlement adapter by default. Real wallet
signing and private-key handling stay outside this script.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import time
import urllib.parse
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from uuid import uuid4


SECRET_KEYS = {
    "private_key",
    "seed_phrase",
    "mnemonic",
    "password",
    "cookie",
    "session",
}
SECRET_TEXT_RE = re.compile(
    r"(?i)(private[_-]?key|seed[_ -]?phrase|mnemonic|password|cookie|session[_ -]?(token|secret|key))\s*['\"]?\s*[:=]"
)

CROO_HACKATHON_FACTS = {
    "status": "open",
    "verified_at": "2026-06-17 Asia/Shanghai",
    "dorahacks_url": "https://dorahacks.io/hackathon/croo-hackathon",
    "dorahacks_card_deadline": "2026-07-12 09:00",
    "conservative_submission_deadline": "2026-07-09 23:59 UTC+8",
    "timeline_after_submission": [
        "2026-07-10 to 2026-07-15 internal review shortlisting",
        "2026-07-16 Demo Day",
        "2026-07-17 to 2026-07-23 final judging",
        "2026-07-24 winners announced",
    ],
    "prize_pool": "10,200 USDC / about 10.2K USD",
    "prizes": [
        "1st Grand Champion: 3,500 USD",
        "2nd: 2,500 USD",
        "3rd: 1,500 USD",
        "4th-10th: 300 USD x 7",
        "Most Popular Agent: 300 USD",
        "Most Innovative Agent: 300 USD",
        "Plus: Agent Store featured listing, CROO airdrop whitelist for top 10, permanent listing for valid submissions",
    ],
    "required_submission": [
        "Listed on CROO Agent Store",
        "Integrated with CAP: callable agent, on-chain settlement",
        "Public open-source repo with MIT / Apache 2.0 / similar license",
        "Max 5-minute demo video plus README with setup, SDK methods, integration notes",
        "DoraHacks BUIDL with all required fields completed",
    ],
    "tracks": [
        "Research & Intelligence Agents",
        "Data & Verification Agents",
        "Creator & Content Ops Agents",
        "DeFi / On-chain Ops Agents",
        "Developer Tooling Agents",
        "Open - Any A2A Agents",
    ],
    "judging": {
        "Technical Execution": "30% - robust CAP integration, reliable A2A interactions, payment state handling; bonus for 10+ real CAP orders",
        "A2A Composability": "25% - number, diversity, depth of A2A relationships; CROO supplies aggregated CAP order data",
        "Innovation": "20% - hard-to-replicate use case beyond a normal API marketplace",
        "Usability & Real Adoption": "15% - path to real users, early organic interactions, retention potential",
        "Presentation": "10% - demo clarity, README reproducibility, crisp value proposition",
    },
    "recommended_stack": [
        "CAP SDK: @croo-network/sdk for Node.js or croo-sdk for Python",
        "API: https://api.croo.network",
        "WebSocket: wss://api.croo.network/ws",
        "Default RPC: https://mainnet.base.org",
        "Payment token: USDC deposited to the agent AA wallet visible in the CROO Dashboard",
        "SDK key: CROO_SDK_KEY from the CROO Dashboard",
    ],
}


@dataclass
class TokenEstimate:
    input_tokens: int
    output_tokens: int
    total_tokens: int
    notional_cost_usd: float
    pricing_note: str


@dataclass
class TriageResult:
    url: str
    title: str
    platform: str
    worth_doing: bool
    priority: str
    cash_probability: dict[str, Any]
    token_estimate: TokenEstimate
    recommended_track: str
    delivery_checklist: list[str]
    reasons: list[str]
    risks: list[str]
    next_actions: list[str]
    deadline_note: str


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat(timespec="seconds").replace("+00:00", "Z")


def contains_secret(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            key_l = key.lower()
            if any(secret in key_l for secret in SECRET_KEYS) or contains_secret(child):
                return True
    elif isinstance(value, list):
        return any(contains_secret(item) for item in value)
    elif isinstance(value, str):
        return bool(SECRET_TEXT_RE.search(value))
    return False


def stable_hash(payload: Any, length: int = 16) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()[:length]


def slug_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.replace("www.", "") or "local"
    path = re.sub(r"[^a-zA-Z0-9]+", "-", parsed.path.strip("/")).strip("-")
    return f"{host}-{path or 'task'}".lower()[:72]


def parse_bounty_amount(text: str) -> float | None:
    """Adapted from the local bounty monitor's lightweight amount heuristic."""
    if not text:
        return None
    patterns = [
        r"/bounty\s+\$?([0-9]+(?:\.[0-9]+)?)",
        r"bounty\s+(?:of\s+)?\$?([0-9]+(?:\.[0-9]+)?)",
        r"\$?([0-9]+(?:\.[0-9]+)?)\s*(?:usd|usdc|dollar|bounty|reward|prize)",
        r"\$([1-9][0-9]*(?:\.[0-9]+)?)",
    ]
    for pattern in patterns:
        for match in re.findall(pattern, text, re.IGNORECASE):
            try:
                value = float(match)
            except ValueError:
                continue
            if value > 0:
                return value
    return None


def infer_platform(url: str) -> str:
    host = urllib.parse.urlparse(url).netloc.lower()
    if "dorahacks" in host:
        return "DoraHacks"
    if "kaggle" in host:
        return "Kaggle Community Hackathon"
    if "github" in host:
        return "GitHub Issue"
    if "opire" in host:
        return "Opire"
    if "algora" in host:
        return "Algora"
    return "Generic bounty or hackathon"


def build_context(url: str, title: str | None, body: str | None) -> dict[str, Any]:
    platform = infer_platform(url)
    inferred_title = title or ""
    inferred_body = body or ""
    if "croo-hackathon" in url or "croo-ai-agent-hackathon" in url:
        inferred_title = inferred_title or "CROO Agent Hackathon"
        inferred_body = inferred_body or json.dumps(CROO_HACKATHON_FACTS)
    elif not inferred_title:
        inferred_title = slug_from_url(url).replace("-", " ")
    return {
        "url": url,
        "title": inferred_title,
        "body": inferred_body,
        "platform": platform,
    }


def estimate_tokens(context: dict[str, Any], depth: str) -> TokenEstimate:
    body_tokens = max(700, len(context.get("body", "")) // 4)
    depth_multiplier = {"fast": 1.0, "standard": 1.35, "deep": 2.0}[depth]
    input_tokens = int((1800 + body_tokens) * depth_multiplier)
    output_tokens = int((900 if depth == "fast" else 1400 if depth == "standard" else 2200))
    total = input_tokens + output_tokens
    notional = round(total / 1000 * 0.0025, 4)
    return TokenEstimate(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total,
        notional_cost_usd=notional,
        pricing_note="Demo estimate only: configurable at implementation time; no provider price is hard-coded into settlement.",
    )


def deadline_note_for_url(url: str) -> str:
    if "croo" not in url.lower():
        return "No verified deadline in the demo context; inspect source before committing work."

    deadline = datetime(2026, 7, 9, 23, 59, tzinfo=timezone(timedelta(hours=8)))
    now_shanghai = utc_now().astimezone(timezone(timedelta(hours=8)))
    days_left = max(0, int((deadline - now_shanghai).total_seconds() // 86400))
    return (
        f"Use conservative deadline {CROO_HACKATHON_FACTS['conservative_submission_deadline']} "
        f"({days_left} full days left at runtime). DoraHacks card also shows "
        f"{CROO_HACKATHON_FACTS['dorahacks_card_deadline']}."
    )


def triage(context: dict[str, Any], depth: str) -> TriageResult:
    url = context["url"]
    title = context["title"]
    body = context["body"]
    combined = f"{title}\n{body}\n{url}"
    lower = combined.lower()
    amount = parse_bounty_amount(combined)
    is_croo = "croo" in lower
    is_hackathon = any(word in lower for word in ("hackathon", "buidl", "dorahacks", "kaggle"))
    has_agent_fit = any(word in lower for word in ("agent", "a2a", "cap", "callable", "sdk"))
    has_payment_fit = any(word in lower for word in ("paid", "payment", "settle", "settlement", "usdc", "wallet"))

    score = 50
    reasons: list[str] = []
    risks: list[str] = []

    if is_croo:
        score += 20
        reasons.append("Direct fit with CROO CAP and Agent Store requirements.")
    if is_hackathon:
        score += 10
        reasons.append("Hackathon format rewards a clear 3-minute demo and crisp submission package.")
    if has_agent_fit:
        score += 8
        reasons.append("The requested deliverable is naturally callable as an agent service.")
    if has_payment_fit:
        score += 8
        reasons.append("Payment, settlement, and receipt evidence map directly to judging criteria.")
    if amount and amount >= 1000:
        score += 6
        reasons.append(f"Prize or bounty signal is meaningful: about {amount:g} USD/USDC detected.")
    if "kyc" in lower:
        score -= 5
        risks.append("KYC or eligibility constraints need manual verification before final submission.")
    if "private" in lower and "repo" in lower:
        score -= 20
        risks.append("Private or unverifiable repositories are disqualifying for CROO.")

    score = max(0, min(100, score))
    worth_doing = score >= 65
    priority = "P1_HIGH" if score >= 82 else "P2_MEDIUM" if score >= 65 else "P3_LOW"
    if is_croo:
        cash_probability = {
            "mock_only": 0.12,
            "with_real_cap_orders": 0.28,
            "note": "Judges weight technical CAP execution and A2A order data heavily; mock-only is demo evidence, not final eligibility.",
        }
        recommended_track = "Research & Intelligence Agents"
    else:
        cash_probability = {
            "estimated": 0.18 if worth_doing else 0.07,
            "note": "Generic estimate based on clarity, prize signal, deadline, and implementation risk.",
        }
        recommended_track = "Open - Any A2A Agents"

    delivery_checklist = [
        "Public repo with MIT or Apache-2.0 license",
        "CLI or HTTP-callable agent entrypoint",
        "One paid call record with order lifecycle events",
        "Triage report: priority, token estimate, cash probability, and delivery plan",
        "Mock receipt now; CAP adapter path documented for real USDC settlement",
        "README with setup, SDK methods, integration notes, and no-private-key policy",
        "Max 5-minute demo video script and DoraHacks BUIDL copy",
    ]
    next_actions = [
        "Record one HTTP POST /call demo for judge-friendly proof of callability.",
        "List service on CROO Agent Store and replace MockSettlementAdapter with CAP SDK calls.",
        "Run at least 3 outside-agent or teammate calls before final submission if possible.",
    ]
    if is_croo:
        risks.extend([
            "Final prize eligibility requires real CROO Agent Store listing and CAP on-chain settlement.",
            "The DoraHacks card and timeline image disagree on submission deadline; treat Jul 9 23:59 UTC+8 as safer.",
        ])

    return TriageResult(
        url=url,
        title=title,
        platform=context["platform"],
        worth_doing=worth_doing,
        priority=priority,
        cash_probability=cash_probability,
        token_estimate=estimate_tokens(context, depth),
        recommended_track=recommended_track,
        delivery_checklist=delivery_checklist,
        reasons=reasons,
        risks=risks,
        next_actions=next_actions,
        deadline_note=deadline_note_for_url(url),
    )


class MockSettlementAdapter:
    name = "mock-croo-cap"

    def settle(self, call: dict[str, Any], triage_result: TriageResult, request: dict[str, Any]) -> dict[str, Any]:
        amount = float(request.get("price_usdc", 0.25))
        digest_payload = {
            "call": call,
            "priority": triage_result.priority,
            "amount": amount,
        }
        tx_hash = "mock-croo-" + stable_hash(digest_payload, 32)
        events = [
            {"event": "NEGOTIATION_CREATED", "status": "ok", "at": iso_now()},
            {"event": "ORDER_CREATED", "status": "ok", "at": iso_now()},
            {"event": "ORDER_PAID", "status": "mock_paid", "at": iso_now()},
            {"event": "ORDER_COMPLETED", "status": "delivered", "at": iso_now()},
        ]
        return {
            "adapter": self.name,
            "settlement_status": "MOCK_SETTLED",
            "asset": "USDC",
            "amount": amount,
            "tx_hash": tx_hash,
            "chain": "local mock; real adapter targets Base mainnet via CROO CAP",
            "explorer": None,
            "events": events,
            "human_wallet_confirmation_gate": {
                "required_in_real_mode": True,
                "demo_status": "mocked_after_policy_check",
                "private_keys_handled": False,
            },
            "receipt_digest": stable_hash({"tx": tx_hash, "events": events, "call": call}, 64),
        }


class RealCapAdapter:
    name = "croo-cap-sdk"

    def settle(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise RuntimeError(
            "Real CAP settlement is intentionally not executed by this demo. "
            "Use CROO_SDK_KEY, CROO_API_URL, CROO_WS_URL, and a manually approved "
            "agent AA wallet flow before calling negotiate/pay/deliver."
        )


def make_call_record(request: dict[str, Any], context: dict[str, Any], run_id: str) -> dict[str, Any]:
    return {
        "call_id": run_id,
        "called_at": iso_now(),
        "service": {
            "name": "Paid Bounty Triage Agent",
            "version": "0.1.0",
            "call_surface": ["CLI: paid_bounty_agent.py call", "HTTP: POST /call"],
            "intended_croo_track": "Research & Intelligence Agents",
        },
        "requester_agent": request.get("requester_agent", "demo-requester-agent"),
        "payer_wallet": request.get("payer_wallet", "0xDEMO_PAYER_AA_WALLET"),
        "provider_agent": request.get("provider_agent", "paid-bounty-triage-agent"),
        "provider_wallet": request.get("provider_wallet", "0xDEMO_PROVIDER_AA_WALLET"),
        "price_usdc": float(request.get("price_usdc", 0.25)),
        "input": {
            "url": context["url"],
            "title": context["title"],
            "platform": context["platform"],
        },
        "cap_lifecycle_model": [
            "negotiate_order",
            "accept_negotiation",
            "pay_order",
            "deliver_order",
            "get_delivery",
        ],
    }


def build_settlement_request(call: dict[str, Any], triage_result: TriageResult, request: dict[str, Any]) -> dict[str, Any]:
    return {
        "settlement_request_id": "set_" + stable_hash(call),
        "created_at": iso_now(),
        "mode": request.get("settlement_mode", "mock"),
        "asset": "USDC",
        "amount": call["price_usdc"],
        "payer_wallet": call["payer_wallet"],
        "provider_wallet": call["provider_wallet"],
        "purpose": f"Paid triage for {triage_result.url}",
        "risk_gate": {
            "secret_material_detected": contains_secret(request),
            "requires_human_wallet_confirmation": True,
            "block_real_settlement_if_secret_detected": True,
        },
        "real_cap_replacement": {
            "sdk": "croo-sdk or @croo-network/sdk",
            "required_env": ["CROO_API_URL", "CROO_WS_URL", "CROO_SDK_KEY", "BASE_RPC_URL optional"],
            "methods": ["negotiate_order", "pay_order", "deliver_order", "get_delivery"],
            "wallet_note": "Deposit USDC to the agent AA wallet in CROO Dashboard; never paste private keys into this demo.",
        },
    }


def render_markdown(triage_result: TriageResult, receipt: dict[str, Any]) -> str:
    lines = [
        f"# Paid Bounty Triage Report",
        "",
        f"- URL: {triage_result.url}",
        f"- Platform: {triage_result.platform}",
        f"- Priority: {triage_result.priority}",
        f"- Worth doing: {str(triage_result.worth_doing).lower()}",
        f"- Recommended track: {triage_result.recommended_track}",
        f"- Token estimate: {triage_result.token_estimate.total_tokens} tokens, notional ${triage_result.token_estimate.notional_cost_usd}",
        f"- Receipt: {receipt['settlement_status']} / {receipt['tx_hash']}",
        f"- Deadline: {triage_result.deadline_note}",
        "",
        "## Reasons",
    ]
    lines.extend(f"- {item}" for item in triage_result.reasons)
    lines.extend(["", "## Risks"])
    lines.extend(f"- {item}" for item in triage_result.risks)
    lines.extend(["", "## Delivery Checklist"])
    lines.extend(f"- {item}" for item in triage_result.delivery_checklist)
    lines.extend(["", "## Next Actions"])
    lines.extend(f"- {item}" for item in triage_result.next_actions)
    return "\n".join(lines) + "\n"


def render_html(triage_result: TriageResult, call: dict[str, Any], receipt: dict[str, Any]) -> str:
    rows = {
        "Call ID": call["call_id"],
        "Priority": triage_result.priority,
        "Worth doing": str(triage_result.worth_doing),
        "Price": f"{call['price_usdc']} USDC",
        "Settlement": receipt["settlement_status"],
        "Mock tx": receipt["tx_hash"],
        "Deadline": triage_result.deadline_note,
    }
    row_html = "\n".join(
        f"<tr><th>{html.escape(key)}</th><td>{html.escape(value)}</td></tr>"
        for key, value in rows.items()
    )
    checklist = "\n".join(f"<li>{html.escape(item)}</li>" for item in triage_result.delivery_checklist)
    reasons = "\n".join(f"<li>{html.escape(item)}</li>" for item in triage_result.reasons)
    risks = "\n".join(f"<li>{html.escape(item)}</li>" for item in triage_result.risks)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Paid Bounty Triage Receipt</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #172018; background: #f7f8f4; }}
    main {{ max-width: 920px; margin: auto; }}
    h1 {{ font-size: 34px; margin-bottom: 8px; }}
    .tag {{ display: inline-block; padding: 4px 8px; border: 1px solid #172018; border-radius: 6px; margin-right: 8px; }}
    table {{ width: 100%; border-collapse: collapse; margin: 24px 0; background: #fff; }}
    th, td {{ text-align: left; border-bottom: 1px solid #d8decf; padding: 12px; vertical-align: top; }}
    th {{ width: 180px; }}
    section {{ margin: 24px 0; }}
    code {{ background: #e8ecdf; padding: 2px 5px; border-radius: 4px; }}
  </style>
</head>
<body>
<main>
  <h1>Paid Bounty Triage Agent</h1>
  <p><span class="tag">callable</span><span class="tag">paid</span><span class="tag">mock receipt</span></p>
  <table>{row_html}</table>
  <section><h2>Why this is worth doing</h2><ul>{reasons}</ul></section>
  <section><h2>Risks</h2><ul>{risks}</ul></section>
  <section><h2>Delivery Checklist</h2><ul>{checklist}</ul></section>
  <p>Real CAP mode replaces the mock adapter with CROO SDK calls after manual wallet approval.</p>
</main>
</body>
</html>
"""


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_call(request: dict[str, Any], out_dir: Path, run_id: str | None = None) -> dict[str, Any]:
    if contains_secret(request):
        raise ValueError("Request contains secret-like fields; refusing to create a settlement artifact.")

    url = request.get("url")
    if not url:
        raise ValueError("url is required")

    run_id = run_id or f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:6]}"
    run_dir = out_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    context = build_context(url, request.get("title"), request.get("body"))
    triage_result = triage(context, request.get("depth", "standard"))
    call = make_call_record(request, context, run_id)
    settlement_request = build_settlement_request(call, triage_result, request)

    mode = request.get("settlement_mode", "mock")
    adapter = MockSettlementAdapter() if mode == "mock" else RealCapAdapter()
    receipt = adapter.settle(call, triage_result, request)

    result = {
        "run_dir": str(run_dir),
        "call": call,
        "triage": asdict(triage_result),
        "settlement_request": settlement_request,
        "receipt": receipt,
    }

    write_json(run_dir / "input.json", request)
    write_json(run_dir / "agent_call.json", call)
    write_json(run_dir / "triage_report.json", asdict(triage_result))
    write_json(run_dir / "settlement_request.json", settlement_request)
    write_json(run_dir / "receipt.json", receipt)
    (run_dir / "triage_report.md").write_text(render_markdown(triage_result, receipt), encoding="utf-8")
    (run_dir / "summary.html").write_text(render_html(triage_result, call, receipt), encoding="utf-8")
    log_lines = [
        f"[{iso_now()}] CALL {call['call_id']} {context['url']}",
        f"[{iso_now()}] TRIAGE priority={triage_result.priority} worth_doing={triage_result.worth_doing}",
        f"[{iso_now()}] SETTLEMENT mode={mode} status={receipt['settlement_status']} amount={receipt['amount']} USDC",
        f"[{iso_now()}] RECEIPT {receipt['tx_hash']} digest={receipt['receipt_digest']}",
        f"[{iso_now()}] ARTIFACTS {run_dir}",
    ]
    (run_dir / "demo.log").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    write_json(run_dir / "result.json", result)
    return result


class AgentHandler(BaseHTTPRequestHandler):
    server_version = "PaidBountyAgent/0.1"

    def _send_json(self, status: int, payload: Any) -> None:
        body = json.dumps(payload, indent=2, sort_keys=True).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json(200, {"ok": True, "service": "Paid Bounty Triage Agent"})
            return
        self._send_json(404, {"error": "not_found", "routes": ["GET /health", "POST /call"]})

    def do_POST(self) -> None:
        if self.path != "/call":
            self._send_json(404, {"error": "not_found", "routes": ["POST /call"]})
            return
        try:
            length = int(self.headers.get("content-length", "0"))
            request = json.loads(self.rfile.read(length).decode() or "{}")
            out_dir = Path(getattr(self.server, "out_dir"))
            result = run_call(request, out_dir, request.get("run_id"))
            response = {
                "ok": True,
                "run_dir": result["run_dir"],
                "triage": result["triage"],
                "receipt": result["receipt"],
            }
            self._send_json(200, response)
        except Exception as exc:  # pragma: no cover - HTTP boundary
            self._send_json(400, {"ok": False, "error": str(exc)})

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write(f"[server] {self.address_string()} {fmt % args}\n")


def print_call_summary(result: dict[str, Any]) -> None:
    triage_result = result["triage"]
    receipt = result["receipt"]
    print("Paid Bounty Triage Agent")
    print(f"run_dir: {result['run_dir']}")
    print(f"priority: {triage_result['priority']}")
    print(f"worth_doing: {triage_result['worth_doing']}")
    print(f"token_estimate: {triage_result['token_estimate']['total_tokens']} tokens")
    print(f"cash_probability: {json.dumps(triage_result['cash_probability'], sort_keys=True)}")
    print(f"receipt: {receipt['settlement_status']} {receipt['amount']} {receipt['asset']} {receipt['tx_hash']}")
    print("artifacts: agent_call.json, triage_report.md, settlement_request.json, receipt.json, summary.html, demo.log")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Paid/callable bounty triage agent demo.")
    sub = parser.add_subparsers(dest="command", required=True)

    call = sub.add_parser("call", help="Run one paid agent call and write artifacts.")
    call.add_argument("--url", required=True)
    call.add_argument("--title")
    call.add_argument("--body")
    call.add_argument("--depth", choices=["fast", "standard", "deep"], default="standard")
    call.add_argument("--price-usdc", type=float, default=0.25)
    call.add_argument("--requester-agent", default="demo-requester-agent")
    call.add_argument("--payer-wallet", default="0xDEMO_PAYER_AA_WALLET")
    call.add_argument("--provider-agent", default="paid-bounty-triage-agent")
    call.add_argument("--provider-wallet", default="0xDEMO_PROVIDER_AA_WALLET")
    call.add_argument("--settlement-mode", choices=["mock", "real"], default="mock")
    call.add_argument("--out-dir", default="artifacts")
    call.add_argument("--run-id")

    serve = sub.add_parser("serve", help="Expose POST /call for requester agents.")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8787)
    serve.add_argument("--out-dir", default="artifacts")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "call":
        request = {
            "url": args.url,
            "title": args.title,
            "body": args.body,
            "depth": args.depth,
            "price_usdc": args.price_usdc,
            "requester_agent": args.requester_agent,
            "payer_wallet": args.payer_wallet,
            "provider_agent": args.provider_agent,
            "provider_wallet": args.provider_wallet,
            "settlement_mode": args.settlement_mode,
        }
        start = time.time()
        try:
            result = run_call(request, Path(args.out_dir), args.run_id)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print_call_summary(result)
        print(f"elapsed_seconds: {time.time() - start:.2f}")
        return 0

    if args.command == "serve":
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        server = ThreadingHTTPServer((args.host, args.port), AgentHandler)
        setattr(server, "out_dir", str(out_dir))
        print(f"Serving Paid Bounty Triage Agent on http://{args.host}:{args.port}")
        print("POST JSON to /call with fields: url, optional title/body, price_usdc, run_id")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nshutting down")
        finally:
            server.server_close()
        return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
