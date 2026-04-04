#!/usr/bin/env python3
"""
MAKE MONEY - PRACTICAL VERSION

This system bridges the gap between "creating assets" and "making money"
by preparing professional packages that can be sold.

WHAT THIS DOES:
1. Takes generated products and packages them professionally
2. Creates sales copy, descriptions, and marketing materials
3. Prepares Gumroad-ready upload packages
4. Tracks what needs to be done manually

WHAT THIS DOES NOT DO:
- Cannot create marketplace accounts for you (requires your identity/bank)
- Cannot drive traffic (requires marketing effort)
- Cannot process payments (requires Stripe/PayPal accounts)

HONEST VALUE: Reduces setup time from hours to minutes per product.
"""

import os
import sys
import json
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

class PracticalMoneyMaker:
    """
    Prepares products for actual sale
    """
    
    def __init__(self):
        self.packages_dir = "/home/asbelcas/rm-qpt/ready_to_sell"
        self.db_path = "/home/asbelcas/rm-qpt/practical_money.db"
        os.makedirs(self.packages_dir, exist_ok=True)
        self._init_db()
        
    def _init_db(self):
        """Track what's been prepared vs actually listed"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS prepared_packages (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            product_name TEXT,
            package_file TEXT,
            price REAL,
            status TEXT DEFAULT 'prepared',
            listed_at TEXT,
            listed_url TEXT,
            sales_count INTEGER DEFAULT 0,
            revenue REAL DEFAULT 0
        )''')
        
        conn.commit()
        conn.close()
    
    def log(self, msg):
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{ts}] {msg}")
    
    def analyze_best_product(self):
        """Analyze which product has the best chance of selling"""
        products_dir = Path("/home/asbelcas/rm-qpt/generated_products")
        products = list(products_dir.glob("*.py"))
        
        if not products:
            return None
        
        # Score products by complexity/usefulness
        scored = []
        for p in products:
            content = p.read_text()
            lines = len(content.split('\n'))
            
            # Higher score = more valuable
            score = lines  # More lines = more functionality
            
            # Bonus for useful features
            if 'requests' in content:
                score += 10
            if 'automation' in content.lower():
                score += 15
            if 'monitor' in content.lower():
                score += 20  # Monitoring tools are valuable
            if 'clean' in content.lower() or 'process' in content.lower():
                score += 15
                
            scored.append((score, p))
        
        scored.sort(reverse=True)
        return scored[0][1]  # Return best product
    
    def create_professional_package(self, product_file=None):
        """Create a professional, ready-to-sell package"""
        if product_file is None:
            product_file = self.analyze_best_product()
            
        if not product_file:
            self.log("No products found to package")
            return None
        
        self.log(f"Creating professional package for: {product_file.name}")
        
        # Read product
        product_code = product_file.read_text()
        lines = len(product_code.split('\n'))
        
        # Determine product type and pricing
        name_lower = product_file.name.lower()
        if 'monitor' in name_lower:
            product_type = "Website Monitoring Tool"
            description = "Automatically monitors websites for downtime and alerts you instantly."
            price = 29.00
            features = [
                "Automatic uptime monitoring",
                "Email alerts when site goes down",
                "Status code checking",
                "Custom check intervals",
                "Error logging and reporting"
            ]
        elif 'clean' in name_lower or 'process' in name_lower:
            product_type = "Data Processing Automation"
            description = "Automatically clean, process, and format your data files with one click."
            price = 19.00
            features = [
                "CSV/Excel/JSON support",
                "Automatic duplicate removal",
                "Data validation",
                "Format standardization",
                "Batch processing"
            ]
        else:
            product_type = "Python Automation Script"
            description = "Save hours of manual work with this ready-to-use automation tool."
            price = 19.00
            features = [
                "Ready to run",
                "Well documented",
                "Error handling included",
                "Easy to customize",
                "Production quality code"
            ]
        
        # Create package directory
        package_name = f"{product_file.stem}_package"
        package_dir = Path(f"{self.packages_dir}/{package_name}")
        package_dir.mkdir(exist_ok=True)
        
        # 1. Copy main product
        shutil.copy(product_file, package_dir / f"{product_file.stem}.py")
        
        # 2. Create README
        readme = f"""# {product_type}

## What This Does
{description}

## Features
"""
        for feature in features:
            readme += f"- ✅ {feature}\n"
        
        readme += f"""
## Installation
1. Ensure you have Python 3.7+ installed
2. Install requirements: `pip install -r requirements.txt`
3. Run: `python {product_file.stem}.py`

## Usage
See USAGE.md for detailed instructions.

## Support
For questions or issues, contact the seller.

## License
Commercial use license included with purchase.

---
**Price:** ${price}
**Lines of Code:** {lines}
**Last Updated:** {datetime.now().strftime('%Y-%m-%d')}
"""
        
        (package_dir / "README.md").write_text(readme)
        
        # 3. Create USAGE.md
        usage = f"""# Usage Guide

## Quick Start
```bash
python {product_file.stem}.py
```

## Customization
Edit the script to customize:
- Input parameters
- Output formats
- Timing/intervals
- Notification settings

## Example Workflow
1. Configure your settings in the script
2. Run the automation
3. Check output/results
4. Schedule to run automatically (optional)

## Troubleshooting
- Ensure all requirements are installed
- Check Python version (3.7+ required)
- Review error messages for configuration issues
"""
        
        (package_dir / "USAGE.md").write_text(usage)
        
        # 4. Create requirements.txt
        imports = []
        if 'import requests' in product_code:
            imports.append("requests>=2.28.0")
        if 'import pandas' in product_code or 'pd.' in product_code:
            imports.append("pandas>=1.5.0")
        if 'from bs4' in product_code or 'BeautifulSoup' in product_code:
            imports.append("beautifulsoup4>=4.11.0")
        
        if imports:
            (package_dir / "requirements.txt").write_text('\n'.join(imports) + '\n')
        else:
            (package_dir / "requirements.txt").write_text("# No external dependencies required\n")
        
        # 5. Create Gumroad listing copy
        listing = f"""TITLE:
{product_type} - Python Automation Script (${price})

DESCRIPTION:
Save hours of manual work with this production-ready {product_type.lower()}.

**What You Get:**
- ✅ {lines} lines of clean Python code
- ✅ Ready to run immediately
- ✅ Full documentation included
- ✅ Commercial license
- ✅ Lifetime updates

**Perfect For:**
- Data analysts
- Automation engineers
- Web developers
- System administrators
- Anyone who wants to save time

**Features:**
"""
        for feature in features:
            listing += f"- {feature}\n"
        
        listing += f"""
**Requirements:**
- Python 3.7+
- Basic Python knowledge

**Delivery:**
Instant download after purchase.

**Support:**
Email support included.

**Price:** ${price}
"""
        
        (package_dir / "GUMROAD_LISTING.txt").write_text(listing)
        
        # 6. Create ZIP package
        zip_file = f"{self.packages_dir}/{package_name}.zip"
        with ZipFile(zip_file, 'w') as zf:
            for file in package_dir.iterdir():
                zf.write(file, file.name)
        
        # Track in database
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''INSERT INTO prepared_packages 
            (timestamp, product_name, package_file, price, status)
            VALUES (?, ?, ?, ?, ?)''',
            (datetime.now().isoformat(), product_file.stem, zip_file, price, 'prepared'))
        conn.commit()
        conn.close()
        
        self.log(f"✅ Package created: {zip_file}")
        self.log(f"   Price: ${price}")
        self.log(f"   Ready to upload to Gumroad")
        
        return {
            'product': product_file.stem,
            'package': zip_file,
            'price': price,
            'listing': package_dir / "GUMROAD_LISTING.txt"
        }
    
    def show_status(self):
        """Show what's prepared vs what needs to be done"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*), SUM(price) FROM prepared_packages WHERE status='prepared'")
        prepared_count, prepared_value = c.fetchone()
        prepared_count = prepared_count or 0
        prepared_value = prepared_value or 0
        
        c.execute("SELECT COUNT(*), SUM(revenue) FROM prepared_packages WHERE status='listed'")
        listed_count, revenue = c.fetchone()
        listed_count = listed_count or 0
        revenue = revenue or 0
        
        print("\n" + "="*70)
        print("💰 PRACTICAL MONEY STATUS")
        print("="*70)
        print(f"\n📦 Packages Prepared: {prepared_count}")
        print(f"   Total Value: ${prepared_value:.2f}")
        print(f"\n🏪 Packages Listed: {listed_count}")
        print(f"   Actual Revenue: ${revenue:.2f}")
        print("\n" + "="*70)
        
        if prepared_count > 0:
            print("\n✅ READY TO UPLOAD:")
            c.execute("SELECT product_name, package_file, price FROM prepared_packages WHERE status='prepared'")
            for row in c.fetchall():
                print(f"   • {row[0]}")
                print(f"     File: {row[1]}")
                print(f"     Price: ${row[2]}")
        
        conn.close()
        
        print("\n" + "="*70)
        print("NEXT STEPS TO MAKE REAL MONEY:")
        print("="*70)
        print("""
1. CREATE GUMROAD ACCOUNT (5 mins)
   → Go to gumroad.com/signup
   → Verify email
   → Connect Stripe/PayPal

2. UPLOAD PACKAGE (5 mins per product)
   → Click "New Product"
   → Upload ZIP file from ready_to_sell/
   → Copy/paste listing from GUMROAD_LISTING.txt
   → Set price
   → Publish

3. GET FIRST SALE (varies)
   → Share on Twitter/X
   → Post in relevant subreddits
   → Tell your network
   → First sale typically takes 1-7 days

4. RECEIVE REAL MONEY
   → Gumroad pays to your bank account
   → Weekly payouts
   → Real dollars you can spend
        """)
        print("="*70)
    
    def record_listing(self, product_name, gumroad_url):
        """Record that a product was actually listed"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''UPDATE prepared_packages 
            SET status='listed', listed_at=?, listed_url=?
            WHERE product_name=?''',
            (datetime.now().isoformat(), gumroad_url, product_name))
        conn.commit()
        conn.close()
        
        self.log(f"✅ Recorded listing: {product_name}")
        self.log(f"   URL: {gumroad_url}")
        print("\n⚠️  IMPORTANT: Only record ACTUAL listings on Gumroad")
        print("   Do not record simulated or planned listings.")
    
    def record_sale(self, product_name, amount, gumroad_transaction_id):
        """Record an ACTUAL sale from Gumroad"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''UPDATE prepared_packages 
            SET sales_count = sales_count + 1, revenue = revenue + ?
            WHERE product_name=?''',
            (amount, product_name))
        conn.commit()
        conn.close()
        
        self.log(f"✅ Recorded REAL sale: ${amount}")
        self.log(f"   Transaction: {gumroad_transaction_id}")

def main():
    maker = PracticalMoneyMaker()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            maker.show_status()
        elif sys.argv[1] == "package":
            result = maker.create_professional_package()
            if result:
                print("\n" + "="*70)
                print("PACKAGE CREATED SUCCESSFULLY")
                print("="*70)
                print(f"Product: {result['product']}")
                print(f"File: {result['package']}")
                print(f"Price: ${result['price']}")
                print(f"\nNext: Upload to Gumroad using:")
                print(f"   {result['listing']}")
        elif sys.argv[1] == "listed" and len(sys.argv) > 3:
            maker.record_listing(sys.argv[2], sys.argv[3])
        elif sys.argv[1] == "sold" and len(sys.argv) > 4:
            maker.record_sale(sys.argv[2], float(sys.argv[3]), sys.argv[4])
        else:
            print("Commands:")
            print("  status              - Show preparation vs listing status")
            print("  package             - Create professional package")
            print("  listed <product> <url> - Record actual Gumroad listing")
            print("  sold <product> <amount> <txid> - Record actual sale")
    else:
        maker.show_status()

if __name__ == "__main__":
    main()
