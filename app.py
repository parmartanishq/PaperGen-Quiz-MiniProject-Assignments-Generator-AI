import os
import fitz  # PyMuPDF for PDF text extraction
import google.generativeai as genai
from flask import Flask, render_template, request

app = Flask(__name__)

# Upload folder setup
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "txt"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Fetch Google Gemini API Key from environment variable
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("ERROR: GOOGLE_API_KEY is not set. Please configure your API key.")
    exit(1)

genai.configure(api_key=GOOGLE_API_KEY)

# Function to check allowed file types
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to extract text from PDF
def extract_text_from_pdf(filepath):
    text = ""
    try:
        doc = fitz.open(filepath)
        for page in doc:
            text += page.get_text("text") + "\n"
        return text.strip()
    except Exception as e:
        return f"Error extracting text: {str(e)}"

# Function to extract text from TXT
def extract_text_from_txt(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return file.read().strip()
    except Exception as e:
        return f"Error reading file: {str(e)}"

# Function to interact with Gemini AI
def generate_content(prompt):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        response = model.generate_content(prompt)
        if response and hasattr(response, 'text'):
            return response.text.strip()
        return "Error generating content."
    except Exception as e:
        return f"API Error: {str(e)}"

# Function to generate quiz questions
def generate_quiz(text):
    prompt = f"Generate 10 multiple-choice quiz questions (each with 4 options) based on:\n{text}"
    response = generate_content(prompt)
    return response.split("\n") if response else []

# Function to generate presentation topics
def generate_presentation_topics(text):
    prompt = f"Suggest 5 one-liner presentation topics related to:\n{text}"
    response = generate_content(prompt)
    return response.split("\n") if response else []

# Function to generate mini-project ideas
def generate_project_ideas(text):
    prompt = f"Suggest 3 mini-project ideas with proper titles and problem statements based on:\n{text}"
    response = generate_content(prompt)
    return response.split("\n") if response else []

# Flask route for file upload and processing
@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == "":
            return render_template("upload.html", error="No file uploaded.", topics={})

        if file and allowed_file(file.filename):
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)

            try:
                extracted_text = extract_text_from_pdf(filepath) if file.filename.endswith(".pdf") else extract_text_from_txt(filepath)
                
                topics = {
                    "quiz_topics": generate_quiz(extracted_text),
                    "presentation_topics": generate_presentation_topics(extracted_text),
                    "project_ideas": generate_project_ideas(extracted_text)
                }

                return render_template("result.html", text=extracted_text, topics=topics)

            except Exception as e:
                return render_template("upload.html", error=f"Error processing file: {str(e)}", topics={})

    return render_template("upload.html", topics={})

# Run Flask app
if __name__ == "__main__":
    app.run(debug=True)
