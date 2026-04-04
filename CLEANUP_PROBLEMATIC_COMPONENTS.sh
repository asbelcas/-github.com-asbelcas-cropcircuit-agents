#!/bin/bash
# =============================================================================
# CLEANUP_PROBLEMATIC_COMPONENTS.sh - Remove Harmful Automation
# =============================================================================
# This script removes components that violate platform Terms of Service
# or constitute unauthorized access to financial systems.
# =============================================================================

set -e

echo "============================================================================="
echo "  🧹 CLEANUP: Removing Problematic Components"
echo "============================================================================="
echo ""
echo "WARNING: This will remove files that:"
echo "  - Automate Coinbase with anti-detection evasion"
echo "  - Automate Upwork/Fiverr proposal submissions"
echo "  - Contain fake/simulated crypto transactions"
echo "  - Include anti-detection/evasion systems"
echo ""
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Cancelled."
    exit 1
fi

# Create archive directory for removed files
ARCHIVE_DIR="/home/asbelcas/ARCHIVED_PROBLEMATIC_COMPONENTS_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$ARCHIVE_DIR"
echo ""
echo "Archive directory: $ARCHIVE_DIR"
echo ""

# =============================================================================
# 1. ARCHIVE AND REMOVE COINBASE AUTOMATION
# =============================================================================
echo "[1/5] Archiving Coinbase automation components..."

if [ -f "core/coinbase_automation_system.py" ]; then
    cp core/coinbase_automation_system.py "$ARCHIVE_DIR/"
    rm core/coinbase_automation_system.py
    echo "  ✅ Removed: core/coinbase_automation_system.py"
fi

if [ -f "core/anti_detection_system.py" ]; then
    cp core/anti_detection_system.py "$ARCHIVE_DIR/"
    rm core/anti_detection_system.py
    echo "  ✅ Removed: core/anti_detection_system.py"
fi

if [ -f "ANTI_DETECTION_GUIDE.md" ]; then
    cp ANTI_DETECTION_GUIDE.md "$ARCHIVE_DIR/"
    rm ANTI_DETECTION_GUIDE.md
    echo "  ✅ Removed: ANTI_DETECTION_GUIDE.md"
fi

# =============================================================================
# 2. ARCHIVE AND REMOVE FREELANCE PLATFORM BOTS
# =============================================================================
echo ""
echo "[2/5] Archiving freelance platform automation..."

for file in AUTOFORGE_BROWSER.py AUTOFORGE_BROWSER_V2.py AUTOFORGE_EXECUTOR.py AUTOFORGE_HYBRID.py AUTOFORGE_LITE.py; do
    if [ -f "$file" ]; then
        cp "$file" "$ARCHIVE_DIR/"
        rm "$file"
        echo "  ✅ Removed: $file"
    fi
done

# =============================================================================
# 3. ARCHIVE AND REMOVE FAKE CRYPTO TRANSACTIONS
# =============================================================================
echo ""
echo "[3/5] Archiving fake crypto transaction records..."

if [ -d "payments/crypto" ]; then
    CRYPTO_COUNT=$(ls payments/crypto/*.json 2>/dev/null | wc -l)
    if [ "$CRYPTO_COUNT" -gt 0 ]; then
        mkdir -p "$ARCHIVE_DIR/payments_crypto"
        cp payments/crypto/*.json "$ARCHIVE_DIR/payments_crypto/" 2>/dev/null || true
        rm -rf payments/crypto/*.json
        echo "  ✅ Removed: $CRYPTO_COUNT fake transaction files from payments/crypto/"
    fi
fi

# =============================================================================
# 4. ARCHIVE AND REMOVE OTHER AUTOMATION EVASION
# =============================================================================
echo ""
echo "[4/5] Archiving other evasion components..."

# Remove stealth modules
for file in core/stealth*.py core/evasion*.py core/ghost*.py core/spoof*.py; do
    if [ -f "$file" ]; then
        cp "$file" "$ARCHIVE_DIR/"
        rm "$file"
        echo "  ✅ Removed: $file"
    fi
done

# Remove platform-specific automation configs
for file in configs/upwork*.json configs/fiverr*.json configs/coinbase*.json; do
    if [ -f "$file" ]; then
        cp "$file" "$ARCHIVE_DIR/"
        rm "$file"
        echo "  ✅ Removed: $file"
    fi
done

# =============================================================================
# 5. CLEANUP REFERENCES IN OTHER FILES
# =============================================================================
echo ""
echo "[5/5] Cleaning up references in remaining files..."

# Note: This is a placeholder - actual cleanup would require sed/awk
# to remove import statements and function calls
# For now, we document what needs manual review

cat > "$ARCHIVE_DIR/CLEANUP_MANIFEST.md" << 'EOF'
# Cleanup Manifest

## Date
Cleanup performed: $(date)

## Files Removed

### Coinbase Automation
- core/coinbase_automation_system.py
- core/anti_detection_system.py
- ANTI_DETECTION_GUIDE.md

### Freelance Platform Bots
- AUTOFORGE_BROWSER.py
- AUTOFORGE_BROWSER_V2.py
- AUTOFORGE_EXECUTOR.py
- AUTOFORGE_HYBRID.py
- AUTOFORGE_LITE.py

### Fake Crypto Transactions
- payments/crypto/*.json (all simulated transaction files)

### Other Evasion Components
- Any core/stealth*.py, core/evasion*.py files found

## Manual Review Required

The following files may contain references to removed components
and should be reviewed manually:

- REAL_SLEEP_MONEY.py - May reference automation components
- MONEY_LOOP.py - Check for anti-detection imports
- START_MONEY.sh - Check for automation launchers
- Any file importing from core/ module

## What Was Preserved

Legitimate components kept:
- General task management (CROPCIRCUIT_AGENT.py)
- Revenue tracking (AGENT_REVENUE.py)
- Client management (AGENT_CLIENT.py)
- Data collection (non-platform-specific)
- Documentation (except ANTI_DETECTION_GUIDE.md)

## Next Steps

1. Review remaining files for broken imports
2. Test that legitimate systems still work
3. Update documentation to reflect removed features
4. Consider building legitimate alternatives using proper APIs
EOF

echo "  ✅ Created cleanup manifest: $ARCHIVE_DIR/CLEANUP_MANIFEST.md"

# =============================================================================
# SUMMARY
# =============================================================================
echo ""
echo "============================================================================="
echo "  ✅ CLEANUP COMPLETE"
echo "============================================================================="
echo ""
echo "Archived files location: $ARCHIVE_DIR"
echo ""
echo "REMAINING LEGITIMATE COMPONENTS:"
echo "  ✓ Task management (CROPCIRCUIT_AGENT.py)"
echo "  ✓ Revenue tracking (AGENT_REVENUE.py)"
echo "  ✓ Client management (AGENT_CLIENT.py)"
echo "  ✓ Data collection (general)"
echo "  ✓ Documentation"
echo ""
echo "NEXT STEPS:"
echo "  1. Review remaining files for broken imports"
echo "  2. Test legitimate systems still work"
echo "  3. Update documentation"
echo "  4. git add -A && git commit -m 'Remove problematic automation components'"
echo "  5. git push origin main"
echo ""
echo "============================================================================="
