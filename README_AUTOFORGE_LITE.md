# 🤖 AUTOFORGE-LITE: Autonomous Freelancer System

**Zero-Hallucination, Human-Checkpointed Automation for Upwork/Fiverr**

---

## ⚡ QUICK START (30 seconds)

```bash
cd /home/asbelcas/rm-qpt
./autoforge_dashboard.sh           # View system status
./autoforge_checkpoint.sh          # Approve pending submissions
```

---

## 📋 WHAT IS AUTOFORGE-LITE?

AUTOFORGE-LITE is a **safety-first** autonomous system that finds freelance jobs and prepares proposals, but **requires human approval before every submission**. Unlike the original system that hallucinated successful submissions, this version:

- ✅ Never submits without explicit approval
- ✅ Creates checkpoints for human review
- ✅ Runs comprehensive pre-flight checks
- ✅ Uses failure-resistant browser automation
- ✅ Logs everything for transparency

---

## 🛡️ SAFETY ARCHITECTURE

### Three Layers of Protection

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 1: Pre-Flight System Checks                      │
│  - Verify Chrome, Selenium, network, disk space         │
│  - Stop immediately if any critical check fails         │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 2: Human Checkpoints                             │
│  - System drafts proposals, PAUSES                      │
│  - You review and approve each submission               │
│  - No automation runs without explicit approval         │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 3: Browser Safety Controls                       │
│  - Detection evasion (stealth mode)                     │
│  - Automatic CAPTCHA/2FA detection                      │
│  - Screenshots on failure                               │
│  - Session timeout protection                           │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 EXECUTION MODES

### Mode 1: Browser Automation (With Checkpoints) ⭐ RECOMMENDED

Uses real browser automation but stops for human approval at every critical step.

```bash
# Stage jobs (creates checkpoints)
python3 AUTOFORGE_EXECUTOR.py

# Review checkpoints
./autoforge_checkpoint.sh

# Approve a submission
./autoforge_checkpoint.sh approve cp_job_001_1775235317

# System will then open browser for final review
```

### Mode 2: Hybrid (Safest)

System drafts proposals, opens browser to job page, you copy/paste manually.

```bash
python3 AUTOFORGE_HYBRID.py
```

### Mode 3: Manual (Full Control)

System finds jobs, you do everything else.

```bash
# Just view opportunities
./autoforge_dashboard.sh
```

---

## 📁 FILE REFERENCE

| File | Purpose |
|------|---------|
| `AUTOFORGE_EXECUTOR.py` | Main execution system with checkpoints |
| `AUTOFORGE_BROWSER_V2.py` | Failure-resistant browser automation |
| `AUTOFORGE_HYBRID.py` | Safe hybrid mode |
| `autoforge_checkpoint.sh` | Approve/reject pending submissions |
| `autoforge_dashboard.sh` | View system status |
| `checkpoints/` | Pending approval packages |
| `logs/` | Execution logs |

---

## 🔄 WORKFLOW

```
1. RUN PREFLIGHT CHECKS
   └── Verify system is ready

2. FIND OPPORTUNITIES
   └── System finds relevant jobs

3. CREATE CHECKPOINTS
   └── Draft proposals + PAUSE

4. HUMAN REVIEW
   └── You review each checkpoint

5. APPROVE/REJECT
   └── Approve: System continues
   └── Reject: Skip that job

6. BROWSER AUTOMATION
   └── System opens browser
   └── You verify everything looks correct
   └── System submits (or you do manually)
```

---

## 🎯 EXAMPLE SESSION

```bash
# Terminal 1: Run the executor
cd /home/asbelcas/rm-qpt
python3 AUTOFORGE_EXECUTOR.py
# → Runs pre-flight checks
# → Creates checkpoints for 2 jobs
# → Pauses for approval

# Terminal 2: Review checkpoints
./autoforge_checkpoint.sh
# Shows:
#   - Session status
#   - Pending checkpoints
#   - Proposal previews

# Approve a submission
./autoforge_checkpoint.sh approve cp_job_001_1775235317

# System then:
#   - Opens browser
#   - Navigates to job page
#   - Fills proposal form
#   - Stops for final review
#   - You click submit manually (or give final approval)
```

---

## ⚠️ IMPORTANT DISCLAIMERS

### What This System DOES:
- ✅ Finds relevant job opportunities
- ✅ Drafts proposal text based on your templates
- ✅ Creates approval checkpoints
- ✅ Opens browser for your review
- ✅ Logs everything transparently

### What This System DOES NOT Do:
- ❌ Submit proposals without approval
- ❌ Guarantee job acceptance
- ❌ Bypass platform security (CAPTCHA, 2FA)
- ❌ Guarantee account won't be flagged

### Platform Risks:
- Upwork and Fiverr prohibit automation
- Using this may result in account suspension
- The checkpoint system provides human oversight but doesn't eliminate risk
- **Use at your own risk**

---

## 🔧 TROUBLESHOOTING

### Pre-flight fails:
```bash
# Install missing dependencies
pip install selenium webdriver-manager

# Install Chrome
sudo apt-get install google-chrome-stable
```

### Browser doesn't open:
```bash
# Check display
echo $DISPLAY

# Try headless mode (edit AUTOFORGE_BROWSER_V2.py)
# Change headless=False to headless=True
```

### Checkpoints not showing:
```bash
# Check checkpoint directory
ls -la /home/asbelcas/rm-qpt/checkpoints/

# Check for .json files
grep -l "PENDING" /home/asbelcas/rm-qpt/checkpoints/*.json
```

---

## 📊 MONITORING

```bash
# View all logs
tail -f /home/asbelcas/rm-qpt/logs/executor_*.log

# View current state
cat /home/asbelcas/rm-qpt/executor_state.json

# View checkpoint responses
cat /home/asbelcas/rm-qpt/checkpoint_responses.txt
```

---

## 🤝 HUMAN-IN-THE-LOOP DESIGN

AUTOFORGE-LITE is designed for **collaborative automation** - the system does the tedious work (finding jobs, drafting proposals) while you retain full control over what actually gets submitted.

This architecture:
- Prevents hallucinations (no false claims of success)
- Protects your accounts (no unapproved submissions)
- Allows quality control (you review everything)
- Maintains transparency (full logging)

---

**Built with safety first. Automation second.**
