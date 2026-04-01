# 🎙️ QR-Process Voice Pipeline Setup

## Status: READY TO DEPLOY (Missing API Key)

---

## What's Already Configured

### ✅ Call Script Created
**Location:** `cropcircuit/caseyops/call_scripts/veterinary_sales.txt`

Features:
- AI disclosure in first 10 seconds (compliant)
- Warm transfer to your cell (269-986-8595)
- Objection handling
- Voicemail version
- Safety rules built-in

### ✅ Pipeline Infrastructure
**Location:** `cropcircuit/caseyops/call_pipeline.py`

- Bland.ai integration ready
- Approval workflow for new numbers
- Call logging to database
- Dry-run mode for testing

### ✅ Pre-approved Numbers
These numbers can be called without approval:
- 269-781-4867 (Calhoun Conservation District)
- 269-467-5646 (MSU Extension / Dean Baas)
- 269-781-2849 (Farm Bureau)
- 269-962-3003 (Sprout Urban Farms)
- 269-671-5117 (KBS)
- 269-781-0784 (MSU Extension Calhoun)
- 269-441-1661 (BCFR / Gabriela)

---

## What's Missing

### ❌ Bland.ai API Key
**File:** `cropcircuit/caseyops/.env`
**Current:** `BLAND_API_KEY=""`

**To get:**
1. Sign up at https://www.bland.ai
2. Add credits ($0.09/minute)
3. Get API key from dashboard
4. Add to `.env`:
   ```
   BLAND_API_KEY="your_key_here"
   BLAND_FROM_NUMBER="+1xxxxxxxxxx"  # optional, can use Bland's number
   ```

### ❌ Veterinary Clinic Phone Numbers
The `close_call_sheet_today.md` shows targets but no phone numbers.

**Need:** Phone numbers for:
1. Lakeside Animal Clinic 2
2. Riverside Pet Clinic 10
3. Metro Pet Care 47
4. Urban Paws Clinic 20
5. Highland Animal Hospital 34

---

## How to Use Once Configured

### Test Mode (Dry Run)
```bash
cd cropcircuit/caseyops
python3 -c "from call_pipeline import make_call; make_call('269-781-4867', 'Test Contact', 'veterinary_sales')"
```

### Live Mode
```bash
# Set live mode in .env
LIVE_MODE=true

# Make a call
python3 -m caseyops.call_pipeline 269-XXX-XXXX "Clinic Name" veterinary_sales
```

### Batch 5 Calls (QR-Process Validation)
```bash
#!/bin/bash
# QR_VALIDATION_CALLS.sh

cd cropcircuit/caseyops

# Call 1
python3 -m caseyops.call_pipeline "269-XXX-XXXX" "Lakeside Animal Clinic" veterinary_sales
sleep 30

# Call 2
python3 -m caseyops.call_pipeline "269-XXX-XXXX" "Riverside Pet Clinic" veterinary_sales
sleep 30

# Call 3
python3 -m caseyops.call_pipeline "269-XXX-XXXX" "Metro Pet Care" veterinary_sales
sleep 30

# Call 4
python3 -m caseyops.call_pipeline "269-XXX-XXXX" "Urban Paws Clinic" veterinary_sales
sleep 30

# Call 5
python3 -m caseyops.call_pipeline "269-XXX-XXXX" "Highland Animal Hospital" veterinary_sales

echo "5 validation calls complete. Check caseyops.db for results."
```

---

## QR-Process Voice Integration

### Q - Quantum
**High-probability targets identified:**
- Veterinary clinics with pain points (workload, technology, revenue)
- GOLD tier scores 67-77
- "Call today then email followup" priority

### R - Reduction
**Collapse to singular action:**
- One AI-powered call script
- 5 lower-stakes validation targets
- 3-minute max call duration

### P - Process
**Feedback loop:**
1. AI makes initial contact
2. Interest qualified or rejected
3. Warm transfer OR callback scheduled
4. You close the interested prospects
5. Objections logged for script refinement

---

## Cost Estimate

| Item | Cost |
|------|------|
| Bland.ai | $0.09/minute |
| Average call | ~2 minutes |
| 5 validation calls | ~$0.90 |
| Scaled to 50 calls | ~$9.00 |

---

## Next Actions

1. **Get Bland API key** → https://www.bland.ai
2. **Find clinic phone numbers** → Google/search the 5 targets
3. **Test one call** → Use dry-run mode first
4. **Execute QR validation** → Run the 5 calls
5. **Review results** → Check `caseyops.db` for outcomes

---

## Alternative: Manual Voice

If you don't want to set up Bland:

```bash
# Use the script as YOUR talking points
cat cropcircuit/caseyops/call_scripts/veterinary_sales.txt

# Pick up the phone and dial manually
# The script is your guide
```

The agent team's recommendation still stands: **Make 5 calls TODAY.**

AI-powered or manual — the goal is real human conversations.
