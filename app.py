from flask import Flask, request
import json
import google.generativeai as genai
import os
import requests
import base64

# Configure API key for Gemini
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# Configure GitHub credentials from environment
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = os.environ.get("GITHUB_REPO")  # In format "username/repo"

app = Flask(__name__)

# Add root route handler for Render health checks
@app.route('/', methods=['GET'])
def index():
    return "GitHub PR Review Bot is running!", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    # Get header signature for GitHub
    github_event = request.headers.get('X-GitHub-Event')
    
    if github_event not in ['pull_request', 'pull_request_review']:
        print(f"📩 Received GitHub event: {github_event} - not processing")
        return '', 200
    
    data = request.json
    print("\n🎯 Webhook received from GitHub:\n")
    print(json.dumps(data, indent=2))
    
    # Only process when PRs are opened or synchronized (updated)
    action = data.get('action')
    if action not in ['opened', 'synchronize']:
        print(f"📩 Pull request {action} - not processing")
        return '', 200
    
    # Extract PR information
    pr_data = data.get('pull_request', {})
    pr_number = pr_data.get('number')
    
    if not pr_number:
        print("❌ PR number not found")
        return '', 200
    
    print(f"🔍 Processing PR #{pr_number}")
    
    # Get list of files changed in the PR
    try:
        files_url = f"https://api.github.com/repos/{GITHUB_REPO}/pulls/{pr_number}/files"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        files_response = requests.get(files_url, headers=headers)
        
        if files_response.status_code != 200:
            print(f"❌ Failed to fetch PR files. Status code: {files_response.status_code}")
            print(files_response.text)
            return '', 200
        
        files_data = files_response.json()
        java_files = [file for file in files_data if file.get('filename', '').endswith('.java')]
        
        if not java_files:
            print("📄 No Java files found in this PR")
            return '', 200
        
        for file in java_files:
            file_name = file.get('filename')
            print(f"📝 Processing {file_name}")
            
            # Get the file content
            content_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_name}?ref={pr_data.get('head', {}).get('ref')}"
            content_response = requests.get(content_url, headers=headers)
            
            if content_response.status_code != 200:
                print(f"❌ Failed to fetch content for {file_name}. Status code: {content_response.status_code}")
                continue
            
            content_data = content_response.json()
            # GitHub API returns content as base64 encoded
            file_content = base64.b64decode(content_data.get('content')).decode('utf-8')
            
            # Generate review with Gemini
            print(f"🤖 Generating AI review for {file_name}")
            model = genai.GenerativeModel("models/gemini-1.5-pro")
            response = model.generate_content(
                f"You are a senior Java developer. Please review the following Java code and suggest improvements in maximum 3 bullet points:\n\n{file_content}"
            )
            
            review_comment = response.text.strip()
            
            # Post the review as a comment on the PR
            comments_url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/{pr_number}/comments"
            comment_payload = {
                "body": f"## 🤖 AI Review for `{file_name}`\n\n{review_comment}"
            }
            
            comment_response = requests.post(
                comments_url,
                headers=headers,
                json=comment_payload
            )
            
            if comment_response.status_code == 201:
                print(f"✅ Successfully posted review comment for {file_name}")
            else:
                print(f"❌ Failed to post comment. Status code: {comment_response.status_code}")
                print(comment_response.text)
    
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
    
    return '', 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)