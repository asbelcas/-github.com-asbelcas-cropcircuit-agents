#!/usr/bin/env python3
"""
RM-QPT Crypto Deposit Test
Tests the cryptocurrency deposit functionality
"""

import os
import sys

# Add core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from crypto_integration import CryptoIntegration, check_crypto_status

def test_deposits():
    """Test crypto deposit functionality"""
    print("=" * 70)
    print("  🧪 TESTING CRYPTO DEPOSITS")
    print("=" * 70)
    print()
    
    # Initialize crypto integration
    crypto = CryptoIntegration()
    print()
    
    # Test different amounts to see auto-selection
    test_amounts = [5.00, 25.00, 150.00, 750.00]
    
    print("Testing automatic crypto selection:")
    print("-" * 50)
    
    for amount in test_amounts:
        crypto_type, crypto_amount = crypto.select_best_crypto(amount)
        print(f"  ${amount:>7.2f} USD → {crypto_amount:.8f} {crypto_type}")
    
    print()
    print("=" * 70)
    print("  💰 SIMULATING DEPOSITS")
    print("=" * 70)
    print()
    
    # Simulate deposits
    test_deposits = [
        (15.50, "affiliate_commission"),
        (23.75, "microtask_completion"),
        (8.25, "content_monetization"),
        (45.00, "digital_product_sale"),
        (250.00, "service_revenue"),
    ]
    
    total_usd = 0
    
    for amount, source in test_deposits:
        print(f"Processing: ${amount:.2f} from {source}")
        tx = crypto.create_deposit(amount, source)
        filepath = crypto.save_transaction(tx)
        total_usd += amount
        print(f"  ✓ Saved to: {filepath}")
        print()
    
    print("=" * 70)
    print("  📊 SUMMARY")
    print("=" * 70)
    print()
    
    totals = crypto.get_total_deposited()
    print(f"Total simulated deposits: ${totals['total_usd']:.2f}")
    print(f"Number of transactions: {totals['count']}")
    
    if totals['by_crypto']:
        print()
        print("By cryptocurrency:")
        for crypto_type, amount in totals['by_crypto'].items():
            print(f"  {crypto_type}: {amount:.8f}")
    
    print()
    print("=" * 70)
    print()
    
    # Check mode
    mode = os.getenv("CRYPTO_MODE", "testnet")
    if mode == "testnet":
        print("⚠️  NOTE: Running in TESTNET/SIMULATION mode")
        print("   No real cryptocurrency is being transferred.")
        print()
        print("To enable mainnet (real money):")
        print("  1. Ensure wallet addresses are correct")
        print("  2. Set CRYPTO_MODE=mainnet in your environment")
        print("  3. For full automation, integrate with exchange API")
    else:
        print("🚀 Running in MAINNET mode")
        print("   Real cryptocurrency will be transferred!")
        print("   Ensure your wallet addresses are correct.")
    
    print()
    print("Deposit records saved to: payments/crypto/")
    print()
    print("=" * 70)

if __name__ == "__main__":
    # First show status
    check_crypto_status()
    print()
    
    # Then run deposit tests
    test_deposits()
