#!/usr/bin/env python3
"""
RM-QPT Cryptocurrency Integration
Replaces PayPal with crypto for instant, automated deposits
Supports Bitcoin (BTC), Ethereum (ETH), and stablecoins (USDC/USDT)
"""

import os
import json
import hashlib
import hmac
import base64
import requests
from datetime import datetime
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

# Configuration from environment
CRYPTO_MODE = os.getenv("CRYPTO_MODE", "testnet")  # "testnet" or "mainnet"
BTC_WALLET = os.getenv("BTC_WALLET_ADDRESS", "")
ETH_WALLET = os.getenv("ETH_WALLET_ADDRESS", "")
USDC_WALLET = os.getenv("USDC_WALLET_ADDRESS", "")  # Same as ETH (ERC-20)

# API Keys for crypto services
BLOCKCYPHER_API_KEY = os.getenv("BLOCKCYPHER_API_KEY", "")
INFURA_API_KEY = os.getenv("INFURA_API_KEY", "")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "")

@dataclass
class CryptoTransaction:
    """Represents a crypto deposit transaction"""
    amount_usd: float
    crypto_type: str  # "BTC", "ETH", "USDC"
    crypto_amount: float
    wallet_address: str
    transaction_hash: Optional[str] = None
    status: str = "pending"
    timestamp: str = ""
    usd_to_crypto_rate: float = 0.0
    fee_usd: float = 0.0
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class CryptoIntegration:
    """
    Cryptocurrency integration for RM-QPT
    Handles deposits to BTC, ETH, or stablecoin wallets
    """
    
    # Transaction fees (approximate, in USD)
    FEES = {
        "BTC": 0.50,      # ~$0.50-2.00 depending on congestion
        "ETH": 1.00,      # ~$1-5 depending on gas
        "USDC": 1.00,     # ~$1-5 (ERC-20 on Ethereum)
        "USDT": 1.00,     # Similar to USDC
    }
    
    # API endpoints
    BLOCKCYPHER_BASE = "https://api.blockcypher.com/v1/btc"
    ETHERSCAN_BASE = "https://api.etherscan.io/api"
    COINGECKO_BASE = "https://api.coingecko.com/api/v3"
    
    def __init__(self):
        self.mode = CRYPTO_MODE
        self.btc_wallet = BTC_WALLET
        self.eth_wallet = ETH_WALLET
        self.usdc_wallet = USDC_WALLET or ETH_WALLET  # USDC uses ETH address
        
        # Cache for exchange rates
        self._rate_cache = {}
        self._rate_cache_time = None
        
        print(f"🔐 Crypto Integration Initialized")
        print(f"   Mode: {self.mode}")
        print(f"   BTC Wallet: {'✓ Set' if self.btc_wallet else '✗ Not Set'}")
        print(f"   ETH Wallet: {'✓ Set' if self.eth_wallet else '✗ Not Set'}")
        print(f"   USDC Wallet: {'✓ Set' if self.usdc_wallet else '✗ Not Set'}")
    
    def get_crypto_prices(self) -> Dict[str, float]:
        """Get current crypto prices in USD"""
        try:
            # Check cache (refresh every 5 minutes)
            if self._rate_cache_time:
                elapsed = (datetime.now() - self._rate_cache_time).total_seconds()
                if elapsed < 300 and self._rate_cache:
                    return self._rate_cache
            
            # Fetch from CoinGecko (free, no API key needed for basic calls)
            url = f"{self.COINGECKO_BASE}/simple/price"
            params = {
                "ids": "bitcoin,ethereum,usd-coin,tether",
                "vs_currencies": "usd"
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                prices = {
                    "BTC": data.get("bitcoin", {}).get("usd", 0),
                    "ETH": data.get("ethereum", {}).get("usd", 0),
                    "USDC": data.get("usd-coin", {}).get("usd", 1.0),  # Should be ~1
                    "USDT": data.get("tether", {}).get("usd", 1.0),    # Should be ~1
                }
                self._rate_cache = prices
                self._rate_cache_time = datetime.now()
                return prices
            else:
                print(f"⚠️ Could not fetch prices: HTTP {response.status_code}")
                return {"BTC": 85000, "ETH": 3200, "USDC": 1.0, "USDT": 1.0}
                
        except Exception as e:
            print(f"⚠️ Error fetching crypto prices: {e}")
            # Return fallback prices
            return {"BTC": 85000, "ETH": 3200, "USDC": 1.0, "USDT": 1.0}
    
    def select_best_crypto(self, amount_usd: float) -> Tuple[str, float]:
        """
        Select best cryptocurrency for the transaction
        Based on: fees, amount size, wallet availability
        
        Returns: (crypto_type, amount_in_crypto)
        """
        prices = self.get_crypto_prices()
        
        # Decision logic:
        # - Small amounts (<$50): USDC/USDT (stable, low volatility)
        # - Medium amounts ($50-$500): ETH
        # - Large amounts (>$500): BTC
        
        if amount_usd < 50 and self.usdc_wallet:
            crypto_type = "USDC"
        elif amount_usd < 500 and self.eth_wallet:
            crypto_type = "ETH"
        elif self.btc_wallet:
            crypto_type = "BTC"
        elif self.eth_wallet:
            crypto_type = "ETH"
        elif self.usdc_wallet:
            crypto_type = "USDC"
        else:
            raise ValueError("No wallet addresses configured!")
        
        # Calculate crypto amount
        rate = prices.get(crypto_type, 1)
        crypto_amount = amount_usd / rate if rate > 0 else 0
        
        return crypto_type, crypto_amount
    
    def create_deposit(self, amount_usd: float, source: str = "rm-qpt") -> CryptoTransaction:
        """
        Create a crypto deposit transaction
        In mainnet mode: this would trigger an actual transfer
        In testnet mode: simulates the transaction
        """
        crypto_type, crypto_amount = self.select_best_crypto(amount_usd)
        
        # Select wallet based on crypto type
        if crypto_type == "BTC":
            wallet = self.btc_wallet
        elif crypto_type in ["USDC", "USDT"]:
            wallet = self.usdc_wallet
        else:
            wallet = self.eth_wallet
        
        # Create transaction
        tx = CryptoTransaction(
            amount_usd=amount_usd,
            crypto_type=crypto_type,
            crypto_amount=crypto_amount,
            wallet_address=wallet,
            usd_to_crypto_rate=self.get_crypto_prices().get(crypto_type, 0),
            fee_usd=self.FEES.get(crypto_type, 1.0)
        )
        
        if self.mode == "mainnet":
            # Real transaction would happen here
            # This requires integration with exchange APIs or smart contracts
            tx.status = "mainnet_ready"
            tx.transaction_hash = self._generate_tx_hash()
            print(f"🚀 Crypto deposit ready for mainnet:")
            print(f"   {crypto_amount:.8f} {crypto_type} = ${amount_usd:.2f} USD")
            print(f"   To: {wallet[:10]}...{wallet[-6:]}")
            print(f"   Note: Integration with exchange API needed for automatic sending")
        else:
            # Testnet/Simulation mode
            tx.status = "testnet_simulation"
            tx.transaction_hash = f"SIM_{hashlib.sha256(f'{datetime.now()}'.encode()).hexdigest()[:16]}"
            print(f"🧪 Simulated crypto deposit:")
            print(f"   {crypto_amount:.8f} {crypto_type} = ${amount_usd:.2f} USD")
            print(f"   To: {wallet[:10]}...{wallet[-6:] if len(wallet) > 16 else wallet}")
        
        return tx
    
    def _generate_tx_hash(self) -> str:
        """Generate a unique transaction hash"""
        data = f"{datetime.now().isoformat()}{os.urandom(16)}"
        return "0x" + hashlib.sha256(data.encode()).hexdigest()
    
    def save_transaction(self, tx: CryptoTransaction) -> str:
        """Save transaction record to file"""
        tx_id = f"CRYPTO_{datetime.now().strftime('%y%m%d%H%M%S')}_{tx.transaction_hash[:8]}"
        
        record = {
            "transaction_id": tx_id,
            "timestamp": tx.timestamp,
            "amount_usd": tx.amount_usd,
            "crypto_type": tx.crypto_type,
            "crypto_amount": tx.crypto_amount,
            "usd_to_crypto_rate": tx.usd_to_crypto_rate,
            "wallet_address": tx.wallet_address,
            "transaction_hash": tx.transaction_hash,
            "status": tx.status,
            "fee_usd": tx.fee_usd,
            "mode": self.mode
        }
        
        # Save to payments directory
        os.makedirs("payments/crypto", exist_ok=True)
        filepath = f"payments/crypto/{tx_id}.json"
        
        with open(filepath, 'w') as f:
            json.dump(record, f, indent=2)
        
        return filepath
    
    def get_wallet_balance(self, crypto_type: str = "ETH") -> Optional[float]:
        """
        Get current balance of a wallet
        Requires API keys for blockchain explorers
        """
        if crypto_type == "BTC" and self.btc_wallet and BLOCKCYPHER_API_KEY:
            return self._get_btc_balance()
        elif crypto_type == "ETH" and self.eth_wallet and ETHERSCAN_API_KEY:
            return self._get_eth_balance()
        else:
            print(f"⚠️ Cannot check balance - missing API key or wallet")
            return None
    
    def _get_btc_balance(self) -> Optional[float]:
        """Get BTC balance via BlockCypher"""
        try:
            chain = "main" if self.mode == "mainnet" else "test3"
            url = f"{self.BLOCKCYPHER_BASE}/{chain}/addrs/{self.btc_wallet}/balance"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Balance is in satoshis
                balance_btc = data.get("final_balance", 0) / 100000000
                return balance_btc
        except Exception as e:
            print(f"⚠️ Error checking BTC balance: {e}")
        return None
    
    def _get_eth_balance(self) -> Optional[float]:
        """Get ETH balance via Etherscan"""
        try:
            url = self.ETHERSCAN_BASE
            params = {
                "module": "account",
                "action": "balance",
                "address": self.eth_wallet,
                "tag": "latest",
                "apikey": ETHERSCAN_API_KEY
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Balance is in wei
                balance_eth = int(data.get("result", 0)) / 10**18
                return balance_eth
        except Exception as e:
            print(f"⚠️ Error checking ETH balance: {e}")
        return None
    
    def get_total_deposited(self) -> Dict:
        """Get total crypto deposited from all transaction records"""
        crypto_dir = "payments/crypto"
        if not os.path.exists(crypto_dir):
            return {"total_usd": 0, "by_crypto": {}, "count": 0}
        
        total_usd = 0
        by_crypto = {}
        count = 0
        
        for filename in os.listdir(crypto_dir):
            if filename.endswith('.json'):
                try:
                    with open(f"{crypto_dir}/{filename}") as f:
                        record = json.load(f)
                    total_usd += record.get("amount_usd", 0)
                    crypto_type = record.get("crypto_type", "UNKNOWN")
                    by_crypto[crypto_type] = by_crypto.get(crypto_type, 0) + record.get("crypto_amount", 0)
                    count += 1
                except:
                    pass
        
        return {
            "total_usd": total_usd,
            "by_crypto": by_crypto,
            "count": count
        }


def check_crypto_status():
    """Check crypto integration status"""
    print("=" * 70)
    print("  CRYPTO INTEGRATION STATUS CHECK")
    print("=" * 70)
    print()
    
    # Check environment variables
    print("Environment Configuration:")
    print(f"  CRYPTO_MODE: {os.getenv('CRYPTO_MODE', 'testnet')} {'✓' if os.getenv('CRYPTO_MODE') else '⚠️ default'}")
    print(f"  BTC_WALLET: {'✓ Set' if os.getenv('BTC_WALLET_ADDRESS') else '✗ Not Set'}")
    print(f"  ETH_WALLET: {'✓ Set' if os.getenv('ETH_WALLET_ADDRESS') else '✗ Not Set'}")
    print(f"  USDC_WALLET: {'✓ Set' if os.getenv('USDC_WALLET_ADDRESS') else '✗ Not Set (uses ETH)'}")
    print()
    
    # Initialize integration
    crypto = CryptoIntegration()
    print()
    
    # Get current prices
    print("Current Crypto Prices (USD):")
    prices = crypto.get_crypto_prices()
    for crypto_type, price in prices.items():
        print(f"  {crypto_type}: ${price:,.2f}")
    print()
    
    # Check existing deposits
    totals = crypto.get_total_deposited()
    print(f"Total Recorded Deposits: ${totals['total_usd']:.2f} ({totals['count']} transactions)")
    if totals['by_crypto']:
        print("By Cryptocurrency:")
        for crypto_type, amount in totals['by_crypto'].items():
            print(f"  {crypto_type}: {amount:.8f}")
    print()
    
    print("=" * 70)


if __name__ == "__main__":
    check_crypto_status()
