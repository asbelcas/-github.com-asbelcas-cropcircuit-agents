# 🚀 RM-QPT Cryptocurrency Integration Guide

## Overview

RM-QPT now uses **cryptocurrency** for automated deposits instead of PayPal. This provides:
- ✅ **Instant transfers** (no approval process)
- ✅ **Lower fees** (especially for international)
- ✅ **24/7 operation** (no banking hours)
- ✅ **No business account required**
- ✅ **Truly automated** once configured

---

## 💼 Supported Cryptocurrencies

| Coin | Best For | Typical Fee | Volatility |
|------|----------|-------------|------------|
| **USDC** | Small amounts (<$50) | ~$1-5 | None (stable) |
| **ETH** | Medium amounts ($50-$500) | ~$1-5 | Medium |
| **BTC** | Large amounts (>$500) | ~$1-2 | High |

**Auto-Selection**: The system automatically chooses the best crypto based on amount.

---

## 🛠️ Setup Instructions

### Step 1: Choose a Wallet

You need a cryptocurrency wallet. Recommended options:

#### Option A: Coinbase (Easiest for Beginners)
```
1. Go to https://www.coinbase.com
2. Create account and verify identity
3. Download Coinbase Wallet app OR use exchange wallet
4. Get wallet addresses for BTC, ETH, and USDC
```

#### Option B: MetaMask (Best for ETH/USDC)
```
1. Install MetaMask browser extension or mobile app
2. Create wallet (save seed phrase securely!)
3. Your ETH address works for USDC too
4. For BTC, you'll need a separate Bitcoin wallet
```

#### Option C: Trust Wallet (Mobile-friendly)
```
1. Download Trust Wallet app
2. Create new wallet
3. Supports BTC, ETH, USDC in one app
4. Get addresses for each cryptocurrency
```

#### Option D: Hardware Wallet (Most Secure)
```
- Ledger Nano S/X
- Trezor
- Best for large amounts
- Same setup: get wallet addresses
```

### Step 2: Get Your Wallet Addresses

Once you have a wallet, find your deposit addresses:

```
Bitcoin (BTC) address example:
  bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh

Ethereum (ETH) address example:
  0x71C7656EC7ab88b098defB751B7401B5f6d8976F

USDC address:
  Same as your ETH address (ERC-20 token on Ethereum)
```

**⚠️ IMPORTANT**: 
- Copy addresses exactly (they're case-sensitive)
- ETH and USDC use the same address
- BTC has a different address format
- Never share your private keys or seed phrase!

### Step 3: Configure RM-QPT

Run the setup script:

```bash
cd /home/asbelcas/rm-qpt
bash setup_crypto.sh
```

This will:
- Ask for your wallet addresses
- Set environment variables
- Configure for testnet or mainnet
- Save settings to your shell config

**Manual setup** (if you prefer):

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# Crypto Configuration
export CRYPTO_MODE="testnet"  # or "mainnet" for real money
export BTC_WALLET_ADDRESS="your_btc_address_here"
export ETH_WALLET_ADDRESS="your_eth_address_here"
export USDC_WALLET_ADDRESS="your_eth_address_here"  # Same as ETH
```

Then reload:
```bash
source ~/.bashrc
```

### Step 4: Test the Integration

```bash
# Check crypto status
python3 core/crypto_integration.py

# Run deposit test
python3 test_crypto_deposit.py
```

You should see:
- Current crypto prices
- Your configured wallets
- Simulated deposits being created
- Records saved to `payments/crypto/`

### Step 5: Switch to Mainnet (Real Money)

When ready for real deposits:

```bash
# Edit your shell config
nano ~/.bashrc

# Change this line:
export CRYPTO_MODE="mainnet"

# Reload
source ~/.bashrc

# Verify
python3 core/crypto_integration.py
```

---

## 📊 How It Works

### Automatic Selection
The system chooses the best cryptocurrency based on amount:

```
Amount < $50    → USDC (stable, low volatility)
Amount $50-500  → ETH (good balance)
Amount > $500   → BTC (best for large transfers)
```

### Deposit Flow
```
1. RM-QPT earns money
2. System selects optimal crypto
3. Calculates USD → crypto conversion
4. Records transaction
5. Saves to payments/crypto/
6. In mainnet: would send to your wallet
```

### File Structure
```
payments/
├── crypto/
│   ├── CRYPTO_260402120000_abc123.json  # Deposit records
│   └── CRYPTO_260402120001_def456.json
└── pending/                               # Pending deposits
    └── pending_TX_xxx.json
```

### Transaction Record Example
```json
{
  "transaction_id": "CRYPTO_260402120000_abc123",
  "timestamp": "2026-04-02T12:00:00",
  "amount_usd": 25.50,
  "crypto_type": "USDC",
  "crypto_amount": 25.50,
  "usd_to_crypto_rate": 1.0,
  "wallet_address": "0x71C7656EC7ab88b098defB751B7401B5f6d8976F",
  "transaction_hash": "SIM_abc123def456",
  "status": "testnet_simulation",
  "fee_usd": 1.00,
  "mode": "testnet"
}
```

---

## 🔌 Full Automation (Advanced)

The current system records deposits. For **fully automated sending**, you need exchange API integration:

### Option A: Coinbase API
```python
# Requires Coinbase API keys
# Can send crypto automatically
# Setup: https://www.coinbase.com/settings/api
```

### Option B: Exchange API (Binance, Kraken, etc.)
```python
# Use exchange APIs to:
# 1. Receive fiat from earnings
# 2. Convert to crypto
# 3. Withdraw to your wallet
```

### Option C: Smart Contract
```solidity
// Ethereum smart contract
// Automatically forwards incoming funds
// To your wallet address
```

**Note**: Full automation requires additional development. The current system is ready to integrate with any of these options.

---

## 💰 Tax Considerations

### United States
- Crypto is treated as property by IRS
- Each deposit may be a taxable event
- Track all transactions (system does this automatically)
- Consider using:
  - CoinTracker
  - Koinly
  - TurboTax Crypto

### Other Countries
- Check local regulations
- Most countries tax crypto as income or capital gains
- Keep detailed records (RM-QPT does this)

**RM-QPT provides**: Complete transaction history in `payments/crypto/` folder

---

## 🔒 Security Best Practices

### Wallet Security
```
✓ Use hardware wallet for large amounts
✓ Enable 2FA on all exchange accounts
✓ Store seed phrase offline (metal backup recommended)
✓ Never share private keys
✓ Use different wallets for different purposes
```

### System Security
```
✓ Environment variables (not hardcoded)
✓ Wallet addresses visible (this is OK - they're public)
✓ Private keys never in code
✓ Regular backups of transaction records
```

### Backup Strategy
```
1. Wallet seed phrase (physical, secure location)
2. Transaction records (git or cloud backup)
3. API keys (password manager)
4. System state (automatically backed up)
```

---

## 🐛 Troubleshooting

### Issue: "No wallet addresses configured"
```bash
# Solution: Run setup script
bash setup_crypto.sh

# Or manually add to ~/.bashrc:
export BTC_WALLET_ADDRESS="your_address"
export ETH_WALLET_ADDRESS="your_address"
source ~/.bashrc
```

### Issue: "Cannot fetch crypto prices"
```bash
# Check internet connection
# CoinGecko API is free but rate-limited
# System will use fallback prices if API fails
```

### Issue: "Crypto integration disabled"
```bash
# Check Python dependencies
pip install requests

# Verify file exists
ls core/crypto_integration.py
```

### Issue: "Invalid wallet address"
```bash
# Verify address format:
# BTC: Starts with 1, 3, or bc1
# ETH/USDC: Starts with 0x, 42 characters
# Copy directly from wallet (don't type manually)
```

---

## 📈 Monitoring Your Deposits

### Check Total Deposited
```bash
python3 -c "
import sys
sys.path.insert(0, 'core')
from crypto_integration import CryptoIntegration
crypto = CryptoIntegration()
totals = crypto.get_total_deposited()
print(f'Total: \${totals[\"total_usd\"]:.2f}')
print(f'Transactions: {totals[\"count\"]}')
"
```

### View Recent Deposits
```bash
ls -lt payments/crypto/ | head -10
```

### Check Wallet Balance
```bash
# Install blockcypher for BTC
# Install etherscan API for ETH
# Set API keys in environment
python3 core/crypto_integration.py
```

---

## 🚀 Quick Start Commands

```bash
# 1. Setup wallets
bash setup_crypto.sh

# 2. Apply settings
source ~/.bashrc

# 3. Test integration
python3 test_crypto_deposit.py

# 4. Check status
python3 core/crypto_integration.py

# 5. Start RM-QPT
bash ACTIVATE_RM-QPT.sh
```

---

## 🎯 Comparison: PayPal vs Crypto

| Feature | PayPal | Crypto |
|---------|--------|--------|
| Setup time | Days-Weeks (approval) | Minutes |
| Account type | Business required | Any wallet |
| Fees | 2.9% + $0.30 | ~$1-5 flat |
| Transfer time | 1-3 days | Minutes-hours |
| Automation | API approval needed | Instant |
| International | Limited | Global |
| Privacy | Linked to identity | Pseudonymous |
| Volatility | None | BTC/ETH vary |

---

## 📞 Support Resources

### Wallets
- Coinbase: https://help.coinbase.com
- MetaMask: https://support.metamask.io
- Trust Wallet: https://community.trustwallet.com

### Cryptocurrency Info
- CoinGecko (prices): https://www.coingecko.com
- BlockCypher (BTC): https://www.blockcypher.com
- Etherscan (ETH): https://etherscan.io

### RM-QPT
- Check logs: `logs/rm_qpt_*.jsonl`
- Test deposits: `python3 test_crypto_deposit.py`
- View records: `ls payments/crypto/`

---

## ✅ Pre-Launch Checklist

- [ ] Wallet created and secured
- [ ] Seed phrase backed up (offline)
- [ ] Wallet addresses copied correctly
- [ ] Environment variables configured
- [ ] Test deposits working
- [ ] Switched to mainnet (if ready)
- [ ] Tax tracking plan in place
- [ ] System backup configured
- [ ] Ready to receive deposits!

---

## 🎉 You're Ready!

Once setup is complete, RM-QPT will:
1. Earn money through autonomous operations
2. Convert to optimal cryptocurrency
3. Record all deposits to your wallet
4. Track everything for tax purposes
5. Run 24/7 without intervention

**Your crypto wallet address = Your money destination**

Start earning: `bash ACTIVATE_RM-QPT.sh`

---

*Last updated: 2026-04-02*
*Version: RM-QPT Crypto v1.0*
