import os
import subprocess
import requests
import markdown

# Retrieve credentials from environment variables
wp_user = os.getenv("WP_USER")
wp_app_password = os.getenv("WP_APP_PASSWORD")

# Specify the WordPress.com site slug (without protocol)
site_slug = "cropcircuit.wordpress.com"
# Build the API endpoint URL for creating posts
site_url = "https://public-api.wordpress.com/wp/v2/sites/" + site_slug + "/posts"

def get_changed_markdown_files():
    """
    Return a list of markdown files in the posts directory that are new or have been modified
    in the most recent commit.
    """
    changed_files = []
    try:
        # Use git diff to find files changed in the last commit within the posts directory
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD", "--", "posts"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        for line in result.stdout.splitlines():
            file_path = line.strip()
            if file_path.lower().endswith(".md"):
                changed_files.append(file_path)
    except Exception:
        pass
    # If no files were detected (e.g., git diff failed), fall back to publishing all markdown files
    if not changed_files:
        for root, _, files in os.walk("posts"):
            for filename in files:
                if filename.lower().endswith(".md"):
                    changed_files.append(os.path.join(root, filename))
    return changed_files

def publish_markdown_file(file_path):
    """
    Convert a Markdown file to HTML and publish it to WordPress.
    """
    # Read the markdown content
    with open(file_path, "r", encoding="utf-8") as f:
        markdown_content = f.read()
    # Use the filename (without extension) as the post title
    title = os.path.splitext(os.path.basename(file_path))[0]
    # Convert markdown content to HTML
    html_content = markdown.markdown(markdown_content)
    # Submit the post via WordPress REST API
    response = requests.post(
        site_url,
        auth=(wp_user, wp_app_password),
        json={
            "title": title,
            "content": html_content,
            "status": "publish",
        },
    )
    if response.status_code == 201:
        print(f"\u2705 Published '{title}' successfully.")
    else:
        print(f"\u274c Failed to publish '{title}': {response.status_code} - {response.text}")

def main():
    # Get list of changed markdown files
    files_to_publish = get_changed_markdown_files()
    if not files_to_publish:
        print("No new or updated markdown files to publish.")
        return
    # Publish each file
    for path in files_to_publish:
        publish_markdown_file(path)

if __name__ == "__main__":
    main()
