import os
import subprocess
from pathlib import Path
import markdown
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost

wp_user = os.getenv("WP_USER")
wp_app_password = os.getenv("WP_APP_PASSWORD")

site_url = "https://crop-circuit.com/xmlrpc.php"
client = Client(site_url, wp_user, wp_app_password)

def get_changed_markdown_files():
    try:
        before = os.getenv("GITHUB_EVENT_BEFORE") or os.getenv("GITHUB_SHA") + "^"
        after = os.getenv("GITHUB_SHA") or "HEAD"
        result = subprocess.run(["git", "diff", "--name-only", before, after, "--", "posts/"], stdout=subprocess.PIPE, text=True, check=False)
        files = result.stdout.splitlines()
    except Exception:
        result = subprocess.run(["git", "diff", "--name-only", "HEAD~1", "HEAD", "--", "posts/"], stdout=subprocess.PIPE, text=True, check=False)
        files = result.stdout.splitlines()
    changed = []
    for f in files:
        if f.endswith(".md"):
            changed.append(Path(f))
    return changed

def publish_post(title, html):
    post = WordPressPost()
    post.title = title
    post.content = html
    post.post_status = 'publish'
    return client.call(NewPost(post))

def main():
    changed_files = get_changed_markdown_files()
    if not changed_files:
        print("No new or updated markdown files found.")
        return
    for path in changed_files:
        md_content = path.read_text(encoding="utf-8")
        html = markdown.markdown(md_content)
        title = path.stem
        try:
            post_id = publish_post(title, html)
            print(f"Published '{title}' as post ID {post_id}")
        except Exception as e:
            print(f"Failed to publish '{title}': {e}")
            raise

if __name__ == "__main__":
    main()
