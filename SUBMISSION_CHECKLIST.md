# Submission Checklist

## Local Proof

- [x] CLI call generates triage, settlement request, receipt, log, and HTML summary.
- [x] HTTP `POST /call` works as the callable agent surface.
- [x] Mock USDC settlement creates order lifecycle events.
- [x] Secret-like inputs are rejected before artifacts are written.
- [x] Screenshot is saved at `artifacts/latest-http-demo/run-screenshot.png`.

## Reproduce

```bash
cd /Users/luke/Documents/Codex/赏金/croo-paid-bounty-agent
python3 -m py_compile paid_bounty_agent.py
python3 paid_bounty_agent.py call \
  --url https://dorahacks.io/hackathon/croo-hackathon \
  --title "CROO Agent Hackathon" \
  --price-usdc 0.25 \
  --run-id latest-cli-demo
python3 paid_bounty_agent.py serve --host 127.0.0.1 --port 8787
```

In another terminal:

```bash
curl -sS -X POST http://127.0.0.1:8787/call \
  -H 'content-type: application/json' \
  --data @examples/request.json
```

If `8787` is already occupied, use `8791` or another local port in both commands.

## Before DoraHacks Submission

- [x] Create or select a public GitHub repository: https://github.com/Lukeknow0/paid-bounty-triage-agent
- [x] Push this folder as the repository root.
- [x] Publish release artifact: https://github.com/Lukeknow0/paid-bounty-triage-agent/releases/tag/v0.1.0
- [x] Record a max 5-minute video: rules check, HTTP call, triage report, receipt, CAP replacement plan.
- [x] Replace the demo video placeholder in `docs/dorahacks-submission.md`.
- [ ] If time permits, list the agent on CROO Agent Store and replace mock settlement with real CAP SDK calls.

## External Actions That Need Manual Confirmation

- Publishing to GitHub.
- Creating/listing the agent in CROO Agent Store.
- Funding the agent AA wallet with USDC.
- Any wallet signature or transaction.
- Submitting the DoraHacks BUIDL form.
