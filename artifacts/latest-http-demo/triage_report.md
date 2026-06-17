# Paid Bounty Triage Report

- URL: https://dorahacks.io/hackathon/croo-hackathon
- Platform: DoraHacks
- Priority: P1_HIGH
- Worth doing: true
- Recommended track: Research & Intelligence Agents
- Token estimate: 4775 tokens, notional $0.0119
- Receipt: MOCK_SETTLED / mock-croo-265d73834407497f3690c1dc8350c50f
- Deadline: Use conservative deadline 2026-07-09 23:59 UTC+8 (22 full days left at runtime). DoraHacks card also shows 2026-07-12 09:00.

## Reasons
- Direct fit with CROO CAP and Agent Store requirements.
- Hackathon format rewards a clear 3-minute demo and crisp submission package.
- The requested deliverable is naturally callable as an agent service.
- Payment, settlement, and receipt evidence map directly to judging criteria.

## Risks
- Final prize eligibility requires real CROO Agent Store listing and CAP on-chain settlement.
- The DoraHacks card and timeline image disagree on submission deadline; treat Jul 9 23:59 UTC+8 as safer.

## Delivery Checklist
- Public repo with MIT or Apache-2.0 license
- CLI or HTTP-callable agent entrypoint
- One paid call record with order lifecycle events
- Triage report: priority, token estimate, cash probability, and delivery plan
- Mock receipt now; CAP adapter path documented for real USDC settlement
- README with setup, SDK methods, integration notes, and no-private-key policy
- Max 5-minute demo video script and DoraHacks BUIDL copy

## Next Actions
- Record one HTTP POST /call demo for judge-friendly proof of callability.
- List service on CROO Agent Store and replace MockSettlementAdapter with CAP SDK calls.
- Run at least 3 outside-agent or teammate calls before final submission if possible.
