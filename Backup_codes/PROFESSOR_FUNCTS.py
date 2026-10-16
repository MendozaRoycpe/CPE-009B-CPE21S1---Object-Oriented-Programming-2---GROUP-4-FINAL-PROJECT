#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# FUNCTIONS / METHODS LIST:
# - ensure_files()
# - hash_password(password)
# - read_csv(filename)
# - write_csv(filename, rows, fieldnames)
# - get_student_fields()
# - load_students()
# - save_students(students)
# - load_retired_ids()
# - save_retired_ids(rows)
# - load_quizzes()
# - save_quizzes(quizzes)
# - questions_path(quiz_id)
# - load_questions(quiz_id)
# - save_questions(quiz_id, questions)
# - generate_quiz_id(category)
# - compute_total_and_remark(student, quizzes)
#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

import csv, os, hashlib, json
from datetime import datetime

DATA_FOLDER = "data"
STUDENTS_FILE = os.path.join(DATA_FOLDER, "students.csv")
RETIRED_FILE = os.path.join(DATA_FOLDER, "retired_ids.csv")
QUIZZES_FILE = os.path.join(DATA_FOLDER, "quizzes.csv")
AUTH_FILE = os.path.join(DATA_FOLDER, "professor_auth.csv")
SESSIONS_FILE = os.path.join(DATA_FOLDER, "sessions.csv")
CONFLICTS_FILE = os.path.join(DATA_FOLDER, "session_conflicts.csv")
QUESTIONS_FOLDER = os.path.join(DATA_FOLDER, "questions")

DEFAULT_STUDENT_FIELDS = ["student_id", "name"]
QUIZ_FIELDS = ["quiz_id", "title", "category", "max_item", "time_limit_minutes", "published", "date_published"]
SESSION_FIELDS = ["student_id", "device_id", "started_at"]
CONFLICT_FIELDS = ["student_id", "device_id", "attempted_at", "issue_type"]

CATEGORIES = ["English", "Math", "Science", "Computer"]
CATEGORY_PREFIXES = {
    "English": "ENG",
    "Math": "MTH",
    "Science": "SCI",
    "Computer": "CPE",
}

REMARK_EXCELLENT_THRESHOLD = 90
REMARK_GOOD_THRESHOLD = 70

# gawa ng data folder tapos initialize lang ng default csv files kung wala pa
def ensure_files():
    os.makedirs(DATA_FOLDER, exist_ok=True)
    if not os.path.isfile(STUDENTS_FILE):
        with open(STUDENTS_FILE, "w", newline="", encoding="utf-8") as file:
            csv.DictWriter(file, fieldnames=DEFAULT_STUDENT_FIELDS).writeheader()

    if not os.path.isfile(RETIRED_FILE):
        with open(RETIRED_FILE, "w", newline="", encoding="utf-8") as file:
            csv.DictWriter(file, fieldnames=["student_id", "date_retired"]).writeheader()

    if not os.path.isfile(QUIZZES_FILE):
        with open(QUIZZES_FILE, "w", newline="", encoding="utf-8") as file:
            csv.DictWriter(file, fieldnames=QUIZ_FIELDS).writeheader()

    if not os.path.isfile(AUTH_FILE):
        with open(AUTH_FILE, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["password_hash"])
            writer.writeheader()
            writer.writerow({"password_hash": hash_password("jabaiskript")})

    if not os.path.isfile(SESSIONS_FILE):
        with open(SESSIONS_FILE, "w", newline="", encoding="utf-8") as file:
            csv.DictWriter(file, fieldnames=SESSION_FIELDS).writeheader()

    if not os.path.isfile(CONFLICTS_FILE):
        with open(CONFLICTS_FILE, "w", newline="", encoding="utf-8") as file:
            csv.DictWriter(file, fieldnames=CONFLICT_FIELDS).writeheader()

    os.makedirs(QUESTIONS_FOLDER, exist_ok=True)

# para ma-hash string yung password using sha256 para safe
def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

# para mag-read lang ng csv file tapos ibabalik niya list of dictionaries
def read_csv(filename):
    if not os.path.isfile(filename):
        return []
    with open(filename, "r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))

# para mag-write/save ng rows sa csv file gamit yung fieldnames
def write_csv(filename, rows, fieldnames):
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

# kukunin lang yung mga headers o column fields ng student records
def get_student_fields():
    if not os.path.isfile(STUDENTS_FILE):
        return DEFAULT_STUDENT_FIELDS.copy()
    with open(STUDENTS_FILE, "r", newline="", encoding="utf-8") as file:
        header = next(csv.reader(file), None)
    return header if header else DEFAULT_STUDENT_FIELDS.copy()

# kuhanin lahat ng student records sa csv
def load_students():
    return read_csv(STUDENTS_FILE)

# i-save yung list ng new students pabalik sa csv
def save_students(students):
    fields = get_student_fields()
    if not fields:
        fields = DEFAULT_STUDENT_FIELDS.copy()
    write_csv(STUDENTS_FILE, students, fields)

# kailangan ito para sa mga na-delete na student IDs para hindi ma-reuse
def load_retired_ids():
    return read_csv(RETIRED_FILE)

# save ng list ng mga retired student IDs
def save_retired_ids(rows):
    write_csv(RETIRED_FILE, rows, ["student_id", "date_retired"])

# load ng list ng mga quizzes galing sa csv
def load_quizzes():
    return read_csv(QUIZZES_FILE)

# save ng list ng quiz data pabalik sa csv
def save_quizzes(quizzes):
    write_csv(QUIZZES_FILE, quizzes, QUIZ_FIELDS)

# kukuha ng buong file path ng json na naglalaman ng mga tanong
def questions_path(quiz_id):
    os.makedirs(QUESTIONS_FOLDER, exist_ok=True)
    return os.path.join(QUESTIONS_FOLDER, f"{quiz_id}.json")

# i-loload yung listahan ng mga questions para sa quiz_id
def load_questions(quiz_id):
    path = questions_path(quiz_id)
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)

# i-save pabalik yung listahan ng mga questions sa json file
def save_questions(quiz_id, questions):
    with open(questions_path(quiz_id), "w", encoding="utf-8") as file:
        json.dump(questions, file, indent=2)

# awtomatikong gagawa ng Quiz ID base sa category prefix at sequence count
def generate_quiz_id(category):
    prefix = CATEGORY_PREFIXES.get(category, category[:3].upper())
    highest = 0
    for quiz in load_quizzes():
        quiz_id = quiz.get("quiz_id", "")
        if quiz_id.startswith(prefix + "-"):
            suffix = quiz_id[len(prefix) + 1:]
            if suffix.isdigit():
                highest = max(highest, int(suffix))
    return f"{prefix}-{highest + 1:03d}"

# kukuwentahin ang kabuuang score, posibleng total, at remark (Excellent/Good/Poor)
def compute_total_and_remark(student, quizzes):
    total_score = 0
    total_possible = 0
    attempted = False

    for quiz in quizzes:
        quiz_id = quiz.get("quiz_id", "")
        value = student.get(quiz_id, "")
        if value == "" or value is None:
            continue
        try:
            score = int(value)
        except ValueError:
            continue
        attempted = True
        total_score += score
        try:
            total_possible += int(quiz.get("max_item", 0) or 0)
        except ValueError:
            pass

    if not attempted or total_possible == 0:
        return total_score, total_possible, "No grades yet"

    percent = (total_score / total_possible) * 100
    if percent >= REMARK_EXCELLENT_THRESHOLD:
        remark = "Excellent"
    elif percent >= REMARK_GOOD_THRESHOLD:
        remark = "Good"
    else:
        remark = "Poor"
    return total_score, total_possible, remark