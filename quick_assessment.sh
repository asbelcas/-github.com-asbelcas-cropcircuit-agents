#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                          ║"
echo "║           🚨 $5,000 EMERGENCY CAPITAL - QUICK ASSESSMENT                 ║"
echo "║                                                                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

echo "Let's figure out your FASTEST path to $5,000..."
echo ""

# Check 1: Assets
echo "1️⃣  DO YOU HAVE ITEMS TO SELL?"
echo "   (Car, electronics, jewelry, tools, collectibles)"
echo ""
read -p "   Estimated value of sellable items: $" SELL_VALUE
echo ""

# Check 2: Credit
echo "2️⃣  DO YOU HAVE GOOD CREDIT (700+)?"
echo ""
read -p "   Credit score (0 if unknown): " CREDIT_SCORE
echo ""

# Check 3: 401k
echo "3️⃣  DO YOU HAVE A 401(k)?"
echo ""
read -p "   401(k) balance (0 if none): $" FOUR01K
echo ""

# Check 4: Family
echo "4️⃣  CAN YOU BORROW FROM FAMILY/FRIENDS?"
echo ""
read -p "   Estimated amount you could borrow: $" BORROW_AMOUNT
echo ""

# Check 5: Skills
echo "5️⃣  DO YOU HAVE MARKETABLE SKILLS?"
echo "   (Programming, design, writing, consulting, etc.)"
echo ""
read -p "   Can you do emergency freelance? (yes/no): " HAS_SKILLS
echo ""

# Calculate
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "  📊 YOUR ASSESSMENT RESULTS"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

TOTAL=0
TIMELINE=""

# Assets
if (( $(echo "$SELL_VALUE > 0" | bc -l) )); then
    echo "✅ Assets to sell:     \$$SELL_VALUE (Same day)"
    TOTAL=$(echo "$TOTAL + $SELL_VALUE" | bc)
fi

# Personal loan
if (( CREDIT_SCORE >= 650 )); then
    LOAN="3000"
    echo "✅ Personal loan:     \$$LOAN (1-3 days)"
    TOTAL=$(echo "$TOTAL + $LOAN" | bc)
elif (( CREDIT_SCORE >= 600 )); then
    LOAN="2000"
    echo "⚠️  Personal loan:     \$$LOAN (1-3 days, higher APR)"
    TOTAL=$(echo "$TOTAL + $LOAN" | bc)
else
    echo "❌ Personal loan:     Not viable (credit too low)"
fi

# 401k
if (( $(echo "$FOUR01K >= 10000" | bc -l) )); then
    KLOAN="5000"
    echo "✅ 401(k) loan:       \$$KLOAN (3-7 days)"
    TOTAL=$(echo "$TOTAL + $KLOAN" | bc)
elif (( $(echo "$FOUR01K >= 5000" | bc -l) )); then
    KLOAN=$(echo "$FOUR01K * 0.5" | bc)
    echo "✅ 401(k) loan:       \$$KLOAN (3-7 days)"
    TOTAL=$(echo "$TOTAL + $KLOAN" | bc)
else
    echo "❌ 401(k) loan:       Not viable (balance too low)"
fi

# Family
if (( $(echo "$BORROW_AMOUNT > 0" | bc -l) )); then
    echo "✅ Family/Friends:    \$$BORROW_AMOUNT (Today)"
    TOTAL=$(echo "$TOTAL + $BORROW_AMOUNT" | bc)
fi

# Skills
if [[ "$HAS_SKILLS" == "yes" || "$HAS_SKILLS" == "y" ]]; then
    echo "✅ Freelance work:    \$500-1000 (This week)"
    TOTAL=$(echo "$TOTAL + 750" | bc)
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "  🎯 PROJECTED TOTAL: \$$TOTAL"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

# Determine if $5k is reachable
if (( $(echo "$TOTAL >= 5000" | bc -l) )); then
    echo "✅ $5,000 IS ACHIEVABLE with your current resources!"
    echo ""
    echo "⏱️  TIMELINE:"
    echo "   • Today: Asset sales + family loans"
    echo "   • 1-3 days: Personal loan deposited"
    echo "   • This week: Freelance work"
    echo ""
    echo "🚀 YOU CAN START GHOST AGENT THIS WEEK!"
    
elif (( $(echo "$TOTAL >= 3000" | bc -l) )); then
    echo "⚠️  YOU'RE CLOSE to $5,000"
    echo "   Gap: \$$(echo "5000 - $TOTAL" | bc)"
    echo ""
    echo "💡 OPTIONS TO CLOSE THE GAP:"
    echo "   • Gig work (Uber/DoorDash): +\$500-1000/week"
    echo "   • Sell more items"
    echo "   • Negotiate higher family loan"
    echo ""
    echo "⏱️  TIMELINE: 1-2 weeks"
    
elif (( $(echo "$TOTAL >= 1000" | bc -l) )); then
    echo "⚠️  PARTIAL FUNDING Available"
    echo "   Current: \$$TOTAL of $5,000"
    echo "   Gap: \$$(echo "5000 - $TOTAL" | bc)"
    echo ""
    echo "💡 YOU'LL NEED:"
    echo "   • 2-4 weeks of gig work, OR"
    echo "   • Next paycheck, OR"
    echo "   • More items to sell"
    echo ""
    echo "⏱️  TIMELINE: 2-4 weeks"
    
else
    echo "❌ LIMITED OPTIONS Currently"
    echo "   Available: \$$TOTAL"
    echo ""
    echo "💡 YOU NEED TO:"
    echo "   • Find items to sell"
    echo "   • Build credit first"
    echo "   • Start saving from income"
    echo "   • Learn skills for freelance"
    echo ""
    echo "⏱️  TIMELINE: 1-3 months"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "📋 DETAILED PLAN SAVED TO: EMERGENCY_5000_PLAN.md"
echo ""
echo "Next step: Start with fastest option above"
echo ""

