
import os
import joblib
import pandas as pd

from flask import Flask, render_template, request, redirect, flash, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DB ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "User.db")

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DB_PATH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------- AUTH ----------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("signup", next=request.path))
        return f(*args, **kwargs)
    return wrapper

# ---------------- MODELS ----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    place = db.Column(db.String(100))
    age = db.Column(db.Integer)
    education = db.Column(db.String(50))
    gender = db.Column(db.String(20))
    stress_level = db.Column(db.String(20))
    sleep = db.Column(db.Float)
    screen_time = db.Column(db.Float)
    physical_activity = db.Column(db.Float)
    probability = db.Column(db.Float)
    status = db.Column(db.String(50))

# ---------------- MODEL LOAD ----------------
model = joblib.load(os.path.join(BASE_DIR, "rf_model.joblib"))
preprocessor = joblib.load(os.path.join(BASE_DIR, "preprocessor.joblib"))

# ---------------- ROUTES ----------------
@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    next_page = request.args.get("next")

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")

        if password != confirm:
            flash("Passwords do not match")
            return redirect(url_for("signup", next=next_page))

        if User.query.filter_by(email=email).first():
            flash("Email already exists")
            return redirect(url_for("signup", next=next_page))

        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password)
        )

        db.session.add(user)
        db.session.commit()

        return redirect(url_for("login", next=next_page))

    return render_template("signup.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    next_page = request.args.get("next")

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash("Invalid credentials")
            return redirect(url_for("login", next=next_page))

        session["user_id"] = user.id
        session["user_name"] = user.name

        return redirect(next_page or url_for("dashboard"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- ANALYSIS ----------------
@app.route("/index", methods=["GET", "POST"])
@login_required
def analysis():

    if request.method == "POST":

        form = request.form
        stress_map = {"Low": 1, "Medium": 2, "High": 3}

        age = int(form.get("age"))
        screen_time = float(form.get("screen_time"))
        sleep = float(form.get("sleep_duration"))
        physical = float(form.get("physical_activity"))

        stress = form.get("stress_level")

        df = pd.DataFrame([{
            "Gender": form.get("gender"),
            "Age": age,
            "Education Level": form.get("education"),
            "Screen Time (hrs/day)": screen_time,
            "Sleep Duration (hrs)": sleep,
            "Physical Activity (hrs/week)": physical,
            "Stress Level": stress,
            "Anxious Before Exams": form.get("anxious_exam"),
            "Stress_Level_Num": stress_map.get(stress, 1),
            "Stress_Sleep_Interaction": stress_map.get(stress, 1) * sleep,
            "Screen_Physical_Interaction": screen_time * physical
        }])

        X = preprocessor.transform(df)
        prob = float(model.predict_proba(X)[0][1])

        if prob > 0.7:
            status = "High Risk"
        elif prob > 0.4:
            status = "Medium Risk"
        else:
            status = "Stable"

        student = Student(
            name=form.get("name"),
            place=form.get("place"),
            age=age,
            education=form.get("education"),
            gender=form.get("gender"),
            stress_level=stress,
            sleep=sleep,
            screen_time=screen_time,
            physical_activity=physical,
            probability=prob,
            status=status
        )

        db.session.add(student)
        db.session.commit()

        return redirect(url_for("dashboard"))

    return render_template("index.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
@login_required
def dashboard():

    query = Student.query.order_by(Student.id.desc()).limit(7).all()

    student_data = [
        {
            "name": s.name or "",
            "place": s.place or "",
            "age": s.age or 0,
            "education": s.education or "",
            "probability": float(s.probability or 0),
            "status": s.status or "Stable"
        }
        for s in query
    ]

    total = len(student_data)
    high = sum(1 for s in student_data if s["status"] == "High Risk")
    avg = (sum(s["probability"] for s in student_data) / total) * 100 if total else 0

    return render_template(
        "dashboard.html",
        students=student_data,
        total_students=total,
        high_risk=high,
        avg_risk=avg
    )

# ---------------- API FOR LIVE CHART ----------------
@app.route("/api/students")
@login_required
def get_students():

    query = Student.query.order_by(Student.id.desc()).limit(7).all()

    student_data = [
        {
            "name": s.name or "",
            "place": s.place or "",
            "age": s.age or 0,
            "education": s.education or "",
            "probability": float(s.probability or 0),
            "status": s.status or "Stable"
        }
        for s in query
    ]

    return jsonify({"data": student_data})

# ---------------- RUN ----------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
