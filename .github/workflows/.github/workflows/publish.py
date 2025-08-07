Nice — publish.yml is in place. ✅

Now we just need to add the three Python files that the workflow will run.


---

📄 Step 3 – Add publish.py

1. In your repo’s main folder (not inside .github), click Add file → Create new file.


2. Name it:

publish.py


3. Paste this in:



import os
import requests
import json
import openai

openai.api_key = os.environ["OPENAI_API_KEY"]

def create_post():
    prompt = f"Write a 300-word blog post for {os.environ['SITE_BRAND']}."
    completion = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message["content"]

def publish_to_wp(title, content):
    site = os.environ["WP_SITE"]
    url = f"https://public-api.wordpress.com/rest/v1.1/sites/{site}/posts/new"
    data = {"title": title, "content": content, "status": "publish"}
    auth = (os.environ["WP_COM_CLIENT_ID"], os.environ["WP_COM_CLIENT_SECRET"])
    headers = {"Authorization": f"Bearer {os.environ['WP_COM_REFRESH_TOKEN']}"}
    r = requests.post(url, headers=headers, data=data)
    print(r.status_code, r.text)

if __name__ == "__main__":
    for _ in range(int(os.environ.get("POSTS_PER_RUN", 1))):
        post_content = create_post()
        publish_to_wp("Automated Post", post_content)

4. Commit the file.




---

Do you want me to give you the next two Python files now so we can finish the automation and make it run daily?

