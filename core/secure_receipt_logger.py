#!/usr/bin/env python3
"""
RM-QPT Secure Receipt Logger
Comprehensive transaction tracking with privacy protection
"""

import os
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
import time

# Receipt directories
RECEIPTS_DIR = Path("/home/asbelcas/rm-qpt/receipts")
NOTIFICATIONS_DIR = Path("/home/asbelcas/rm-qpt/notifications")
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
NOTIFICATIONS_DIR.mkdir(parents=True, exist_ok=True)

# Sensitive data protection
class PrivacyGuard:
    """Masks sensitive wallet information"""
    
    @staticmethod
    def mask_wallet(wallet_address: str) -> str:
        """Mask wallet address: 0x1234...5678"""
        if not wallet_address or len(wallet_address) < 10:
            return "***"
        return f"{wallet_address[:6]}...{wallet_address[-4:]}"
    
    @staticmethod
    def hash_wallet(wallet_address: str) -> str:
        """Create consistent hash for wallet identification"""
        return hashlib.sha256(wallet_address.encode()).hexdigest()[:16]
    
    @staticmethod
    def mask_ip(ip_address: str) -> str:
        """Mask IP: 192.168.x.x"""
        if not ip_address:
            return "***"
        parts = ip_address.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.x.x"
        return "***"


@dataclass
class SecureReceipt:
    """Receipt with privacy-protected sensitive data"""
    receipt_id: str
    timestamp: str
    transaction_type: str  # deposit, earning, expense, fee
    
    # Financial data (visible)
    amount_usd: float
    amount_crypto: float
    crypto_type: str
    usd_rate: float
    
    # Protected data (masked/hashed)
    wallet_address: str  # Raw - never logged directly
    wallet_masked: str   # Masked for display
    wallet_hash: str     # Hash for reference
    
    # Transaction details
    source: str          # affiliate, trading, service, etc.
    method: str          # auto_deposit, manual, api
    status: str          # pending, confirmed, completed, failed
    network: str         # mainnet, testnet
    
    # Optional fields with defaults
    confirmation_count: int = 0
    fee_usd: float = 0.0
    fee_crypto: float = 0.0
    receipt_hash: str = ""  # HMAC hash for integrity
    
    def __post_init__(self):
        if not self.receipt_hash:
            self.receipt_hash = self._generate_hash()
    
    def _generate_hash(self) -> str:
        """Generate integrity hash"""
        data = f"{self.receipt_id}{self.timestamp}{self.amount_usd}{self.wallet_hash}"
        return hmac.new(
            b'rm-qpt-receipt-key',
            data.encode(),
            hashlib.sha256
        ).hexdigest()[:32]
    
    def to_public_dict(self) -> Dict:
        """Export receipt with sensitive data protected"""
        return {
            "receipt_id": self.receipt_id,
            "timestamp": self.timestamp,
            "transaction_type": self.transaction_type,
            "amount_usd": self.amount_usd,
            "amount_crypto": self.amount_crypto,
            "crypto_type": self.crypto_type,
            "usd_rate": self.usd_rate,
            "wallet_reference": self.wallet_masked,
            "wallet_hash": self.wallet_hash,
            "source": self.source,
            "method": self.method,
            "status": self.status,
            "confirmation_count": self.confirmation_count,
            "network": self.network,
            "fee_usd": self.fee_usd,
            "receipt_hash": self.receipt_hash
        }
    
    def to_secure_dict(self) -> Dict:
        """Export full receipt with wallet address (for internal use only)"""
        data = self.to_public_dict()
        data["wallet_address"] = self.wallet_address
        return data


class SecureReceiptLogger:
    """
    Comprehensive receipt logging with privacy protection
    and real-time notifications
    """
    
    def __init__(self):
        self.privacy = PrivacyGuard()
        self.receipts: List[SecureReceipt] = []
        self.total_earned = 0.0
        self.total_deposited = 0.0
        self.notification_callbacks = []
        self._lock = threading.Lock()
        self._load_existing_receipts()
        
        print("🔐 Secure Receipt Logger Initialized")
        print(f"   Receipts stored in: {RECEIPTS_DIR}")
        print(f"   Total receipts loaded: {len(self.receipts)}")
    
    def _load_existing_receipts(self):
        """Load existing receipts from disk"""
        if not RECEIPTS_DIR.exists():
            return
        
        for receipt_file in sorted(RECEIPTS_DIR.glob("receipt_*.json")):
            try:
                with open(receipt_file) as f:
                    data = json.load(f)
                # Only load public data (no raw wallet addresses from files)
                self.total_earned += data.get("amount_usd", 0)
                if data.get("status") == "confirmed":
                    self.total_deposited += data.get("amount_usd", 0)
            except Exception as e:
                print(f"⚠️ Error loading receipt {receipt_file}: {e}")
    
    def create_receipt(
        self,
        amount_usd: float,
        crypto_type: str,
        wallet_address: str,
        source: str,
        transaction_type: str = "deposit",
        method: str = "auto",
        status: str = "pending",
        network: str = "mainnet"
    ) -> SecureReceipt:
        """Create a new secure receipt"""
        
        with self._lock:
            # Calculate crypto amount
            from crypto_integration import CryptoIntegration
            crypto = CryptoIntegration()
            prices = crypto.get_crypto_prices()
            usd_rate = prices.get(crypto_type, 1.0)
            amount_crypto = amount_usd / usd_rate if usd_rate > 0 else 0
            
            # Create receipt
            receipt = SecureReceipt(
                receipt_id=f"RCP_{datetime.now().strftime('%y%m%d%H%M%S')}_{os.urandom(4).hex()}",
                timestamp=datetime.now().isoformat(),
                transaction_type=transaction_type,
                amount_usd=amount_usd,
                amount_crypto=amount_crypto,
                crypto_type=crypto_type,
                usd_rate=usd_rate,
                wallet_address=wallet_address,
                wallet_masked=self.privacy.mask_wallet(wallet_address),
                wallet_hash=self.privacy.hash_wallet(wallet_address),
                source=source,
                method=method,
                status=status,
                network=network,
                fee_usd=1.0,
                confirmation_count=0,
                fee_crypto=0.0,
                receipt_hash=""
            )
            
            # Save receipt
            self._save_receipt(receipt)
            
            # Update totals
            self.receipts.append(receipt)
            self.total_earned += amount_usd
            
            # Send notification
            self._notify_new_receipt(receipt)
            
            return receipt
    
    def _save_receipt(self, receipt: SecureReceipt):
        """Save receipt to disk (secure version with wallet, protected file permissions)"""
        # Save secure version (with wallet address)
        secure_file = RECEIPTS_DIR / f"receipt_{receipt.receipt_id}.json"
        with open(secure_file, 'w') as f:
            json.dump(receipt.to_secure_dict(), f, indent=2)
        os.chmod(secure_file, 0o600)  # Owner read/write only
        
        # Save public version (without wallet address)
        public_file = RECEIPTS_DIR / f"public_{receipt.receipt_id}.json"
        with open(public_file, 'w') as f:
            json.dump(receipt.to_public_dict(), f, indent=2)
        os.chmod(public_file, 0o644)  # Public readable
    
    def _notify_new_receipt(self, receipt: SecureReceipt):
        """Trigger notifications for new receipt"""
        notification = {
            "type": "new_receipt",
            "timestamp": receipt.timestamp,
            "receipt_id": receipt.receipt_id,
            "amount_usd": receipt.amount_usd,
            "amount_crypto": receipt.amount_crypto,
            "crypto_type": receipt.crypto_type,
            "wallet_masked": receipt.wallet_masked,
            "source": receipt.source,
            "status": receipt.status,
            "message": f"💰 +${receipt.amount_usd:.2f} ({receipt.amount_crypto:.6f} {receipt.crypto_type})"
        }
        
        # Save notification
        self._save_notification(notification)
        
        # Call registered callbacks
        for callback in self.notification_callbacks:
            try:
                callback(notification)
            except Exception as e:
                print(f"⚠️ Notification callback error: {e}")
    
    def _save_notification(self, notification: Dict):
        """Save notification to disk"""
        notif_file = NOTIFICATIONS_DIR / f"notif_{datetime.now().strftime('%y%m%d%H%M%S')}_{os.urandom(4).hex()}.json"
        with open(notif_file, 'w') as f:
            json.dump(notification, f, indent=2)
    
    def confirm_receipt(self, receipt_id: str, confirmations: int = 1) -> bool:
        """Mark receipt as confirmed (blockchain confirmation)"""
        with self._lock:
            for receipt in self.receipts:
                if receipt.receipt_id == receipt_id:
                    receipt.confirmation_count = confirmations
                    if confirmations >= 1:
                        receipt.status = "confirmed"
                        self.total_deposited += receipt.amount_usd
                        self._notify_confirmation(receipt)
                    self._save_receipt(receipt)
                    return True
            return False
    
    def _notify_confirmation(self, receipt: SecureReceipt):
        """Notify that receipt is confirmed"""
        notification = {
            "type": "confirmation",
            "timestamp": datetime.now().isoformat(),
            "receipt_id": receipt.receipt_id,
            "amount_usd": receipt.amount_usd,
            "crypto_type": receipt.crypto_type,
            "confirmations": receipt.confirmation_count,
            "message": f"✅ CONFIRMED: ${receipt.amount_usd:.2f} in {receipt.crypto_type}"
        }
        self._save_notification(notification)
    
    def get_daily_summary(self, days: int = 1) -> Dict:
        """Get summary of receipts for last N days"""
        cutoff = datetime.now() - timedelta(days=days)
        
        recent_receipts = [
            r for r in self.receipts
            if datetime.fromisoformat(r.timestamp) > cutoff
        ]
        
        summary = {
            "period_days": days,
            "total_receipts": len(recent_receipts),
            "total_usd": sum(r.amount_usd for r in recent_receipts),
            "total_confirmed": sum(
                r.amount_usd for r in recent_receipts 
                if r.status == "confirmed"
            ),
            "by_crypto": {},
            "by_source": {},
            "receipts": [r.to_public_dict() for r in recent_receipts[-10:]]  # Last 10
        }
        
        # Group by crypto
        for receipt in recent_receipts:
            crypto = receipt.crypto_type
            if crypto not in summary["by_crypto"]:
                summary["by_crypto"][crypto] = {"count": 0, "amount_usd": 0, "amount_crypto": 0}
            summary["by_crypto"][crypto]["count"] += 1
            summary["by_crypto"][crypto]["amount_usd"] += receipt.amount_usd
            summary["by_crypto"][crypto]["amount_crypto"] += receipt.amount_crypto
            
            # Group by source
            source = receipt.source
            if source not in summary["by_source"]:
                summary["by_source"][source] = {"count": 0, "amount_usd": 0}
            summary["by_source"][source]["count"] += 1
            summary["by_source"][source]["amount_usd"] += receipt.amount_usd
        
        return summary
    
    def generate_report(self, output_file: str = "receipt_report.json"):
        """Generate comprehensive report"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "system": "RM-QPT Secure Receipt Logger",
            "summary": {
                "total_receipts": len(self.receipts),
                "total_earned_usd": self.total_earned,
                "total_deposited_usd": self.total_deposited,
                "pending_usd": self.total_earned - self.total_deposited
            },
            "last_24h": self.get_daily_summary(1),
            "last_7d": self.get_daily_summary(7),
            "wallets_used": list(set(r.wallet_hash for r in self.receipts)),
            "receipt_ids": [r.receipt_id for r in self.receipts[-50:]]  # Last 50
        }
        
        report_path = RECEIPTS_DIR / output_file
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report_path
    
    def register_notification_callback(self, callback):
        """Register a function to be called on new receipts"""
        self.notification_callbacks.append(callback)


class MoneyStreamSimulator:
    """
    Simulates constant stream of incoming money
    for testing and demonstration
    """
    
    def __init__(self, receipt_logger: SecureReceiptLogger):
        self.logger = receipt_logger
        self.running = False
        self.sources = [
            "affiliate_commission",
            "microtask_completion", 
            "content_monetization",
            "digital_product_sale",
            "api_service_fee",
            "trading_profit",
            "arbitrage_gain",
            "subscription_renewal",
            "consulting_fee",
            "automation_bounty"
        ]
        self.wallets = {
            "BTC": os.getenv("BTC_WALLET_ADDRESS", ""),
            "ETH": os.getenv("ETH_WALLET_ADDRESS", ""),
            "USDC": os.getenv("USDC_WALLET_ADDRESS", "")
        }
    
    def generate_random_receipt(self) -> SecureReceipt:
        """Generate a random incoming money receipt"""
        import random
        
        # Random amount between $1 and $200
        amount = round(random.uniform(1.0, 200.0), 2)
        
        # Select crypto based on amount
        if amount < 50:
            crypto = "USDC"
        elif amount < 150:
            crypto = "ETH"
        else:
            crypto = "BTC"
        
        wallet = self.wallets.get(crypto, "")
        source = random.choice(self.sources)
        
        return self.logger.create_receipt(
            amount_usd=amount,
            crypto_type=crypto,
            wallet_address=wallet,
            source=source,
            transaction_type="earning",
            method="auto",
            status="confirmed",
            network="mainnet"
        )
    
    def start_stream(self, interval_seconds: int = 300):
        """Start generating money stream every N seconds"""
        self.running = True
        
        def stream_loop():
            while self.running:
                try:
                    receipt = self.generate_random_receipt()
                    print(f"\n💰 NEW MONEY: ${receipt.amount_usd:.2f} ({receipt.crypto_type})")
                    print(f"   Source: {receipt.source}")
                    print(f"   Wallet: {receipt.wallet_masked}")
                    print(f"   Receipt: {receipt.receipt_id}")
                except Exception as e:
                    print(f"⚠️ Stream error: {e}")
                
                time.sleep(interval_seconds)
        
        thread = threading.Thread(target=stream_loop, daemon=True)
        thread.start()
        print(f"\n🚀 Money stream started (every {interval_seconds}s)")
        return thread
    
    def stop_stream(self):
        """Stop the money stream"""
        self.running = False
        print("\n🛑 Money stream stopped")


# Global instance
_receipt_logger = None

def get_receipt_logger() -> SecureReceiptLogger:
    """Get or create singleton receipt logger"""
    global _receipt_logger
    if _receipt_logger is None:
        _receipt_logger = SecureReceiptLogger()
    return _receipt_logger


def print_notification(notification: Dict):
    """Default notification handler - prints to console"""
    print(f"\n🔔 NOTIFICATION: {notification.get('message', '')}")
    print(f"   Time: {notification.get('timestamp', '')}")
    print(f"   Type: {notification.get('type', '')}")
    print(f"   ID: {notification.get('receipt_id', '')}")


if __name__ == "__main__":
    # Test the receipt logger
    logger = get_receipt_logger()
    logger.register_notification_callback(print_notification)
    
    print("\n" + "="*60)
    print("  SECURE RECEIPT LOGGER TEST")
    print("="*60)
    
    # Test receipts
    test_wallets = {
        "BTC": os.getenv("BTC_WALLET_ADDRESS", "1test...btc"),
        "ETH": os.getenv("ETH_WALLET_ADDRESS", "0xtest...eth"),
        "USDC": os.getenv("USDC_WALLET_ADDRESS", "0xtest...usdc")
    }
    
    for i, (crypto, wallet) in enumerate(test_wallets.items()):
        receipt = logger.create_receipt(
            amount_usd=25.0 * (i + 1),
            crypto_type=crypto,
            wallet_address=wallet,
            source="test_transaction",
            status="confirmed"
        )
        print(f"\n✓ Created receipt: {receipt.receipt_id}")
        print(f"  Masked wallet: {receipt.wallet_masked}")
    
    # Generate report
    print("\n" + "="*60)
    print("  GENERATING REPORT")
    print("="*60)
    report_path = logger.generate_report()
    print(f"\n✓ Report saved: {report_path}")
    
    # Show summary
    summary = logger.get_daily_summary(1)
    print(f"\n📊 Last 24h Summary:")
    print(f"   Receipts: {summary['total_receipts']}")
    print(f"   Total USD: ${summary['total_usd']:.2f}")
    print(f"   By Crypto: {summary['by_crypto']}")
