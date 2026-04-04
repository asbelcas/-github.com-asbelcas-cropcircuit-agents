#!/bin/bash

# CROP CIRCUIT - COMMAND DASHBOARD v2.0
# Shows ACTUAL system status

cd /home/asbelcas/rm-qpt

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║           🤖 CROP CIRCUIT - COMMAND DASHBOARD v2.0                ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "Time: $(date '+%I:%M %p')"
echo ""

# Check if AUTO_EXECUTOR is actually running
if [ -f "auto_executor.pid" ]; then
    PID=$(cat auto_executor.pid)
    if ps -p $PID > /dev/null 2>&1; then
        RUNTIME=$(ps -o etime= -p $PID 2>/dev/null | tr -d ' ')
        echo "✅ AUTO_EXECUTOR: RUNNING (PID: $PID, Runtime: $RUNTIME)"
        STATUS="RUNNING"
    else
        echo "⚠️  AUTO_EXECUTOR: STOPPED (stale PID file)"
        rm -f auto_executor.pid
        STATUS="STOPPED"
    fi
else
    echo "⚠️  AUTO_EXECUTOR: NOT RUNNING"
    STATUS="STOPPED"
fi

# Check for other ghost processes
GHOST_PIDS=$(pgrep -f "ghost_real_auto\|ghost_worker" | wc -l)
if [ "$GHOST_PIDS" -gt 0 ]; then
    echo "⚠️  Ghost Trading: $GHOST_PIDS process(es) running"
else
    echo "✅ Ghost Trading: STOPPED (as requested)"
fi

echo ""

# Show created resources
echo "📁 CREATED RESOURCES:"
echo ""

if [ -d "freelance_profiles" ]; then
    echo "  ✅ Freelance Profiles:"
    for f in freelance_profiles/*.txt; do
        if [ -f "$f" ]; then
            size=$(wc -c < "$f")
            echo "     - $(basename $f) (${size} bytes)"
        fi
    done
    echo ""
fi

if [ -d "proposals" ]; then
    echo "  ✅ Job Proposals:"
    for f in proposals/*.txt; do
        if [ -f "$f" ]; then
            size=$(wc -c < "$f")
            echo "     - $(basename $f) (${size} bytes)"
        fi
    done
    echo ""
fi

if [ -f "opportunity_research.json" ]; then
    size=$(wc -c < opportunity_research.json)
    echo "  ✅ Opportunity Research: ${size} bytes"
    echo ""
fi

# Recent activity
if [ -f "auto_executor_state.json" ]; then
    echo "  ✅ State File: Last updated $(stat -c %y auto_executor_state.json 2>/dev/null | cut -d' ' -f1,2 | cut -d'.' -f1)"
    echo ""
fi

echo "═══════════════════════════════════════════════════════════════════"
echo "  QUICK ACTIONS:"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

if [ "$STATUS" = "STOPPED" ]; then
    echo "  🔴 START THE SYSTEM:"
    echo "     nohup python3 AUTO_EXECUTOR.py > logs/auto.log 2>&1 &"
    echo ""
fi

echo "  📋 VIEW RESOURCES:"
echo "     cat freelance_profiles/upwork_profile.txt"
echo "     cat proposals/web_scraping_proposal.txt"
echo "     cat opportunity_research.json | python3 -m json.tool"
echo ""

echo "  📊 VIEW LOGS:"
echo "     tail -f logs/auto_*.log"
echo "     cat current_status.json"
echo ""

if [ "$STATUS" = "RUNNING" ]; then
echo "  🛑 STOP THE SYSTEM:"
echo "     kill $(cat auto_executor.pid)"
echo ""
fi

echo "═══════════════════════════════════════════════════════════════════"

if [ "$STATUS" = "RUNNING" ]; then
    echo ""
    echo "✅ System is active and monitoring"
    echo "   Last check: $(date '+%H:%M:%S')"
    echo "   Status updates every 5 minutes"
else
    echo ""
    echo "⚠️  System is NOT running"
    echo "   Run the 'START THE SYSTEM' command above"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo ""
