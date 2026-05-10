from flask import Flask, render_template, request, redirect, session
from db import Base, engine, SessionLocal
import models
import PyPDF2
import docx
import json
from ai import analyze_resume
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)

# ---------------- SECURITY CONFIG ----------------
app.secret_key = os.getenv("SECRET_KEY", "dev-only-change-this")

Base.metadata.create_all(bind=engine)

# ---------------- LOGIN DECORATOR ----------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper


# ---------------- HOME ----------------
@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")


# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    db = SessionLocal()
    try:
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")

            existing_user = db.query(models.User).filter_by(email=email).first()
            if existing_user:
                return "User already exists"

            hashed_pw = generate_password_hash(password)

            user = models.User(email=email, password=hashed_pw)
            db.add(user)
            db.commit()

            return redirect("/login")

        return render_template("signup.html")

    finally:
        db.close()


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    db = SessionLocal()
    try:
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")

            user = db.query(models.User).filter_by(email=email).first()

            if user and check_password_hash(user.password, password):
                session["user"] = user.email
                return redirect("/dashboard")

            return "Invalid Credentials"

        return render_template("login.html")

    finally:
        db.close()


# ---------------- FILE VALIDATION ----------------
ALLOWED_EXTENSIONS = {"pdf", "docx"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------- DASHBOARD ----------------
@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():

    result = None
    resume_text = ""
    user_goal = ""

    db = SessionLocal()
    try:
        user = db.query(models.User).filter_by(email=session["user"]).first()
        if not user:
            return redirect("/login")

        if request.method == "POST":
            user_goal = request.form.get("role")
            resume_text = request.form.get("resume")
            file = request.files.get("file")

            # FILE HANDLING
            if file and file.filename != "" and allowed_file(file.filename):

                if file.filename.endswith(".pdf"):
                    pdf_reader = PyPDF2.PdfReader(file)
                    resume_text = "".join(
                        [p.extract_text() or "" for p in pdf_reader.pages]
                    )

                elif file.filename.endswith(".docx"):
                    doc = docx.Document(file)
                    resume_text = "\n".join([p.text for p in doc.paragraphs])

            # AI ANALYSIS
            if resume_text and user_goal:
                try:
                    result = analyze_resume(resume_text, user_goal)

                    report = models.Report(
                        user_id=user.id,
                        resume_text=resume_text,
                        results=json.dumps(result)
                    )

                    db.add(report)
                    db.commit()

                except Exception as e:
                    result = {"error": str(e)}

        return render_template(
            "dashboard.html",
            user=session["user"],
            result=result
        )

    finally:
        db.close()


# ---------------- HISTORY ----------------
@app.route("/history")
@login_required
def history():

    db = SessionLocal()
    try:
        user = db.query(models.User).filter_by(email=session["user"]).first()
        if not user:
            return redirect("/login")

        reports = db.query(models.Report).filter_by(user_id=user.id).all()

        parsed_reports = []
        for r in reports:
            try:
                parsed_result = json.loads(r.results)
            except:
                parsed_result = {}

            parsed_reports.append({
                "resume": r.resume_text,
                "result": parsed_result
            })

        return render_template("history.html", reports=parsed_reports)

    finally:
        db.close()


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0")