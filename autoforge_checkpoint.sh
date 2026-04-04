#!/bin/bash
# AUTOFORGE-LITE CHECKPOINT MANAGER
# Human approval system for automated submissions

CHECKPOINT_DIR="/home/asbelcas/rm-qpt/checkpoints"
RESPONSE_FILE="/home/asbelcas/rm-qpt/checkpoint_responses.txt"
STATE_FILE="/home/asbelcas/rm-qpt/executor_state.json"

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "🎛️  AUTOFORGE-LITE CHECKPOINT MANAGER"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

# Show current status
echo "📊 SYSTEM STATUS:"
if [ -f "$STATE_FILE" ]; then
    STATUS=$(cat "$STATE_FILE" | grep -o '"status": "[^"]*"' | cut -d'"' -f4)
    SESSION=$(cat "$STATE_FILE" | grep -o '"session_id": "[^"]*"' | cut -d'"' -f4)
    TOTAL=$(cat "$STATE_FILE" | grep -o '"checkpoints_created": [0-9]*' | cut -d' ' -f2)
    APPROVED=$(cat "$STATE_FILE" | grep -o '"checkpoints_approved": [0-9]*' | cut -d' ' -f2)
    
    echo "   Session: $SESSION"
    echo "   Status: $STATUS"
    echo "   Checkpoints Total: $TOTAL | Approved: $APPROVED"
else
    echo "   No active session"
fi

echo ""
echo "────────────────────────────────────────────────────────────────────────────────"
echo "📋 PENDING CHECKPOINTS:"
echo "────────────────────────────────────────────────────────────────────────────────"

# Find pending checkpoints
PENDING_COUNT=0
for checkpoint in "$CHECKPOINT_DIR"/cp_*.json; do
    if [ -f "$checkpoint" ]; then
        PENDING_COUNT=$((PENDING_COUNT + 1))
        ID=$(basename "$checkpoint" .json)
        
        # Extract job info
        JOB_TITLE=$(cat "$checkpoint" | grep -o '"job_title": "[^"]*"' | cut -d'"' -f4)
        PLATFORM=$(cat "$checkpoint" | grep -o '"platform": "[^"]*"' | cut -d'"' -f4)
        BUDGET=$(cat "$checkpoint" | grep -o '"budget": "[^"]*"' | cut -d'"' -f4)
        
        echo ""
        echo "────────────────────────────────────────────────────────────────────────────────"
        echo "   Checkpoint ID: $ID"
        echo "   Job: $JOB_TITLE"
        echo "   Platform: $PLATFORM"
        echo "   Budget: $BUDGET"
        echo ""
        echo "   📁 Full package: $checkpoint"
        echo ""
        echo "   ACTIONS:"
        echo "   ✅ APPROVE: ./autoforge_checkpoint.sh approve $ID"
        echo "   ❌ REJECT:  ./autoforge_checkpoint.sh reject $ID"
        echo "   📝 EDIT:    nano $checkpoint"
    fi
done

if [ $PENDING_COUNT -eq 0 ]; then
    echo "   No pending checkpoints found."
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"

# Handle command-line arguments
if [ "$1" = "approve" ] && [ -n "$2" ]; then
    CHECKPOINT_ID="$2"
    echo "✅ APPROVING: $CHECKPOINT_ID"
    echo "$CHECKPOINT_ID:approve" >> "$RESPONSE_FILE"
    echo "Checkpoint approved. Browser automation will proceed."
    
    # Show proposal preview
    FILE="$CHECKPOINT_DIR/$CHECKPOINT_ID.json"
    if [ -f "$FILE" ]; then
        echo ""
        echo "PROPOSAL PREVIEW:"
        cat "$FILE" | grep -o '"proposal_text": "[^"]*"' | cut -d'"' -f4 | head -5
    fi
    
    echo ""
    echo "Run ./autoforge_checkpoint.sh to see updated status"
    
elif [ "$1" = "reject" ] && [ -n "$2" ]; then
    CHECKPOINT_ID="$2"
    echo "❌ REJECTING: $CHECKPOINT_ID"
    echo "$CHECKPOINT_ID:reject" >> "$RESPONSE_FILE"
    echo "Checkpoint rejected. Job will be skipped."
    echo ""
    echo "Run ./autoforge_checkpoint.sh to see updated status"
    
elif [ "$1" = "list" ]; then
    # Just show list (already done above)
    :
    
else
    echo ""
    echo "USAGE:"
    echo "  ./autoforge_checkpoint.sh              - Show dashboard"
    echo "  ./autoforge_checkpoint.sh list         - List pending checkpoints"
    echo "  ./autoforge_checkpoint.sh approve <id> - Approve checkpoint"
    echo "  ./autoforge_checkpoint.sh reject <id>  - Reject checkpoint"
fi

echo ""
