import os, subprocess, sys, time
from pathlib import Path

import requests
import markdown

WP_USER = os.getenv("WP_USER")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
SITE_SLUG = (os.getenv("SITE_SLUG") or "crop-circuit.com").strip()
BEFORE = os.getenv("BEFORE")
AFTER = os.getenv("AFTER")

API_URL = f"https://public-api.wordpress.com/wp/v2/sites/{SITE_SLUG}/posts"

def changed_markdown_files():
    posts = Path("posts")
    if not posts.exists():
        return []
    files = []
    if BEFORE and AFTER:
        res = subprocess.run([
            "git",
            "diff",
            "--name-only",
            BEFORE,
            AFTER,
            "--",
            "posts/",
        ], text=True, capture_output=True)
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                p = Path(line.strip())
                if p.suffix.lower() == ".md" and p.exists():
                    files.append(p)
    if not files:
        files = sorted(posts.glob("*.md"))
    return files

def md_to_html(p: Path) -> str:
    return markdown.markdown(p.read_text(encoding="utf-8"))

def publish(title: str, html: str) -> str:
    r = requests.post(
        API_URL,
        auth=(WP_USER, WP_APP_PASSWORD),
        json={"title": title, "content": html, "status": "publish"},
        timeout=60,
    )
    if r.status_code != 201:
        raise RuntimeError(f"Publish failed {r.status_code}: {r.text[:500]}")
    return r.json().get("link", "")

def main():
    if not WP_USER or not WP_APP_PASSWORD:
        print("Missing WP_USER or WP_APP_PASSWORD.")
        sys.exit(1)
    files = changed_markdown_files()
    if not files:
        print("No posts/*.md to publish.")
        return
    print(f"Site: {SITE_SLUG}")
    for p in files:
        title = p.stem
        html = md_to_html(p)
        print(f"Publishing {p} -> '{title}'")
        link = publish(title, html)
        print(f"  OK: {link}")
        time.sleep(0.5)

if __name__ == "__main__":
    main()
