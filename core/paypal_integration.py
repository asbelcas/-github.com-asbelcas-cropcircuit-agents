#!/usr/bin/env python3
"""
PayPal Integration for RM-QPT
=============================

This module handles real PayPal API integration for depositing money
to your PayPal account automatically.

REQUIREMENTS FOR REAL PAYPAL INTEGRATION:
1. PayPal Business Account (not personal)
2. PayPal Developer Account
3. API Credentials (Client ID, Client Secret)
4. PayPal Python SDK: pip install paypalrestsdk

LIMITATIONS:
- PayPal doesn't allow "pushing" money to accounts without recipient approval
- Alternative: Use PayPal Payouts API (requires business account + approval)
- Alternative: Accumulate funds and transfer manually
- Alternative: Use other payment processors (Stripe, Wise, crypto)
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Configuration - Set these environment variables or edit directly
PAYPAL_MODE = os.environ.get("PAYPAL_MODE", "sandbox")  # "sandbox" or "live"
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID", "")
PAYPAL_CLIENT_SECRET = os.environ.get("PAYPAL_CLIENT_SECRET", "")
PAYPAL_RECEIVER_EMAIL = "asbelcas@gmail.com"  # Your PayPal email

class PayPalIntegration:
    """
    PayPal integration handler for RM-QPT.
    
    IMPORTANT: PayPal does not allow automated "push" transfers to arbitrary
    accounts without the recipient's approval for each transaction.
    
    Options for real implementation:
    1. PayPal Payouts API (requires business account + PayPal approval)
    2. Manual transfer (accumulate, then user withdraws)
    3. Use alternative: Stripe Connect, Wise, crypto wallets
    """
    
    def __init__(self):
        self.mode = PAYPAL_MODE
        self.client_id = PAYPAL_CLIENT_ID
        self.client_secret = PAYPAL_CLIENT_SECRET
        self.receiver_email = PAYPAL_RECEIVER_EMAIL
        self.paypal_api = None
        
        # Track deposit status
        self.pending_deposits = []
        self.completed_deposits = []
        self.failed_deposits = []
        
        # Check if credentials are configured
        self.is_configured = bool(self.client_id and self.client_secret)
        
    def check_configuration(self) -> Dict:
        """Check if PayPal is properly configured"""
        status = {
            "configured": self.is_configured,
            "mode": self.mode,
            "receiver_email": self.receiver_email,
            "client_id_set": bool(self.client_id),
            "client_secret_set": bool(self.client_secret),
            "paypal_sdk_installed": False,
            "can_deposit": False
        }
        
        # Check if PayPal SDK is installed
        try:
            import paypalrestsdk
            status["paypal_sdk_installed"] = True
            
            # Try to configure PayPal
            if self.is_configured:
                paypalrestsdk.configure({
                    "mode": self.mode,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                })
                self.paypal_api = paypalrestsdk
                status["can_deposit"] = True
                
        except ImportError:
            status["error"] = "PayPal SDK not installed. Run: pip install paypalrestsdk"
        except Exception as e:
            status["error"] = str(e)
        
        return status
    
    def deposit_funds(self, amount: float, transaction_id: str, 
                     description: str = "RM-QPT Revenue Share") -> Dict:
        """
        Attempt to deposit funds to PayPal account.
        
        NOTE: This requires PayPal Payouts API which needs:
        - Business Account
        - PayPal approval for Payouts
        - Verified account with linked bank
        """
        if not self.is_configured:
            return {
                "status": "failed",
                "error": "PayPal not configured",
                "message": "Set PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET environment variables"
            }
        
        try:
            # For Payouts API (requires approval from PayPal)
            payout = self.paypal_api.Payout({
                "sender_batch_header": {
                    "sender_batch_id": f"RMQPT_{transaction_id}",
                    "email_subject": "RM-QPT Revenue Share",
                    "email_message": f"You've received ${amount:.2f} from RM-QPT automated system."
                },
                "items": [{
                    "recipient_type": "EMAIL",
                    "amount": {
                        "value": f"{amount:.2f}",
                        "currency": "USD"
                    },
                    "receiver": self.receiver_email,
                    "note": description,
                    "sender_item_id": transaction_id
                }]
            })
            
            if payout.create():
                result = {
                    "status": "success",
                    "payout_batch_id": payout.batch_header.payout_batch_id,
                    "amount": amount,
                    "receiver": self.receiver_email,
                    "transaction_id": transaction_id,
                    "timestamp": datetime.now().isoformat()
                }
                self.completed_deposits.append(result)
                return result
            else:
                error = payout.error
                result = {
                    "status": "failed",
                    "error": str(error),
                    "amount": amount,
                    "transaction_id": transaction_id
                }
                self.failed_deposits.append(result)
                return result
                
        except Exception as e:
            result = {
                "status": "error",
                "error": str(e),
                "amount": amount,
                "transaction_id": transaction_id
            }
            self.failed_deposits.append(result)
            return result
    
    def get_account_balance(self) -> Dict:
        """Check PayPal account balance (if API allows)"""
        if not self.is_configured:
            return {"error": "Not configured"}
        
        try:
            # This requires specific API permissions
            # Most apps don't have access to read balance
            return {
                "status": "info",
                "message": "PayPal balance check requires special permissions",
                "recommendation": "Check balance at paypal.com"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_setup_instructions(self) -> str:
        """Get instructions for setting up real PayPal integration"""
        return """
╔══════════════════════════════════════════════════════════════════╗
║           PAYPAL INTEGRATION SETUP INSTRUCTIONS                  ║
╚══════════════════════════════════════════════════════════════════╝

STEP 1: Create PayPal Developer Account
────────────────────────────────────────
1. Go to https://developer.paypal.com/
2. Sign up/login with your PayPal account
3. Navigate to "Dashboard" → "My Apps & Credentials"

STEP 2: Create App for API Credentials
───────────────────────────────────────
1. Click "Create App"
2. Name it "RM-QPT Money System"
3. Select "Merchant" app type
4. Copy the Client ID and Secret

STEP 3: Request Payouts API Access
───────────────────────────────────
⚠️ IMPORTANT: PayPal Payouts requires approval!

1. Go to your app settings
2. Find "Payouts" in the features list
3. Click "Request Access"
4. Fill out the form explaining your use case:
   - Business type: Automated revenue sharing
   - Volume: Estimated monthly payouts
   - Use case: Distributing profits to account owner
5. Wait for PayPal approval (can take days/weeks)

STEP 4: Configure Environment Variables
────────────────────────────────────────
Add to your ~/.bashrc or ~/.profile:

export PAYPAL_CLIENT_ID="your_client_id_here"
export PAYPAL_CLIENT_SECRET="your_client_secret_here"
export PAYPAL_MODE="live"  # or "sandbox" for testing

Then reload:
source ~/.bashrc

STEP 5: Install PayPal SDK
───────────────────────────
pip install paypalrestsdk

STEP 6: Test in Sandbox
────────────────────────
1. Set PAYPAL_MODE="sandbox"
2. Use sandbox test accounts
3. Run a test transaction
4. Verify it works

STEP 7: Switch to Live
───────────────────────
1. Set PAYPAL_MODE="live"
2. Use real Client ID and Secret
3. Start processing real payments

╔══════════════════════════════════════════════════════════════════╗
║                    ALTERNATIVE APPROACHES                        ║
╚══════════════════════════════════════════════════════════════════╝

OPTION A: Manual Withdrawal (Easiest)
──────────────────────────────────────
• System accumulates earnings in your business account
• You manually transfer to PayPal when desired
• No API integration needed
• Full control over timing

OPTION B: Stripe Connect (More flexible)
─────────────────────────────────────────
• Stripe Connect allows automated transfers
• Better API for marketplace/revenue share
• Easier to get approved than PayPal Payouts
• Requires Stripe account

OPTION C: Wise (formerly TransferWise)
───────────────────────────────────────
• Lower fees than PayPal
• Good for international transfers
• API available for automated transfers

OPTION D: Cryptocurrency
─────────────────────────
• Use crypto wallet addresses
• Instant, low-fee transfers
• No approval process
• Tax implications to consider

╔══════════════════════════════════════════════════════════════════╗
║                      CURRENT STATUS                              ║
╚══════════════════════════════════════════════════════════════════╝
"""


def check_paypal_status():
    """Check current PayPal integration status"""
    paypal = PayPalIntegration()
    status = paypal.check_configuration()
    
    print("\n" + "=" * 70)
    print("  PAYPAL INTEGRATION STATUS CHECK")
    print("=" * 70)
    print()
    
    print(f"PayPal Mode: {status['mode']}")
    print(f"Receiver Email: {status['receiver_email']}")
    print()
    
    print("Configuration:")
    print(f"  ✓ Client ID set: {status['client_id_set']}")
    print(f"  ✓ Client Secret set: {status['client_secret_set']}")
    print(f"  ✓ PayPal SDK installed: {status['paypal_sdk_installed']}")
    print()
    
    if status['can_deposit']:
        print("✅ PayPal is FULLY CONFIGURED and ready for deposits!")
    elif not status['paypal_sdk_installed']:
        print("⚠️  PayPal SDK not installed")
        print("   Run: pip install paypalrestsdk")
    elif not status['client_id_set']:
        print("⚠️  PayPal API credentials not configured")
        print("   See setup instructions above")
    else:
        print("⚠️  Configuration issue")
        if 'error' in status:
            print(f"   Error: {status['error']}")
    
    print()
    print("=" * 70)
    
    # Show setup instructions
    if not status['can_deposit']:
        print(paypal.get_setup_instructions())
    
    return status


if __name__ == "__main__":
    # Run status check
    check_paypal_status()
