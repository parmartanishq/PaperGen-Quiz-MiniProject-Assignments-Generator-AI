import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import fitz  # PyMuPDF
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash-latest")

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

def extract_text_from_file(file_path):
    if file_path.endswith(".pdf"):
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
        return text
    elif file_path.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process", methods=["POST"])
def process():
    query = request.form.get("query", "").strip()
    content_type = request.form.get("content_type", "Quiz")
    file = request.files.get("file")
    extracted_text = ""

    if file and file.filename != "":
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        extracted_text = extract_text_from_file(filepath)

    if not extracted_text and not query:
        return jsonify({"result": "Please provide input or upload a file."})

    # Enhanced and structured prompt for clear, focused outputs
    prompt = f"""
You are an expert educational assistant.
Generate only a {content_type.lower()} in a clearly structured, readable format.
Avoid mixing unrelated content.

Use this content for context:
{extracted_text or query}

Format your output properly with numbered questions (if Quiz), headings (if Project Ideas), or sections (if Question Paper).
"""

    try:
        response = model.generate_content(prompt)
        return jsonify({"result": response.candidates[0].content.parts[0].text})
    except Exception as e:
        print("Error from Gemini:", e)
        return jsonify({"result": "Error from model: Please check your input or API key."})

if __name__ == "__main__":
    app.run(debug=True)
