# DoraHacks Submission Copy

## Project Name

Paid Bounty Triage Agent

## Tagline

A paid, callable CROO-style agent that turns a bounty or hackathon link into a go/no-go decision, token-cost estimate, delivery checklist, and auditable payment receipt.

## Track

Primary: Research & Intelligence Agents

Secondary: Open - Any A2A Agents

## Short Description

Paid Bounty Triage Agent helps builders decide whether a bounty or hackathon is worth doing before spending agent time. A requester submits a link, pays for a triage call, receives a structured priority report, and gets a settlement receipt. The demo uses a mock CROO CAP settlement adapter today and documents the exact adapter boundary for real CAP SDK order negotiation, USDC payment, delivery, and receipt retrieval.

## Long Description

Builders waste time chasing unclear bounties. This agent packages the first decision into a paid, callable service:

- Input: bounty, issue, or hackathon URL.
- Output: priority, worth-doing verdict, estimated token cost, cash probability, recommended track, risks, and delivery checklist.
- Commerce loop: call record, payment intent, mock USDC settlement, receipt digest, and deliverable artifacts.
- Real CAP path: replace `MockSettlementAdapter` with CROO SDK methods `negotiate_order`, `pay_order`, `deliver_order`, and `get_delivery` after manual wallet approval.

For the CROO hackathon, the agent itself demonstrates the core theme: agents can be discoverable, priced, callable, paid, and receipt-producing. It is intentionally small enough for judges to understand in three minutes while preserving the key production boundary: no private keys in the agent runtime, and wallet signing remains a human confirmation gate.

## Demo Script

1. Start the local callable agent:

```bash
python3 paid_bounty_agent.py serve --host 127.0.0.1 --port 8787
```

2. From another terminal, call it like a requester agent:

```bash
curl -sS -X POST http://127.0.0.1:8787/call \
  -H 'content-type: application/json' \
  --data @examples/request.json
```

3. Show generated artifacts:

```bash
ls artifacts/latest-http-demo
cat artifacts/latest-http-demo/triage_report.md
cat artifacts/latest-http-demo/receipt.json
```

4. Explain the CAP replacement:

- Requester: `negotiate_order`.
- Provider: `accept_negotiation`.
- Requester: `pay_order` after AA wallet is funded and manually approved.
- Provider: `deliver_order`.
- Requester: `get_delivery`.

## README / SDK Methods Used

The README documents:

- CLI and HTTP call surfaces.
- Generated call, triage, settlement, receipt, log, and HTML artifacts.
- Mock settlement mode.
- Real CROO SDK replacement methods.
- Wallet approval gate and no-private-key policy.

## Repository Placeholder

Replace with the public repository URL before submission.

## Demo Video Placeholder

Replace with the final max 5-minute video URL before submission.
