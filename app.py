import os
import fitz  # PyMuPDF
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "txt"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Gemini API setup
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("ERROR: GOOGLE_API_KEY is not set.")
    exit(1)

genai.configure(api_key=GOOGLE_API_KEY)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(filepath):
    text = ""
    try:
        doc = fitz.open(filepath)
        for page in doc:
            text += page.get_text("text") + "\n"
        return text.strip()
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def extract_text_from_txt(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return file.read().strip()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def generate_content(prompt):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        response = model.generate_content(prompt)
        return response.text.strip() if response and hasattr(response, "text") else "Error generating content."
    except Exception as e:
        return f"API Error: {str(e)}"

def generate_quiz(text, count):
    prompt = f"""
    Generate {count} multiple-choice quiz questions based on the following content:

    "{text}"

    Each question should have 4 options labeled a, b, c, d.
    After each question and its options, mention the correct answer in the format:
    Correct Answer: <option letter>
    """
    response = generate_content(prompt)
    return response.split("\n") if response else []


@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("index.html")

@app.route("/generate_quiz", methods=["POST"])
def generate_quiz_route():
    text_input = request.form.get("text_input", "").strip()
    file = request.files.get("file")
    quiz_count = int(request.form.get("quiz_count", 10))

    extracted_text = text_input
    if file and allowed_file(file.filename):
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(filepath)
        extracted_text = extract_text_from_pdf(filepath) if file.filename.endswith(".pdf") else extract_text_from_txt(filepath)

    if not extracted_text:
        return render_template("index.html", error="No valid input provided.")

    quiz_questions = generate_quiz(extracted_text, quiz_count)
    return render_template("result.html", quiz_topics=quiz_questions, text=extracted_text)

if __name__ == "__main__":
    app.run(debug=True)
