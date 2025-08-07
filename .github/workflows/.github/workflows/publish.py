import os
import csv
import random
import requests
from datetime import datetime
import openai

# --- Config ---
OPENAI_API_KEY        = os.environ["OPENAI_API_KEY"]
SITE_BRAND            = os.environ.get("SITE_BRAND", "Crop Circuit")
WP_SITE               = os.environ["WP_SITE"]
WP_COM_CLIENT_ID      = os.environ["WP_COM_CLIENT_ID"]
WP_COM_CLIENT_SECRET  = os.environ["WP_COM_CLIENT_SECRET"]
WP_COM_REFRESH_TOKEN  = os.environ["WP_COM_REFRESH_TOKEN"]
POSTS_PER_RUN         = int(os.environ.get("POSTS_PER_RUN", "1"))

# --- Affiliate Links ---
AMAZON_TAG = "youramazontag-20"   # replace with your Amazon Associates tag
TRACTOR_SUPPLY_URL = "https://www.tractorsupply.com/"  # can add affiliate params later

openai.api_key = OPENAI_API_KEY

def gen_post(keyword: str) -> str:
    """Generates a post with affiliate structure if keyword starts with 'best'."""
    if keyword.lower().startswith("best "):
        prompt = f"""
Write a 1000-word affiliate-style product review article for: "{keyword}".
Requirements:
- Hook readers in first 2 sentences by identifying their need/problem.
- Include an H2 "Top Picks for {keyword.title()}"
- For each of the top 3 products:
  * H3 with product name (placeholder)
  * Short engaging description
  * Key features in bullet points
  * Pros and Cons bullet lists
  * Add this line after pros/cons:
    👉 [Check Price on Amazon](https://www.amazon.com/s?k={keyword.replace(' ', '+')}&tag={AMAZON_TAG})  
    👉 [Check Price on Tractor Supply]({TRACTOR_SUPPLY_URL})
- Add a markdown comparison table: Product | Key Feature | Price Range | Our Rating
- H2 "Buying Guide" explaining what to look for in this type of product.
- H2 "Final Thoughts" with urgency + call-to-action linking to /get-quotes.
- Friendly, expert tone for small farm owners.
- No fluff; make it highly useful and scannable.
"""
    else:
        prompt = f"""
Write a concise, high-quality blog post (350–500 words) for {SITE_BRAND} about: "{keyword}".
Requirements:
- Clear H2 subheads
- Short paragraphs and bullet lists
- Practical steps or checklist
- Internal CTA at the end linking to /get-quotes with anchor text "Get quotes"
- Neutral, trustworthy tone; no fluff; avoid repeating the keyword excessively
- Add a one-sentence meta description at the top prefixed with 'META: '
"""

    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        temperature=0.6
    )
    return resp.choices[0].message["content"].strip()

def refresh_access_token() -> str:
    token_url = "https://public-api.wordpress.com/oauth2/token"
    r = requests.post(token_url, data={
        "client_id": WP_COM_CLIENT_ID,
        "client_secret": WP_COM_CLIENT_SECRET,
        "refresh_token": WP_COM_REFRESH_TOKEN,
        "grant_type": "refresh_token",
    }, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]

def publish_post(title: str, content: str) -> dict:
    access_token = refresh_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    post_url = f"https://public-api.wordpress.com/rest/v1.1/sites/{WP_SITE}/posts/new"
    data = {"title": title, "content": content, "status": "publish"}
    r = requests.post(post_url, headers=headers, data=data, timeout=60)
    r.raise_for_status()
    return r.json()

def load_keywords(csv_path="keywords.csv"):
    keywords, weights = [], []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or not row[0].strip():
                continue
            kw = row[0].strip()
            wt = float(row[1]) if len(row) > 1 else 1.0
            keywords.append(kw)
            weights.append(wt)
    return keywords, weights

def choose_keywords(keywords, weights, k):
    chosen = []
    pool = list(zip(keywords, weights))
    for _ in range(min(k, len(pool))):
        total = sum(w for _, w in pool)
        r = random.uniform(0, total)
        acc = 0.0
        for i, (_, w) in enumerate(pool):
            acc += w
            if r <= acc:
                chosen.append(pool[i][0])
                pool.pop(i)
                break
    return chosen

def main():
    keywords, weights = load_keywords()
    picks = choose_keywords(keywords, weights, POSTS_PER_RUN)

    for kw in picks:
        today = datetime.now().strftime("%B %d, %Y")
        title = f"{kw.title()} — {today}"
        content = gen_post(kw)

        # Handle meta description if present
        lines = content.splitlines()
        if lines and lines[0].strip().lower().startswith("meta:"):
            content = "\n".join(lines[1:]).strip()

        # Append a final CTA
        content += f"\n\n---\n**Need help?** <a href=\"/get-quotes\">Get quotes</a> from {SITE_BRAND}."

        result = publish_post(title, content)
        print(f"Published: {title} -> {result.get('URL', '(no URL)')}")

if __name__ == "__main__":
    main()
