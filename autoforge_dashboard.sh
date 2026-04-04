#!/bin/bash

# AUTOFORGE-LITE DASHBOARD
# Control center for the calibrated autonomy system

cd /home/asbelcas/rm-qpt

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║           🔥 AUTOFORGE-LITE CONTROL CENTER                        ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "Time: $(date '+%I:%M %p')"
echo ""

# Check if AUTOFORGE is running
if pgrep -f "AUTOFORGE_LITE.py" > /dev/null; then
    PID=$(pgrep -f "AUTOFORGE_LITE.py" | head -1)
    RUNTIME=$(ps -o etime= -p $PID 2>/dev/null | tr -d ' ')
    echo "✅ AUTOFORGE-LITE: RUNNING (PID: $PID, Runtime: $RUNTIME)"
    STATUS="RUNNING"
else
    echo "⚠️  AUTOFORGE-LITE: NOT RUNNING"
    STATUS="STOPPED"
fi

echo ""

# Show autonomy level
if [ -f "autoforge_state.json" ]; then
    AUTONOMY=$(cat autoforge_state.json | grep autonomy_level | cut -d'"' -f4)
    echo "🎚️  Current Autonomy Level: $AUTONOMY"
    
    PENDING=$(cat autoforge_state.json | grep pending_checkpoints | cut -d':' -f2 | tr -d ' ,')
    echo "⏸️  Pending Checkpoints: $PENDING"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "  📋 PENDING CHECKPOINTS"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# List pending checkpoints
if [ -d "checkpoints" ]; then
    PENDING_FILES=$(ls checkpoints/*_pending.json 2>/dev/null | wc -l)
    
    if [ "$PENDING_FILES" -gt 0 ]; then
        echo "Found $PENDING_FILES checkpoint(s) awaiting your approval:"
        echo ""
        
        for file in checkpoints/*_pending.json; do
            if [ -f "$file" ]; then
                CP_ID=$(basename "$file" _pending.json)
                echo "  📌 $CP_ID"
                
                # Extract key info
                if command -v python3 &> /dev/null; then
                    python3 -c "
import json
with open('$file') as f:
    data = json.load(f)
    print(f\"    Task: {data.get('task_id', 'unknown')}\")
    print(f\"    Reason: {data.get('reason', 'unknown')}\")
    print(f\"    Created: {data.get('timestamp_created', 'unknown')}\")
" 2>/dev/null
                fi
                echo ""
            fi
        done
        
        echo "To approve: echo 'checkpoint_id:approve' >> checkpoint_responses.txt"
        echo "To reject:  echo 'checkpoint_id:reject' >> checkpoint_responses.txt"
    else
        echo "✅ No pending checkpoints"
    fi
else
    echo "No checkpoints directory"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "  📊 SYSTEM STATUS"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# Show recent activity
if [ -d "logs" ]; then
    LATEST_LOG=$(ls -t logs/autoforge_*.log 2>/dev/null | head -1)
    if [ -n "$LATEST_LOG" ]; then
        echo "Latest log: $(basename $LATEST_LOG)"
        echo ""
        echo "Recent activity:"
        tail -10 "$LATEST_LOG" | grep -E "CHECKPOINT|ROLE:|✅|⏸️" | tail -5
    fi
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "  🎮 QUICK ACTIONS"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

if [ "$STATUS" = "STOPPED" ]; then
    echo "  🔴 START SYSTEM:"
    echo "     nohup python3 AUTOFORGE_LITE.py > logs/autoforge.log 2>&1 &"
    echo ""
fi

echo "  📋 VIEW CHECKPOINTS:"
echo "     ls checkpoints/"
echo "     cat checkpoints/cp_*.txt"
echo ""

echo "  ✅ APPROVE CHECKPOINT:"
echo "     echo 'checkpoint_id:approve' >> checkpoint_responses.txt"
echo ""

echo "  ❌ REJECT CHECKPOINT:"
echo "     echo 'checkpoint_id:reject' >> checkpoint_responses.txt"
echo ""

echo "  📊 VIEW LOGS:"
echo "     tail -f logs/autoforge_*.log"
echo ""

if [ "$STATUS" = "RUNNING" ]; then
echo "  🛑 STOP SYSTEM:"
echo "     kill $PID"
echo ""
fi

echo "═══════════════════════════════════════════════════════════════════"
echo ""

if [ "$PENDING_FILES" -gt 0 ]; then
    echo "⚠️  ACTION REQUIRED: You have $PENDING_FILES checkpoint(s) waiting for approval"
    echo "   Review the checkpoints above and approve/reject as needed"
elif [ "$STATUS" = "RUNNING" ]; then
    echo "✅ System running smoothly - monitoring for opportunities"
fi

echo ""
