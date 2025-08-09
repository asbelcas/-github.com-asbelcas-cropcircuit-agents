import os, subprocess, sys, time
from pathlib import Path

try:
    import requests
    import markdown
except Exception as e:
    print("Dependency import failed:", e)
    sys.exit(1)

WP_USER = os.getenv("WP_USER")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
SITE_SLUG = os.getenv("SITE_SLUG", "crop-circuit.com").strip()
BEFORE = os.getenv("BEFORE")
AFTER = os.getenv("AFTER")

API_URL = f"https://public-api.wordpress.com/wp/v2/sites/{SITE_SLUG}/posts"

def changed_markdown_files():
    posts_dir = Path("posts")
    if not posts_dir.exists():
        return []

    changed = []
    if BEFORE and AFTER:
        try:
            res = subprocess.run(
                ["git", "diff", "--name-only", BEFORE, AFTER, "--", "posts/"],
                text=True, capture_output=True, check=False
            )
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    p = Path(line.strip())
                    if p.suffix.lower() == ".md" and p.exists():
                        changed.append(p)
        except Exception as e:
            print("git diff failed:", e)

    if not changed:
        changed = sorted(posts_dir.glob("*.md"))
    return changed

def md_to_html(md_path: Path) -> str:
    text = md_path.read_text(encoding="utf-8")
    return markdown.markdown(text)

def publish_post(title: str, html: str) -> str:
    auth = (WP_USER, WP_APP_PASSWORD)
    payload = {"title": title, "content": html, "status": "publish"}
    r = requests.post(API_URL, auth=auth, json=payload, timeout=60)
    if r.status_code != 201:
        raise RuntimeError(f"Publish failed {r.status_code}: {r.text[:500]}")
    return r.json().get("link", "")

def main():
    if not WP_USER or not WP_APP_PASSWORD:
        print("Missing WP_USER or WP_APP_PASSWORD secrets.")
        sys.exit(1)

    files = changed_markdown_files()
    if not files:
        print("No posts/*.md to publish.")
        return

    print(f"Using site slug: {SITE_SLUG}")
    print("Files to publish:")
    for p in files:
        print(" -", p)

    for p in files:
        title = p.stem
        html = md_to_html(p)
        print(f"Publishing '{title}' ...")
        link = publish_post(title, html)
        print(f"  -> OK: {link}")
        time.sleep(0.5)

if __name__ == "__main__":
    main()
