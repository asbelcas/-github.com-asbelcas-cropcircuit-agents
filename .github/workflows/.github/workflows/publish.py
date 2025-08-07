import os
import csv
import random
import requests
from datetime import datetime
import openai
import html

# --- Config ---
OPENAI_API_KEY        = os.environ["OPENAI_API_KEY"]
SITE_BRAND            = os.environ.get("SITE_BRAND", "Crop Circuit")
WP_SITE               = os.environ["WP_SITE"]
WP_COM_CLIENT_ID      = os.environ["WP_COM_CLIENT_ID"]
WP_COM_CLIENT_SECRET  = os.environ["WP_COM_CLIENT_SECRET"]
WP_COM_REFRESH_TOKEN  = os.environ["WP_COM_REFRESH_TOKEN"]
POSTS_PER_RUN         = int(os.environ.get("POSTS_PER_RUN", "1"))

# --- Affiliate Links ---
AMAZON_TAG = "youramazontag-20"   # TODO: replace with your real tag
TRACTOR_SUPPLY_URL = "https://www.tractorsupply.com/"

openai.api_key = OPENAI_API_KEY

def hero_image_html(keyword: str) -> str:
    """
    Uses Unsplash Source (no API key needed) to fetch a topical hero image.
    Attribution: Unsplash license allows commercial use w/ credit appreciated.
    """
    q = keyword.replace(" ", "+")
    url = f"https://source.unsplash.com/960x640/?{q},farm,agriculture"
    alt = html.escape(f"{keyword} - {SITE_BRAND}")
    caption = f'Photo via <a href="https://unsplash.com" rel="nofollow noopener" target="_blank">Unsplash</a>'
    return f'''
<figure class="wp-block-image">
  <img src="{url}" alt="{alt}" loading="lazy" decoding="async" />
  <figcaption>{caption}</figcaption>
</figure>
'''

def build_summary_box(keyword: str) -> str:
    """
    Lightweight HTML summary panel for affiliate posts.
    """
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
    """
    Generates content. For 'best ...' keywords, produces affiliate-style review
    content with pros/cons, comparison table, buying guide, and CTA.
    """
    if keyword.lower().startswith("best "):
        prompt = f"""
Write a ~1000-word affiliate-style review article for: "{keyword}".
Requirements:
- Opening hook: call out the real farm need/problem this solves.
- Insert a short "Summary Box" with 3 picks (Best Overall, Best Budget, Best Premium).
- H2: "Top Picks for {keyword.title()}"
- For each of 3 products:
  - H3 with a placeholder product name (you invent a realistic but generic placeholder)
  - 2–3 sentence overview
  - Bullet list: Key features (4–6 bullets)
  - Bullet list: Pros and Cons
  - Two links (leave as provided text; do not change the URLs or tags):
    👉 [Check Price on Amazon] ( https://www.amazon.com/s?k={keyword.replace(' ', '+')}&tag={AMAZON_TAG} )
    👉 [Check Price on Tractor Supply] ( {TRACTOR_SUPPLY_URL} )
- Add a markdown comparison table with columns:
  Product | Key Feature | Price Range | Our Rating
- H2 "Buying Guide": what to look for, pitfalls, sizing/capacity tips.
- H2 "Final Thoughts" with a soft urgency CTA linking to /get-quotes.
- Tone: friendly, expert, scannable; short paragraphs and bullets.
- DO NOT overuse the exact keyword; keep it natural and helpful.
Return only the article body (no YAML, no extra metadata).
"""
    else:
        prompt = f"""
Write a concise, high-quality blog post (350–500 words) for {SITE_BRAND} about: "{keyword}".
Requirements:
- Clear H2 subheads
- Short paragraphs and bullet lists
- Practical steps or checklist
- Internal CTA at the end linking to /get-quotes with anchor text "Get quotes"
- Neutral, trustworthy tone; avoid repeating the keyword excessively
- Add a one-sentence meta description at the top prefixed with 'META: '
Return only the post content.
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
