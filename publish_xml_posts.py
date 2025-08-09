import os
import subprocess
from pathlib import Path
import time
import sys

try:
    import markdown
except Exception as e:
    print(f"Failed to import markdown: {e}")
    sys.exit(1)

try:
    from wordpress_xmlrpc import Client, WordPressPost
    from wordpress_xmlrpc.methods.posts import NewPost
except Exception as e:
    print(f"Failed to import python-wordpress-xmlrpc: {e}")
    sys.exit(1)

WP_USER = os.getenv("WP_USER")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
SITE_URL = os.getenv("SITE_URL", "https://crop-circuit.com/xmlrpc.php")
BEFORE = os.getenv("BEFORE")
AFTER = os.getenv("AFTER")

def list_changed_md():
    posts_dir = Path("posts")
    if not posts_dir.exists():
        return []
    changed = []
    if BEFORE and AFTER:
        try:
            res = subprocess.run(
                ["git", "diff", "--name-only", BEFORE, AFTER, "--", "posts/"],
                capture_output=True,
                text=True,
                check=False,
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

def md_to_html(path):
    text = path.read_text(encoding="utf-8")
    return markdown.markdown(text)

def publish_post(title, html, client):
    post = WordPressPost()
    post.title = title
    post.content = html
    post.post_status = "publish"
    return client.call(NewPost(post))

def main():
    if not (WP_USER and WP_APP_PASSWORD):
        print("Missing WP_USER or WP_APP_PASSWORD.")
        sys.exit(1)

    try:
        client = Client(SITE_URL, WP_USER, WP_APP_PASSWORD)
    except Exception as e:
        print(f"Failed to connect to WordPress XML-RPC: {e}")
        sys.exit(1)

    files = list_changed_md()
    if not files:
        print("No posts/*.md to publish.")
        return

    for p in files:
        title = p.stem
        html = md_to_html(p)
        print(f"Publishing: {title}")
        try:
            response = publish_post(title, html, client)
            print(f"  -> OK: Published post ID {response}")
        except Exception as e:
            print(f"Failed to publish {title}: {e}")
        time.sleep(0.6)

if __name__ == "__main__":
    main()
