import os
import requests
from datetime import datetime

wp_user = os.getenv("WP_USER")
wp_app_password = os.getenv("WP_APP_PASSWORD")

site_slug = "cropcircuit.wordpress.com"
site_url = "https://public-api.wordpress.com/wp/v2/sites/" + site_slug + "/posts"

post_title = f"GitHub Actions Test Post - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
post_content = "✅ This is a test post published automatically from GitHub Actions."

response = requests.post(
    site_url,
    auth=(wp_user, wp_app_password),
    json={
        "title": post_title,
        "content": post_content,
        "status": "publish"
    }
)

if response.status_code == 201:
    print("✅ Post published successfully!")
else:
    print(f"❌ Failed to publish post: {response.status_code} - {response.text}")
    exit(1)
