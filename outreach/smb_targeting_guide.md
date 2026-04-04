# SMB Targeting Guide
Finding small businesses with manual workflows and no internal automation

The RemoteOK / WWR data is wrong for this. Those platforms list tech company
engineering jobs. SMB clients are elsewhere.

---

## Best sources, ranked by conversion likelihood

### 1. r/forhire — search for HIRING posts (10 min, free)

Go to: https://reddit.com/r/forhire  
Filter by flair: **[Hiring]**  
Search within results:

```
python
automation
script
excel
spreadsheet
scraping
data entry
"google sheets"
```

What a good lead looks like:
- Small business owner or founder posting directly
- Specific task described ("need someone to automate my invoice emails")
- Budget mentioned ($50–$500)
- No jargon — they don't know Python themselves

Reply directly in the thread. Don't pitch — ask one clarifying question.

---

### 2. r/slavelabour — [Task] posts (5 min, free)

Go to: https://reddit.com/r/slavelabour  
Search: `python` `script` `automation` `excel` `spreadsheet`

Smaller budgets ($20–$100) but fast decisions and easy first reviews.
Good for getting the first 3–5 Fiverr-equivalent reviews to cite elsewhere.

---

### 3. Upwork — browse without posting a profile (15 min)

Go to: https://www.upwork.com/nx/jobs/search/  
Search: `python automation` or `excel automation` or `data cleaning script`  
Filter: **Budget: Fixed price, under $500**

Look for:
- Posted by someone with a company name, not a username
- Job description that shows they don't know what they're doing technically
  ("I need a script that does X, I'm not a programmer")
- Clear deliverable described

You can apply without reviews on Upwork — bid low ($30–50) on first jobs to get
the rating. After 3 ratings you can charge full price.

---

### 4. Facebook Groups (20 min, free, underused)

Search Facebook for:
- "small business owners" + your city or "remote"
- "entrepreneurs" group
- Industry-specific groups: "restaurant owners", "real estate agents",
  "ecommerce sellers", "online store owners"

Look for posts asking for help with:
- "Does anyone know how to..." (Excel, forms, reports)
- "Is there a tool that can..." (often something scriptable)
- "I'm spending hours every week on..." (manual data work)

Reply with a short offer. These convert better than cold email because
there's existing trust in the group.

---

### 5. Craigslist computer gigs — run locally (30 min setup)

The script `outreach/scrape_craigslist_gigs.py` can't run from the Claude
Code container (outbound requests are blocked) but works on `intuitionmachine1`:

```bash
cd /path/to/repo
pip install requests beautifulsoup4
python3 outreach/scrape_craigslist_gigs.py
# Output: outreach/craigslist_leads.csv
```

Note: Craigslist uses JavaScript rendering on their main search page. The
script handles both the newer and older markup. If 0 results come back,
try with Playwright:

```bash
pip install playwright
playwright install chromium
```
Then update the script to use `playwright` instead of `requests` — or just
browse https://[city].craigslist.org/search/cpg manually and copy interesting
titles into the CSV.

---

## Identifying a good prospect

Ask yourself:
- Do they have an in-house developer? (If yes, skip — they'll do it themselves)
- Is the task repetitive and clearly defined? (Good signal)
- Is the budget $50–$500? (Right range — too low = not worth it, too high = they'll hire FT)
- Are they non-technical? (They describe the problem in plain English, not code)

Red flags:
- "Must sign NDA before discussing" on a $30 job
- Vague scope ("I need a general automation system")
- "Equity only" or "we'll pay you after launch"
- Company has a careers page with 5+ engineering roles open

---

## What to say (reply template for Reddit / Upwork)

```
Hi — I can do this.

I've built similar tools: [one specific example from your portfolio].

For your job, I'd [one sentence on approach]. Delivery in [X] days.

Quick question before I quote: [one clarifying question about scope].
```

Short. Specific. Don't oversell. Ask a question to start a conversation.

---

## Tracking

When you find a lead, add it to `outreach/craigslist_leads.csv` manually
(or create a new `outreach/reddit_leads.csv` with the same columns):

```
title, city/source, score, link, date, contact_attempted, notes
```

Mark `contact_attempted` with the date you replied. Follow up once after
3 business days if no response.
