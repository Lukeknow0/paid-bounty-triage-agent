# CROO Hackathon Rules Check

Verified on 2026-06-17 Asia/Shanghai from the DoraHacks CROO page, the DoraHacks detail page, the Kaggle mirror, and CROO SDK/docs pages.

## Status

- The hackathon is still open for submissions.
- DoraHacks summary card shows "24 days left for submission" at verification time.
- DoraHacks card deadline: `2026/07/12 09:00`.
- Detail-page timeline image says submission deadline: `Jul 9 23:59 UTC+8`.
- Demo planning should use the earlier `2026-07-09 23:59 UTC+8` deadline as the internal safety cutoff.

## Awards

- Incentive pool: `10,200 USDC` / about `$10.2K`.
- 1st Grand Champion: `$3,500`.
- 2nd: `$2,500`.
- 3rd: `$1,500`.
- 4th-10th: `$300 x 7`.
- Most Popular Agent: `$300`.
- Most Innovative Agent: `$300`.
- Plus: Agent Store featured listing, `$CROO` airdrop whitelist for top 10, permanent listing for every valid submission.

## Technical Requirements

Every BUIDL must satisfy all five:

- Listed on CROO Agent Store.
- Integrated with CAP: callable and settles on-chain.
- Open source public repo with MIT, Apache 2.0, or similar permissive license.
- Demo plus README: max 5-minute video, setup instructions, SDK methods used, integration notes.
- DoraHacks BUIDL filed with all required fields completed.

## Judging

- Technical Execution: 30%. Robust CAP integration, reliable A2A interactions, payment state handling. Bonus for 10+ real CAP orders.
- A2A Composability: 25%. Number, diversity, and depth of A2A relationships. CROO supplies aggregated CAP order data to judges.
- Innovation: 20%. Hard-to-replicate use case beyond a normal API marketplace.
- Usability & Real Adoption: 15%. Path to real users, early organic interactions, retention potential.
- Presentation: 10%. Demo clarity, README reproducibility, crisp value proposition.

## Recommended Chain, Wallet, SDK

- SDKs: `@croo-network/sdk` for Node.js and `croo-sdk` for Python.
- API: `https://api.croo.network`.
- WebSocket: `wss://api.croo.network/ws`.
- Default RPC: `https://mainnet.base.org`, so the practical chain target is Base mainnet unless overridden.
- Payment asset: USDC.
- Wallet note from SDK docs: payment tokens should be deposited to the agent AA wallet visible in the CROO Dashboard, not the controller address.
- Secret policy for this demo: no private keys, seed phrases, cookies, or wallet sessions are accepted. Real wallet signing is a manual confirmation gate.

## Submission Format

- Public GitHub, GitLab, or Bitbucket link is required.
- Demo video is required.
- Public repo should include setup instructions, SDK methods used, CAP integration notes, and a reproducible call/receipt artifact.
- Recommended tracks for this demo: `Research & Intelligence Agents` and optionally `Open - Any A2A Agents`.

## Source Links

- DoraHacks: https://dorahacks.io/hackathon/croo-hackathon
- DoraHacks detail: https://dorahacks.io/hackathon/croo-hackathon/detail
- Kaggle mirror: https://www.kaggle.com/competitions/croo-ai-agent-hackathon-10-k-usd-prize-pool/overview
- CROO CAP: https://cap.croo.network/
- Node SDK: https://github.com/CROO-Network/node-sdk
- Python SDK: https://github.com/CROO-Network/python-sdk
