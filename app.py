from sklearn.feature_extraction.text import CountVectorizer 
from sklearn.metrics.pairwise import cosine_similarity 
from flask import Flask, render_template, request 
import pdfplumber 
from docx import Document 
from skills import skills_list 
from google import genai 
import os 
from dotenv import load_dotenv

 
load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY")) 
 
 
# create flask 
app = Flask(__name__) 
 
UPLOAD_FOLDER = "uploads" 
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER 
 
# create uploads folder if it does not exist 
os.makedirs(UPLOAD_FOLDER, exist_ok=True) 
 
 
# extraction text from pdf file 
def extract_pdf_text(path): 
    text = "" 
    with pdfplumber.open(path) as pdf: 
        for page in pdf.pages: 
            text += page.extract_text() or "" 
    return text.lower() 
 
 
# extract text from docx 
def extract_doc_text(path): 
    doc = Document(path) 
    text = "".join([paragraph.text for paragraph in doc.paragraphs]) 
    return text.lower() 
 
 
# extract the skills 
def extract_skills(text): 
    found_skills = [] 
 
    for skill in skills_list: 
        if skill.lower() in text.lower(): 
            found_skills.append(skill) 
 
    return list(set(found_skills)) 
 
 
# match score 
def calculate_similarity(resume, jd): 
    resume_skills = set(extract_skills(resume.lower())) 
    jd_skills = set(extract_skills(jd.lower())) 
 
    if len(jd_skills) == 0: 
        return 0 
 
    matched_skills = resume_skills.intersection(jd_skills) 
 
    score = (len(matched_skills) / len(jd_skills)) * 100 
 
    return round(score, 2) 
 
 
def recommend_jobs(found_skills): 
    jobs = [] 
 
    skills = [skill.lower() for skill in found_skills] 
 
    if "python" in skills: 
        jobs.append("Python Developer ⭐⭐⭐⭐⭐") 
        jobs.append("Backend Developer ⭐⭐⭐⭐") 
        jobs.append("AI/ML Engineer ⭐⭐⭐") 
 
    if "html" in skills and "css" in skills and "javascript" in skills: 
        jobs.append("Full Stack Developer ⭐⭐⭐⭐") 
 
    if "sql" in skills: 
        jobs.append("Data Analyst ⭐⭐⭐⭐") 
 
    if jobs: 
        best_career = jobs[0].split("⭐")[0].strip() 
    else: 
        best_career = "No suitable career found" 
 
    return jobs, best_career 
 
 
@app.route("/", methods=["GET", "POST"]) 
def index(): 
    result = {} 
    recommended_jobs = [] 
    best_career = "" 
 
    if request.method == "POST": 
        jd = request.form["job_description"] 
        file = request.files.get("resume") 
 
        if not file or file.filename == "": 
            return "Please upload a resume." 
 
        filepath = os.path.join( 
            app.config["UPLOAD_FOLDER"], 
            file.filename 
        ) 
 
        file.save(filepath) 
 
        # read resume 
        if file.filename.lower().endswith(".pdf"): 
            resume_text = extract_pdf_text(filepath) 
 
        elif file.filename.lower().endswith(".docx"): 
            resume_text = extract_doc_text(filepath) 
 
        else: 
            return "Unsupported file" 
 
        # skill extraction 
        resume_skills = extract_skills(resume_text) 
        jd_skills = extract_skills(jd.lower()) 
 
        # Recommended Jobs 
        recommended_jobs, best_career = recommend_jobs(resume_skills) 
 
        # missing skills 
        missing_skills = set(jd_skills) - set(resume_skills) 
 
        # similarity score 
        score = calculate_similarity(resume_text, jd) 
 
        result = { 
            "resume_skills": resume_skills, 
            "jd_skills": jd_skills, 
            "missing_skills": list(missing_skills), 
            "score": score, 
        } 
 
    # IMPORTANT: This must be outside the if block 
    return render_template( 
        "index.html", 
        result=result, 
        recommended_jobs=recommended_jobs, 
        best_career=best_career 
    ) 
 
 
@app.route("/chat", methods=["POST"]) 
def chat(): 
    user_message = request.json.get("message", "") 
 
    if not user_message: 
        return {"reply": "Please enter your question."} 
 
    try: 
        response = client.models.generate_content( 
            model="gemini-2.5-flash", 
            contents=f""" 
You are the AI assistant for an AI Resume Analyzer. 
 
Help users with: 
- Resume improvement 
- ATS score 
- Missing skills 
- Job descriptions 
- Career guidance 
- Interview preparation 
- Resume writing 
- Technical skills 
- Software engineering careers 
- General questions 
 
Give simple, clear and useful answers. 
 
User question: 
{user_message} 
""" 
        ) 
 
        return {"reply": response.text} 
 
    except Exception as e: 
        print("Chatbot Error:", e) 
 
        return { 
            "reply": "Sorry, I couldn't process your question right now." 
        } 
 
 
if __name__ == "__main__": 
    app.run(host="0.0.0.0", port=5000, debug=True)