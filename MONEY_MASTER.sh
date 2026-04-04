#!/bin/bash
# MONEY MASTER - The definitive money-making control center
# NO HALLUCINATION - Shows both estimated value AND actual revenue

cd /home/asbelcas/rm-qpt

clear
echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                          ║"
echo "║   💰 MONEY MASTER - Actual Revenue System                                ║"
echo "║                                                                          ║"
echo "║   NO HALLUCINATION - Real Assets + Real Sales                            ║"
echo "║                                                                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Show unified dashboard
python3 ACTUAL_MONEY_MASTER.py dashboard

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "WHAT YOU SEE ABOVE:"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "  📊 ESTIMATED VALUE = Worth of files/data created by automation"
echo "  💵 ACTUAL REVENUE  = Real money from real sales ( PayPal/bank )"
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "ACTIONS:"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "  1) 🚀 Start 24/7 Asset Creation (REAL_SLEEP_MONEY)"
echo "     → Automatically creates data files and scripts"
echo "     → Runs continuously in background"
echo ""
echo "  2) 🏭 Create Product for Sale (REAL_MONEY_SYSTEM)"
echo "     → Create professional product ready for marketplace"
echo ""
echo "  3) 💰 Record a Real Sale"
echo "     → When someone buys your product, record it here"
echo ""
echo "  4) 📊 View Complete Dashboard"
echo "     → See both estimated value AND actual revenue"
echo ""
echo "  5) 📚 Explain the Numbers"
echo "     → Understand estimated vs actual"
echo ""
echo "  6) 🛑 Stop Background Process"
echo "     → Stop the 24/7 asset creation engine"
echo ""
echo "  7) ❌ Exit"
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

read -p "Select action (1-7): " choice

case $choice in
    1)
        echo ""
        echo "🚀 Starting 24/7 Asset Creation..."
        echo "This creates files/data automatically."
        echo ""
        
        # Check if already running
        PID=$(pgrep -f "REAL_SLEEP_MONEY.py start" | head -1)
        if [ -n "$PID" ]; then
            echo "Already running (PID $PID)"
        else
            python3 REAL_SLEEP_MONEY.py start &
            echo "Started in background (PID $!)"
        fi
        ;;
    
    2)
        echo ""
        echo "🏭 Creating product for sale..."
        python3 << 'PYEOF'
import sys
sys.path.insert(0, '/home/asbelcas/rm-qpt')
from REAL_MONEY_SYSTEM import RealMoneySystem

system = RealMoneySystem()

print("\nAvailable product types:")
print("  1) web_scraper_pro - $29")
print("  2) data_cleaner_pro - $19")
print("  3) automation_bot - $39")
print("")

choice = input("Select (1-3): ").strip()

products = {
    "1": ("web_scraper_pro", 29.00),
    "2": ("data_cleaner_pro", 19.00),
    "3": ("automation_bot", 39.00)
}

if choice in products:
    name, price = products[choice]
    system.create_sellable_product(name, price)
    print(f"\n✅ Product created! Next steps:")
    print(f"   1. Go to gumroad.com")
    print(f"   2. Create new product")
    print(f"   3. Upload: products_for_sale/{name}_*.py")
    print(f"   4. Set price: ${price}")
    print(f"   5. When it sells, record it here (option 3)")
else:
    print("Invalid choice")
PYEOF
        ;;
    
    3)
        echo ""
        echo "💰 Recording a real sale..."
        python3 << 'PYEOF'
import sys
sys.path.insert(0, '/home/asbelcas/rm-qpt')
from REAL_MONEY_SYSTEM import RealMoneySystem

system = RealMoneySystem()

print("\nRecord actual sale:")
product = input("Product name: ").strip()
price = float(input("Sale price ($): ").strip())
marketplace = input("Marketplace (gumroad/etc): ").strip()
email = input("Buyer email: ").strip()

system.record_real_sale(product, price, marketplace, email)
print("\n✅ Sale recorded in ACTUAL REVENUE")
PYEOF
        ;;
    
    4)
        echo ""
        python3 ACTUAL_MONEY_MASTER.py dashboard
        ;;
    
    5)
        echo ""
        python3 ACTUAL_MONEY_MASTER.py explain
        ;;
    
    6)
        echo ""
        PID=$(pgrep -f "REAL_SLEEP_MONEY.py start" | head -1)
        if [ -n "$PID" ]; then
            kill $PID 2>/dev/null
            echo "🛑 Stopped (PID $PID)"
        else
            echo "Not running"
        fi
        ;;
    
    7)
        echo ""
        echo "Money master closed."
        exit 0
        ;;
    
    *)
        echo ""
        echo "Invalid option"
        ;;
esac

echo ""
read -p "Press Enter to return to menu..."
exec "$0"
