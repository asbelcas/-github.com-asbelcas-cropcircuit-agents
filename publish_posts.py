import os
import subprocess
import sys
import time
from pathlib import Path

try:
    import markdown
    import requests
except Exception as e:
    print('Failed to import dependencies', e)
    sys.exit(1)

WP_USER = os.getenv('WP_USER')
WP_APP_PASSWORD = os.getenv('WP_APP_PASSWORD')
SITE_SLUG = os.getenv('SITE_SLUG', 'crop-circuit.com').strip()
WP_XMLRPC = os.getenv('WP_XMLRPC', f'https://{SITE_SLUG}/xmlrpc.php')
BEFORE = os.getenv('BEFORE')
AFTER = os.getenv('AFTER')

REST_API = f'https://public-api.wordpress.com/wp/v2/sites/{SITE_SLUG}/posts'

def list_changed_markdown():
    posts_dir = Path('posts')
    if not posts_dir.is_dir():
        return []
    changed = []
    if BEFORE and AFTER:
        try:
            result = subprocess.run(['git', 'diff', '--name-only', BEFORE, AFTER, '--', 'posts/'], text=True, capture_output=True, check=False)
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    p = Path(line.strip())
                    if p.suffix.lower() == '.md' and p.exists():
                        changed.append(p)
        except Exception as e:
            print('git diff failed', e)
    if not changed:
        changed = sorted(posts_dir.glob('*.md'))
    return changed

def md_to_html(path):
    try:
        text = path.read_text(encoding='utf-8')
    except Exception:
        text = ''
    return markdown.markdown(text)

def publish_rest(title, html):
    payload = {'title': title, 'content': html, 'status': 'publish'}
    try:
        r = requests.post(REST_API, auth=(WP_USER, WP_APP_PASSWORD), json=payload, timeout=60)
        return r.status_code, r
    except Exception as e:
        return None, e

def publish_xmlrpc(title, html):
    try:
        from wordpress_xmlrpc import Client, WordPressPost
        from wordpress_xmlrpc.methods.posts import NewPost
    except Exception:
        print('xmlrpc library not available')
        raise
    client = Client(WP_XMLRPC, WP_USER, WP_APP_PASSWORD)
    post = WordPressPost()
    post.title = title
    post.content = html
    post.post_status = 'publish'
    return client.call(NewPost(post))

def main():
    if not WP_USER or not WP_APP_PASSWORD:
        print('Missing WordPress credentials')
        sys.exit(1)
    posts = list_changed_markdown()
    if not posts:
        print('No markdown posts to publish')
        return
    print(f'Using site slug: {SITE_SLUG}')
    for p in posts:
        title = p.stem
        html = md_to_html(p)
        print(f'Publishing {title}')
        status, resp = publish_rest(title, html)
        success = False
        if status == 201:
            try:
                link = resp.json().get('link', '')
            except Exception:
                link = ''
            print(f'Success via REST: {link}')
            success = True
        else:
            if status:
                try:
                    text = resp.text
                except Exception:
                    text = str(resp)
                print(f'REST failed ({status}) - {text[:200]}')
            else:
                print(f'REST request error: {resp}')
            try:
                post_id = publish_xmlrpc(title, html)
                print(f'Success via XMLRPC: post id {post_id}')
                success = True
            except Exception as e:
                print(f'XMLRPC failed: {e}')
        if not success:
            print(f'Failed to publish {title}')
        time.sleep(0.5)

if __name__ == '__main__':
    main()
