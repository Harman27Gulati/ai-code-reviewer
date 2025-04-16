from flask import Flask, request
import json
import google.generativeai as genai
import os
import requests

# Configure API key for Gemini
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# Configure Bitbucket credentials from environment
BITBUCKET_USERNAME = os.environ.get("BITBUCKET_USERNAME")
BITBUCKET_APP_PASSWORD = os.environ.get("BITBUCKET_APP_PASSWORD")

# Repo slug (e.g., the repo name from the URL like bitbucket.org/yourteam/yourrepo)
REPO_SLUG = "calculator"  # Change if your Bitbucket repo slug is different

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("\n🎯 Webhook received from Bitbucket:\n")
    print(json.dumps(data, indent=2))

    # Attempt to extract PR ID safely
    try:
        pr_id = data["pullrequest"]["id"]
    except KeyError:
        print("❌ PR ID not found in payload. Please check webhook structure.")
        return '', 400

    # Java file path
    file_path = "src/main/java/com/houarizegai/calculator/App.java"

    try:
        with open(file_path, "r") as file:
            java_code = file.read()

        model = genai.GenerativeModel("models/gemini-1.5-pro")
        response = model.generate_content(
            f"You are a senior Java developer. Please review the following Java code and suggest improvements in maximum 3 bullet points:\n\n{java_code}"
        )

        review_comment = response.text.strip()

        # Construct the comment URL
        comment_url = f"https://api.bitbucket.org/2.0/repositories/{BITBUCKET_USERNAME}/{REPO_SLUG}/pullrequests/{pr_id}/comments"

        # Bitbucket comment payload
        payload = {
            "content": {
                "raw": f"🤖 AI Review:\n{review_comment}"
            }
        }

        # POST request to Bitbucket
        bitbucket_response = requests.post(
            comment_url,
            json=payload,
            auth=(BITBUCKET_USERNAME, BITBUCKET_APP_PASSWORD)
        )

        if bitbucket_response.status_code == 201:
            print("✅ Successfully posted comment to PR.")
        else:
            print(f"❌ Failed to post comment. Status code: {bitbucket_response.status_code}")
            print(bitbucket_response.text)

    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

    return '', 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
