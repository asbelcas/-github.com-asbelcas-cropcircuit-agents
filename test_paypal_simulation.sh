#!/bin/bash

# PayPal Simulation Test Script
# Tests the PayPal integration without real API calls

echo "======================================================================"
echo "  PAYPAL SIMULATION TEST"
echo "======================================================================"
echo ""
echo "This script tests the PayPal integration in SIMULATION mode."
echo "No real money will be transferred."
echo ""
echo "Press Ctrl+C to cancel, or wait 3 seconds to continue..."
sleep 3

# Create test directories
mkdir -p payments state logs

# Create a test state with some earnings
cat > state/rm_qpt_state.json << 'EOF'
{
  "total_earned": 0,
  "total_spent": 0,
  "net_profit": 0,
  "transactions": [],
  "experiments": [],
  "paypal_deposited": 0,
  "paypal_pending": 0,
  "start_time": "$(date -Iseconds)",
  "uptime_hours": 0,
  "mode": "simulation"
}
EOF

echo ""
echo "✓ Test state created"
echo ""

# Run a test deposit
python3 << 'PYEOF'
import json
import os
from datetime import datetime
import uuid

# Configuration
PAYPAL_ACCOUNT = "asbelcas@gmail.com"

def simulate_deposit(amount, source):
    """Simulate a PayPal deposit"""
    transaction_id = f"TX_{datetime.now().strftime('%y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    deposit_record = {
        "timestamp": datetime.now().isoformat(),
        "paypal_account": PAYPAL_ACCOUNT,
        "amount": amount,
        "transaction_id": transaction_id,
        "source": source,
        "status": "simulation_mode",
        "note": "This is a simulated deposit - no real money transferred"
    }
    
    # Save deposit record
    filename = f"payments/deposit_{transaction_id}.json"
    with open(filename, 'w') as f:
        json.dump(deposit_record, f, indent=2)
    
    return deposit_record

# Simulate some earnings
print("Simulating earnings...")
print("")

deposits = [
    (15.50, "affiliate_commission"),
    (23.75, "microtask_completion"),
    (8.25, "content_monetization"),
    (45.00, "digital_product_sale"),
]

total = 0
for amount, source in deposits:
    record = simulate_deposit(amount, source)
    print(f"✓ Deposited ${amount:.2f} from {source}")
    print(f"  Transaction ID: {record['transaction_id']}")
    print(f"  Status: {record['status']}")
    print("")
    total += amount

# Update state
state_file = "state/rm_qpt_state.json"
if os.path.exists(state_file):
    with open(state_file, 'r') as f:
        state = json.load(f)
    state['total_earned'] = total
    state['paypal_deposited'] = total
    state['paypal_pending'] = 0
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)

print("=" * 50)
print(f"TOTAL SIMULATED DEPOSITS: ${total:.2f}")
print("=" * 50)
print("")
print("Deposit records saved to: payments/")
print("")
print("NOTE: These are SIMULATED deposits. To enable real PayPal")
print("transfers, you need to:")
print("  1. Get PayPal Business Account")
print("  2. Apply for Payouts API")
print("  3. Install PayPal SDK")
print("  4. Configure API credentials")
print("")
print("See PAYPAL_SETUP_GUIDE.md for full instructions.")

PYEOF

echo ""
echo "======================================================================"
echo "  SIMULATION COMPLETE"
echo "======================================================================"
echo ""
echo "Files created:"
ls -la payments/
echo ""
echo "Current state:"
cat state/rm_qpt_state.json | python3 -m json.tool
