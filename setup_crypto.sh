#!/bin/bash

# RM-QPT Crypto Wallet Setup Script
# Configures environment variables for crypto deposits

echo "======================================================================"
echo "  🔐 RM-QPT CRYPTO WALLET SETUP"
echo "======================================================================"
echo ""
echo "This script will help you configure cryptocurrency wallets for"
echo "automated deposits from the RM-QPT system."
echo ""
echo "Supported cryptocurrencies:"
echo "  • BTC (Bitcoin) - Best for large amounts"
echo "  • ETH (Ethereum) - Good for medium amounts"
echo "  • USDC (USD Coin) - Stable, best for small amounts"
echo ""
echo "Press Ctrl+C to cancel, or wait 3 seconds to continue..."
sleep 3

# Determine shell config file
if [ -f "$HOME/.bashrc" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
elif [ -f "$HOME/.zshrc" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
else
    SHELL_CONFIG="$HOME/.profile"
fi

echo ""
echo "Shell configuration file: $SHELL_CONFIG"
echo ""

# Function to add env var if not exists
add_env_var() {
    local var_name=$1
    local var_value=$2
    
    if grep -q "^export $var_name=" "$SHELL_CONFIG" 2>/dev/null; then
        echo "  $var_name already set in $SHELL_CONFIG"
    else
        echo "export $var_name=\"$var_value\"" >> "$SHELL_CONFIG"
        echo "  ✓ Added $var_name to $SHELL_CONFIG"
    fi
}

# Collect wallet addresses
echo "Enter your cryptocurrency wallet addresses:"
echo "(Leave blank if you don't have one - you can add later)"
echo ""

read -p "Bitcoin (BTC) wallet address: " BTC_WALLET
read -p "Ethereum (ETH) wallet address: " ETH_WALLET
read -p "USDC wallet address (press Enter to use ETH address): " USDC_WALLET

# Default USDC to ETH if not provided
if [ -z "$USDC_WALLET" ]; then
    USDC_WALLET="$ETH_WALLET"
fi

# Set crypto mode
read -p "Use mainnet (real money) or testnet (testing)? [mainnet/testnet] (default: testnet): " CRYPTO_MODE
if [ -z "$CRYPTO_MODE" ]; then
    CRYPTO_MODE="testnet"
fi

echo ""
echo "======================================================================"
echo "  💾 Saving Configuration"
echo "======================================================================"
echo ""

# Add to shell config
add_env_var "CRYPTO_MODE" "$CRYPTO_MODE"
add_env_var "BTC_WALLET_ADDRESS" "$BTC_WALLET"
add_env_var "ETH_WALLET_ADDRESS" "$ETH_WALLET"
add_env_var "USDC_WALLET_ADDRESS" "$USDC_WALLET"

echo ""
echo "======================================================================"
echo "  ✅ Configuration Saved!"
echo "======================================================================"
echo ""
echo "To apply these changes, run:"
echo "  source $SHELL_CONFIG"
echo ""
echo "Or restart your terminal."
echo ""
echo "Your wallet addresses:"
[ -n "$BTC_WALLET" ] && echo "  BTC: $BTC_WALLET"
[ -n "$ETH_WALLET" ] && echo "  ETH: $ETH_WALLET"
[ -n "$USDC_WALLET" ] && echo "  USDC: $USDC_WALLET"
echo ""
echo "Mode: $CRYPTO_MODE"
echo ""

if [ -z "$BTC_WALLET" ] && [ -z "$ETH_WALLET" ]; then
    echo "⚠️  WARNING: No wallet addresses configured!"
    echo "    The system will record deposits but cannot send crypto."
    echo "    Run this script again to add wallet addresses."
    echo ""
fi

# Optional: API keys for balance checking
read -p "Would you like to add API keys for balance checking? [y/N]: " ADD_API_KEYS
if [[ $ADD_API_KEYS =~ ^[Yy]$ ]]; then
    echo ""
    echo "API Keys (optional - for balance checking):"
    read -p "BlockCypher API Key (for BTC): " BLOCKCYPHER_KEY
    read -p "Etherscan API Key (for ETH/USDC): " ETHERSCAN_KEY
    
    [ -n "$BLOCKCYPHER_KEY" ] && add_env_var "BLOCKCYPHER_API_KEY" "$BLOCKCYPHER_KEY"
    [ -n "$ETHERSCAN_KEY" ] && add_env_var "ETHERSCAN_API_KEY" "$ETHERSCAN_KEY"
    
    echo ""
    echo "✓ API keys added"
fi

echo ""
echo "======================================================================"
echo "  📚 Next Steps"
echo "======================================================================"
echo ""
echo "1. Apply configuration:"
echo "   source $SHELL_CONFIG"
echo ""
echo "2. Test crypto integration:"
echo "   python3 core/crypto_integration.py"
echo ""
echo "3. Run deposit test:"
echo "   python3 test_crypto_deposit.py"
echo ""
echo "4. Start RM-QPT with crypto enabled:"
echo "   bash ACTIVATE_RM-QPT.sh"
echo ""
echo "======================================================================"
