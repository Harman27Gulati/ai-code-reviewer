from flask import Flask, request
import json
import google.generativeai as genai
import os

# Configure API key
os.environ["GOOGLE_API_KEY"] = "AIzaSyByjtOi44YnHbJ4SpWqW0wfNXljdzqJRPw"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("\n🎯 Webhook received from Bitbucket:\n")
    print(json.dumps(data, indent=2))

    # 🔁 Path to your Java file
    file_path = "src\\main\\java\\com\\houarizegai\\calculator\\App.java"

    try:
        with open(file_path, "r") as file:
            java_code = file.read()

        
        model = genai.GenerativeModel("models/gemini-1.5-pro")
        
        # 🧠 Run code review
        response = model.generate_content(
            f"You are a senior Java developer. Please review the following Java code and suggest improvements in maximum 3 bullet points:\n\n{java_code}"
        )

        print("\n🧠 AI Review:\n")
        print(response.text)

    except FileNotFoundError:
        print(f"❌ Could not find file at: {file_path}")
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")

    return '', 200

if __name__ == '__main__':
    app.run(debug=True)