#!/bin/bash
# CLEANUP LEGACY FILES
# Archives old systems to avoid confusion

cd /home/asbelcas/rm-qpt

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "  LEGACY SYSTEM CLEANUP"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""
echo "This will archive old/unused systems to the 'archive/' folder"
echo ""
echo "CURRENT ACTIVE SYSTEM:"
echo "  • REAL_SLEEP_MONEY.py"
echo "  • real_sleep_money.db"
echo "  • RUN_REAL_MONEY.sh"
echo ""
echo "FILES TO ARCHIVE:"
echo ""

# List files to be archived
declare -a LEGACY_FILES=(
    "SLEEP_MONEY.py:Old simulation (hallucination)"
    "PASSIVE_INCOME_ENGINE.py:Analysis tool (not 24/7)"
    "MONEY_MAKER.py:Manual job fetcher"
    "EMERGENCY_MONEY_MODE.py:Manual entry mode"
    "sleep_money.db:Old simulation database"
    "passive_income.db:Analysis database"
    "real_money.db:Old real money db"
    "emergency_money.db:Emergency mode db"
    "money_tracker.db:Money tracker (legacy)"
)

for item in "${LEGACY_FILES[@]}"; do
    file="${item%%:*}"
    desc="${item##*:}"
    if [ -f "$file" ]; then
        echo "  ⚠️  $file ($desc)"
    fi
done

echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""
read -p "Proceed with archiving? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Archiving files..."

mkdir -p archive

# Archive with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_DIR="archive/legacy_${TIMESTAMP}"
mkdir -p "$ARCHIVE_DIR"

# Move legacy files
for item in "${LEGACY_FILES[@]}"; do
    file="${item%%:*}"
    if [ -f "$file" ]; then
        mv "$file" "$ARCHIVE_DIR/"
        echo "  ✅ Archived: $file"
    fi
done

echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "  CLEANUP COMPLETE"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Archived to: $ARCHIVE_DIR"
echo ""
echo "Remaining active files:"
ls -la REAL_SLEEP_MONEY.py RUN_REAL_MONEY.sh MASTER_DASHBOARD.sh real_sleep_money.db 2>/dev/null | awk '{print "  " $9, $5}'
echo ""
echo "To restore archived files:"
echo "  mv $ARCHIVE_DIR/* ."
echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"
