import os, subprocess, time, sys
from pathlib import Path

try:
    import markdown
except Exception as e:
    print("Failed to import markdown:", e); sys.exit(1)

WP_USER = os.getenv("WP_USER")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
SITE_SLUG = os.getenv("SITE_SLUG", "crop-circuit.wordpress.com")
BEFORE = os.getenv("BEFORE")
AFTER = os.getenv("AFTER")
API = f"https://public-api.wordpress.com/wp/v2/sites/{SITE_SLUG}/posts"

def list_changed_md():
    posts_dir = Path("posts")
    if not posts_dir.exists():
        return []
    changed = []
    if BEFORE and AFTER:
        try:
            res = subprocess.run(
                ["git", "diff", "--name-only", BEFORE, AFTER, "--", "posts/"],
                capture_output=True, text=True, check=False
            )
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    p = Path(line.strip())
                    if p.suffix.lower() == ".md" and p.exists():
                        changed.append(p)
        except Exception as e:
            print("git diff failed:", e)
    if not changed:
        changed = sorted(Path("posts").glob("*.md"))
    return changed

def md_to_html(p: Path) -> str:
    text = p.read_text(encoding="utf-8")
    return markdown.markdown(text)

def post_wp(title: str, html: str):
    import requests
    resp = requests.post(
        API, auth=(WP_USER, WP_APP_PASSWORD),
        json={"title": title, "content": html, "status": "publish"},
        timeout=60
    )
    if resp.status_code != 201:
        raise RuntimeError(f"WP POST failed {resp.status_code}: {resp.text}")
    return resp.json()

def main():
    if not (WP_USER and WP_APP_PASSWORD):
        print("Missing WP_USER or WP_APP_PASSWORD."); sys.exit(1)
    files = list_changed_md()
    if not files:
        print("No posts/*.md to publish."); return
    print("Publishing:")
    for p in files:
        print(" -", p)
        data = post_wp(p.stem, md_to_html(p))
        print("   -> OK:", data.get('link'))
        time.sleep(0.6)

if __name__ == "__main__":
    main()
