# PAYPAL HOLD PLAYBOOK (UU-2)
New-service PayPal accounts routinely hold inbound "goods & services" payments up to
21 days (no tracking number to release them). Service businesses hit this on early
sales. Defenses, in order:
1. Confirmation email (template in pending_replies/) says: payment may show a temporary
   hold on PayPal's side; delivery still starts immediately; if a hold appears, we
   deliver anyway and the hold clears on completion.
2. Delivery-evidence packet MANDATORY from sale #1: dated intake, deliverable, email
   thread — zipped per customer (ops policy already requires this).
3. Offer alternative rails in every confirmation: BTC/stablecoin invoice (Casey issues
   on request) — priced in USD, converted same-day (volatility policy UU-11).
4. Ledger: record hold status per settlement in CLOSED_CASH_LOOP (fields: settled /
   held / released-date).
5. If PayPal limits the account: full stop on that rail, notify Casey via HA, switch
   confirmations to alternative rails only. Never open a second personal account to
   route around a limit (that is how accounts get permanently banned).
