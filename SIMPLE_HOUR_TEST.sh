#!/bin/bash
# Simple hour-long test - records metrics every 5 minutes

cd /home/asbelcas/rm-qpt

LOGFILE="test_logs/simple_hour_test_$(date +%Y%m%d_%H%M%S).log"
mkdir -p test_logs

START_TIME=$(date +%s)
END_TIME=$((START_TIME + 3600))  # 1 hour

echo "═══════════════════════════════════════════════════════════════════════════════" | tee -a $LOGFILE
echo "  SIMPLE HOUR-LONG TEST" | tee -a $LOGFILE
echo "═══════════════════════════════════════════════════════════════════════════════" | tee -a $LOGFILE
echo "Start time: $(date '+%H:%M:%S')" | tee -a $LOGFILE
echo "End time:   $(date -d @${END_TIME} '+%H:%M:%S')" | tee -a $LOGFILE
echo "Duration:   60 minutes" | tee -a $LOGFILE
echo "Checking:   Every 5 minutes" | tee -a $LOGFILE
echo "═══════════════════════════════════════════════════════════════════════════════" | tee -a $LOGFILE

# Get baseline
BASELINE_DATA=$(ls collected_data/*.json 2>/dev/null | wc -l)
BASELINE_PROD=$(ls generated_products/*.py 2>/dev/null | wc -l)
BASELINE_ACT=$(sqlite3 real_sleep_money.db "SELECT COUNT(*) FROM actions;" 2>/dev/null || echo "0")

echo "" | tee -a $LOGFILE
echo "BASELINE (Minute 0):" | tee -a $LOGFILE
echo "  Data files: $BASELINE_DATA" | tee -a $LOGFILE
echo "  Products:   $BASELINE_PROD" | tee -a $LOGFILE
echo "  Actions:    $BASELINE_ACT" | tee -a $LOGFILE
echo "" | tee -a $LOGFILE

MINUTE=0
while [ $(date +%s) -lt $END_TIME ]; do
    sleep 300  # 5 minutes
    MINUTE=$((MINUTE + 5))
    
    CURRENT_TIME=$(date '+%H:%M:%S')
    REMAINING=$(( (END_TIME - $(date +%s)) / 60 ))
    
    # Get current metrics
    CURRENT_DATA=$(ls collected_data/*.json 2>/dev/null | wc -l)
    CURRENT_PROD=$(ls generated_products/*.py 2>/dev/null | wc -l)
    CURRENT_ACT=$(sqlite3 real_sleep_money.db "SELECT COUNT(*) FROM actions;" 2>/dev/null || echo "0")
    
    # Check process
    if pgrep -f "REAL_SLEEP_MONEY.py start" > /dev/null; then
        PROCESS="🟢 Running"
    else
        PROCESS="🔴 Stopped"
    fi
    
    # Calculate changes
    DELTA_DATA=$((CURRENT_DATA - BASELINE_DATA))
    DELTA_PROD=$((CURRENT_PROD - BASELINE_PROD))
    DELTA_ACT=$((CURRENT_ACT - BASELINE_ACT))
    
    echo "═══════════════════════════════════════════════════════════════════════════════" | tee -a $LOGFILE
echo "  CHECKPOINT: Minute $MINUTE/60 | Time: $CURRENT_TIME | Remaining: ${REMAINING}m" | tee -a $LOGFILE
    echo "═══════════════════════════════════════════════════════════════════════════════" | tee -a $LOGFILE
    echo "  Process:    $PROCESS" | tee -a $LOGFILE
    echo "  Data files: $CURRENT_DATA (+$DELTA_DATA)" | tee -a $LOGFILE
    echo "  Products:   $CURRENT_PROD (+$DELTA_PROD)" | tee -a $LOGFILE
    echo "  Actions:    $CURRENT_ACT (+$DELTA_ACT)" | tee -a $LOGFILE
    echo "" | tee -a $LOGFILE
done

# Final report
echo "═══════════════════════════════════════════════════════════════════════════════" | tee -a $LOGFILE
echo "  TEST COMPLETE" | tee -a $LOGFILE
echo "═══════════════════════════════════════════════════════════════════════════════" | tee -a $LOGFILE

FINAL_DATA=$(ls collected_data/*.json 2>/dev/null | wc -l)
FINAL_PROD=$(ls generated_products/*.py 2>/dev/null | wc -l)
FINAL_ACT=$(sqlite3 real_sleep_money.db "SELECT COUNT(*) FROM actions;" 2>/dev/null || echo "0")

TOTAL_DATA=$((FINAL_DATA - BASELINE_DATA))
TOTAL_PROD=$((FINAL_PROD - BASELINE_PROD))
TOTAL_ACT=$((FINAL_ACT - BASELINE_ACT))

echo "" | tee -a $LOGFILE
echo "RESULTS (60 minutes):" | tee -a $LOGFILE
echo "  Data files created: +$TOTAL_DATA" | tee -a $LOGFILE
echo "  Products created:   +$TOTAL_PROD" | tee -a $LOGFILE
echo "  Actions performed:  +$TOTAL_ACT" | tee -a $LOGFILE

if pgrep -f "REAL_SLEEP_MONEY.py start" > /dev/null; then
    echo "  Process status:     ✅ Still running" | tee -a $LOGFILE
else
    echo "  Process status:     ❌ Stopped during test" | tee -a $LOGFILE
fi

echo "" | tee -a $LOGFILE
echo "Log saved to: $LOGFILE" | tee -a $LOGFILE
echo "═══════════════════════════════════════════════════════════════════════════════" | tee -a $LOGFILE
