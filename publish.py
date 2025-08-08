import os
import csv
import random
import requests
from datetime import datetime
import openai
import html

# Config
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
SITE_BRAND = os.environ.get("SITE_BRAND", "Crop Circuit")
WP_SITE = os.environ["WP_SITE"]
WP_COM_CLIENT_ID = os.environ["WP_COM_CLIENT_ID"]
WP_COM_CLIENT_SECRET = os.environ["WP_COM_CLIENT_SECRET"]
WP_COM_REFRESH_TOKEN = os.environ["WP_COM_REFRESH_TOKEN"]
POSTS_PER_RUN = int(os.environ.get("POSTS_PER_RUN", "1"))

# Affiliate Links
AMAZON_TAG = "youramazontag-20"  # TODO: replace with your real tag
TRACTOR_SUPPLY_URL = "https://www.tractorsupply.com/"

openai.api_key = OPENAI_API_KEY

def hero_image_html(keyword: str) -> str:
    q = keyword.replace(" ", "+")
    url = f"https://source.unsplash.com/960x640/?{q},farm,agriculture"
    alt = html.escape(f"{keyword} - {SITE_BRAND}")
    caption = (
        'Photo via <a href="https://unsplash.com" rel="nofollow noopener" target="_blank">Unsplash</a>'
    )
    return f'''<figure class="wp-block-image">
  <img src="{url}" alt="{alt}" loading="lazy" decoding="async" />
  <figcaption>{caption}</figcaption>
</figure>'''

def build_summary_box(keyword: str) -> str:
    safe_kw = html.escape(keyword.title())
    return f"""
<div style="border:1px solid #e2e8f0;border-radius:12px;padding:16px;background:#f8fafc;margin:16px 0;">
  <strong>Quick Picks — {safe_kw}</strong>
  <ul style="margin:8px 0 0 18px;">
    <li><strong>Best Overall:</strong> {{PRODUCT_1}} — balanced performance and value</li>
    <li><strong>Best Budget:</strong> {{PRODUCT_2}} — reliable and affordable for small farms</li>
    <li><strong>Best Premium:</strong> {{PRODUCT_3}} — top-tier features for heavy use</li>
  </ul>
  <div style="margin-top:8px;font-size:0.9em;color:#475569;">
    Prices change often. Always check current pricing:
    <a href="https://www.amazon.com/s?k={safe_kw.replace(' ', '+')}&tag={AMAZON_TAG}" rel="sponsored nofollow noopener" target="_blank">Amazon</a> ·
    <a href="{TRACTOR_SUPPLY_URL}" rel="sponsored nofollow noopener" target="_blank">Tractor Supply</a>
  </div>
</div>
"""

def gen_post(keyword: str) -> str:
    if keyword.lower().startswith("best "):
        prompt = (
            f"Write a 1000-word affiliate-style product review article for: \"{keyword}\".\n"
            f"Requirements:\n"
            "- Start with a short introduction about why this item is important for farmers.\n"
            f"- Include an H2 \"Top Picks for {keyword.title()}\"\n"
            "- For each of the top 3 products:\n"
            "  * Use an H3 with the product name (placeholder)\n"
            "  * Provide a short description\n"
            "  * List key features in bullet points\n"
            "  * Add Pros and Cons bullet lists\n"
            f"  * Include a placeholder line: \"\ud83d\udc49 [Check Price on Amazon](https://www.amazon.com/s?k={keyword.replace(' ', '+')}&tag={AMAZON_TAG})  \ud83d\udc49 [Check Price on Tractor Supply]({TRACTOR_SUPPLY_URL})\"\n"
            "- Add a markdown comparison table with columns: Product | Key Feature | Price Range | Our Rating\n"
            "- Add an H2 \"Buying Guide\" explaining what to look for when choosing this type of product.\n"
            "- Add an H2 \"Final Thoughts\" with a call-to-action linking to /get-quotes\n"
            "- Write in a friendly, expert tone for small farm owners.\n"
            "- No fluff; make it highly useful and scannable."
        )
    else:
        prompt = (
            f"Write a concise, high-quality blog post (350–500 words) for {SITE_BRAND} about: \"{keyword}\".\n"
            "Requirements:\n"
            "- Clear H2 subheads\n"
            "- Short paragraphs and bullet lists\n"
            "- Practical steps or checklist\n"
            "- Internal CTA at the end linking to /get-quotes with anchor text \"Get quotes\"\n"
            "- Neutral, trustworthy tone; no fluff; avoid repeating the keyword excessively\n"
            "- Add a one-sentence meta description at the top prefixed with 'META: '"
        )
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
    )
    return response.choices[0].message["content"].strip()

def refresh_access_token() -> str:
    token_url = "https://public-api.wordpress.com/oauth2/token"
    r = requests.post(
        token_url,
        data={
            "client_id": WP_COM_CLIENT_ID,
            "client_secret": WP_COM_CLIENT_SECRET,
            "refresh_token": WP_COM_REFRESH_TOKEN,
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
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

def load_keywords(csv_path: str = "keywords.csv"):
    keywords = []
    weights = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or not row[0].strip():
                continue
            kw = row[0].strip()
            wt = 1.0
            if len(row) > 1:
                try:
                    wt = float(row[1])
                except:
                    wt = 1.0
            keywords.append(kw)
            weights.append(wt)
    return keywords, weights

def choose_keywords(keywords, weights, k):
    chosen = []
    pool = list(zip(keywords, weights))
    k = min(k, len(pool))
    for _ in range(k):
        total = sum(w for _, w in pool)
        r = random.uniform(0, total) if total > 0 else random.random()
        acc = 0.0
        for i, (_, w) in enumerate(pool):
            acc += w
            if r <= acc:
                chosen.append(pool[i][0])
                pool.pop(i)
                break
    return chosen

def inject_hero_and_summary(keyword: str, body: str, is_best: bool) -> str:
    lines = body.splitlines()
    meta = ""
    if lines and lines[0].strip().lower().startswith("meta:"):
        meta = lines[0]
        body = "\n".join(lines[1:]).strip()
    pieces = []
    if meta:
        pieces.append(meta)
    pieces.append(hero_image_html(keyword))
    if is_best:
        pieces.append(build_summary_box(keyword))
    pieces.append(body)
    if is_best:
        pieces.append(
            '\n<div style="font-size:0.9em;color:#475569;margin-top:16px;">'
            'Disclosure: Some links in this article are affiliate links. If you click and buy, '
            f'{html.escape(SITE_BRAND)} may earn a small commission at no extra cost to you. '
            'We only recommend products we’d use on our own farm.</div>'
        )
    pieces.append(
        f'\n---\n<strong>Need help?</strong> <a href="/get-quotes">Get quotes</a> from {html.escape(SITE_BRAND)}.'
    )
    return "\n\n".join(pieces)

def main():
    keywords, weights = load_keywords()
    picks = choose_keywords(keywords, weights, POSTS_PER_RUN)
    for kw in picks:
        today = datetime.now().strftime("%B %d, %Y")
        title = f"{kw.title()} — {today}"
        raw = gen_post(kw)
        is_best = kw.lower().startswith("best ")
        content = inject_hero_and_summary(kw, raw, is_best)
        result = publish_post(title, content)
        print(f"Published: {title} -> {result.get('URL', '(no URL)')}")

if __name__ == "__main__":
    main()
