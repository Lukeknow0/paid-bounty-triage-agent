# Real CROO CAP Adapter Notes

The demo defaults to `MockSettlementAdapter` because it must not handle private keys or sign transactions automatically. To make the submission prize-eligible, replace the adapter with the official CROO SDK lifecycle after the agent is created in the CROO Dashboard.

## Required Setup

- `CROO_API_URL=https://api.croo.network`
- `CROO_WS_URL=wss://api.croo.network/ws`
- `CROO_SDK_KEY=croo_sk_...`
- Optional `BASE_RPC_URL`, defaulting to `https://mainnet.base.org`
- USDC deposited to the agent AA wallet shown in the CROO Dashboard

Do not paste private keys, seed phrases, cookies, or wallet session material into this repo or runtime.

## Python SDK Lifecycle

```python
from croo import AgentClient, Config, DeliverableType, DeliverOrderRequest

client = AgentClient(
    Config(base_url=os.environ["CROO_API_URL"], ws_url=os.environ["CROO_WS_URL"]),
    os.environ["CROO_SDK_KEY"],
)

# Requester side
neg = await client.negotiate_order({
    "service_id": os.environ["CROO_TARGET_SERVICE_ID"],
    "requirements": json.dumps(request_payload),
})

# Provider side
order = await client.accept_negotiation(neg.negotiation_id)

# Requester side after manual wallet approval and AA wallet funding
payment = await client.pay_order(order.order_id)

# Provider side
await client.deliver_order(order.order_id, DeliverOrderRequest(
    deliverable_type=DeliverableType.TEXT,
    deliverable_text=json.dumps(triage_result),
))

# Requester side
delivery = await client.get_delivery(order.order_id)
```

## Adapter Boundary

The existing demo expects an adapter method with this shape:

```python
def settle(self, call: dict, triage_result: TriageResult, request: dict) -> dict:
    ...
```

The returned dict should preserve these keys so the rest of the demo does not change:

- `adapter`
- `settlement_status`
- `asset`
- `amount`
- `tx_hash`
- `chain`
- `explorer`
- `events`
- `human_wallet_confirmation_gate`
- `receipt_digest`

## Demo-Day Honesty

If real CAP orders are not complete before submission, say plainly:

> This build demonstrates the paid/callable and receipt loop with mock settlement. The production CAP adapter boundary is isolated and documented; final on-chain eligibility requires CROO Agent Store listing, AA wallet funding, and SDK-backed order payment.
