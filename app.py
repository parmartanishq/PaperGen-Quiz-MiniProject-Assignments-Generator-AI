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

    if content_type.lower() == "quiz":
        prompt = f"""
You are an expert quiz generator.

Generate exactly 15 multiple choice questions (MCQs) based on the following content. Do not repeat questions. Do not copy any text from the content directly—create original questions based on the concepts.

Format each question like this:

1. Question goes here?
a) Option A  
b) Option B  
c) Option C  
d) Option D  
Answer: Correct option here

Only follow this format strictly. Do not include explanations or introductory lines.

Content to use:
{extracted_text or query}
"""
    elif content_type.lower() == "assignment":
        prompt = f"""
You are an academic content generator.

Create a heading based on the overall topic, and generate exactly 15 descriptive questions worth 5 marks each. These should be based on the content provided. Do not copy the content directly—paraphrase and create unique questions that test conceptual understanding.

Format:
"Heading Related to the Topic"

1. Question one?
2. Question two?
...
15. Question fifteen?

No introductory text or explanation.

Content to use:
{extracted_text or query}
"""
    elif content_type.lower() == "presentation":
        prompt = f"""
You are an academic assistant.

Generate exactly 15 unique presentation topics based on the following content.

Each topic must follow **this exact format**:
1. Title  
   Subtitle (optional, only if it adds value)

**Important rules you must follow strictly**:
- Do NOT use bold text (no **)
- Do NOT add any section titles or categories
- Do NOT add introductory or extra text
- Do NOT exceed or go below 15 topics
- Each entry should be in the format above, one after the other

Content to use:
{extracted_text or query}
"""
    elif content_type.lower() == "mini project":
        prompt = f"""
You are an academic assistant.

Generate exactly 15 mini project ideas based on the content provided.

Each project idea must follow this exact format:
1. Problem statement title  
   A clear and detailed problem description of 4-5 lines explaining the objective and purpose of the project.

Important:
- Do NOT add bold text (no **)
- Do NOT include section headers, categories or extra text
- Make sure all 15 items are present
- The statements should be meaningful, unique, and based on the given content

Content to use:
{extracted_text or query}
"""
    else:
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
        raw_text = response.candidates[0].content.parts[0].text
        cleaned_text = raw_text.replace("**", "")
        return jsonify({"result": cleaned_text})
    except Exception as e:
        print("Error from Gemini:", e)
        return jsonify({"result": "Error from model: Please check your input or API key."})

if __name__ == "__main__":
    app.run(debug=True)
