import sys
import os
import csv
import json
import socket
import hashlib
import random
import ctypes
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QWidget, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, 
    QComboBox, QTextEdit, QFrame, QHeaderView, QRadioButton, QButtonGroup,
    QProgressBar, QStackedWidget, QSizePolicy, QScrollArea, QListWidget, QListWidgetItem,
    QFormLayout, QDialogButtonBox, QSpinBox, QFileDialog, QAbstractItemView, QGraphicsOpacityEffect,
    QInputDialog,
)
from PyQt6.QtCore import Qt, QTimer, QEvent, QPropertyAnimation, QEasingCurve, QRectF, QPointF
from PyQt6.QtGui import QIcon, QColor, QPainter, QLinearGradient, QPen, QFont, QPainterPath, QBrush

#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# FUNCTIONS / METHODS LIST (single-file "compilation" build of the Group 4 quiz system):
# - apply_app_icon(widget), hash_password(password), get_device_id(), get_spaced_now()
# - calculate_remarks(score, total), apply_fade_in(widget, duration)
# - read_csv(filename), write_csv(filename, rows, fieldnames), get_student_fields()
# - load_students()/save_students(), load_retired_ids()/save_retired_ids()
# - load_quizzes()/save_quizzes(), questions_path(quiz_id), load_questions()/save_questions()
# - generate_quiz_id(category), compute_total_and_remark(student, quizzes)
# - load_sessions()/save_sessions(), start_session(student_id), end_session(student_id),
#   log_conflict(student_id, issue_type)
# - generate_auto_questions(count), ensure_files(), table_cell(text)
#
# CLASSES:
# - GradientButton — T.I.P.-gold animated hover/press button
# - AddStudentDialog, QuizDialog, QuestionDialog, GradebookDialog (anti-cheat audit log
#   viewer), FullscreenPromptDialog (pre-quiz proctoring notice)
# - QuestionManagerWindow, QuizManagerWindow
# - ProfessorLogin, ProfessorDashboard
# - StudentLogin, StudentDashboard, MyGradesWindow, TakeQuizWindow (fullscreen, proctored,
#   logs focus loss via log_conflict), ResultWindow
# - MainLauncher — role-select portal; entry point is main()
#
#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ==========================================
# FILE PATHS & STORAGE INITIALIZATION
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
QUESTIONS_DIR = os.path.join(DATA_DIR, "questions")

STUDENTS_CSV = os.path.join(DATA_DIR, "students.csv")
STUDENTS_FILE = STUDENTS_CSV  # alias: several GUI methods below write students via this name
RETIRED_CSV = os.path.join(DATA_DIR, "retired_ids.csv")
QUIZZES_CSV = os.path.join(DATA_DIR, "quizzes.csv")
AUTH_CSV = os.path.join(DATA_DIR, "professor_auth.csv")
SESSIONS_CSV = os.path.join(DATA_DIR, "sessions.csv")
CONFLICTS_CSV = os.path.join(DATA_DIR, "session_conflicts.csv")

# Dynamic icon path resolution
ICON_PATH = os.path.join(BASE_DIR, "TIPlogo.ico")

STUDENT_FIELDS = ["student_id", "name"]
QUIZ_FIELDS = ["quiz_id", "title", "category", "max_item", "time_limit_minutes", "published", "date_published"]
SESSION_FIELDS = ["session_id", "student_id", "quiz_id", "score", "date_taken", "tab_switches", "remarks", "device_id", "started_at"]
CONFLICT_FIELDS = ["conflict_id", "student_id", "device_id", "issue_type", "description", "attempted_at", "status"]

CATEGORIES = ["English", "Math", "Science", "Computer"]
CATEGORY_PREFIXES = {
    "English": "ENG",
    "Math": "MTH",
    "Science": "SCI",
    "Computer": "CPE",
}

# Helper function to apply the window icon to any widget/dialog
def apply_app_icon(widget: QWidget):
    if os.path.exists(ICON_PATH):
        widget.setWindowIcon(QIcon(ICON_PATH))

# ==========================================
# HELPER & DATA FUNCTIONS
# ==========================================
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def get_device_id() -> str:
    return socket.gethostname()

def get_spaced_now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def calculate_remarks(score: int, total: int) -> str:
    if total <= 0:
        return "No grades yet"
    percentage = (score / total) * 100
    if percentage >= 90:
        return "Excellent"
    elif percentage >= 75:
        return "Good"
    elif percentage >= 50:
        return "Fair"
    else:
        return "Poor"

def apply_fade_in(widget, duration=350):
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
    anim.start()
    widget._fade_anim = anim

def read_csv(filename: str) -> list:
    if not os.path.isfile(filename):
        return []
    with open(filename, "r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))

def write_csv(filename: str, rows: list, fieldnames: list):
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def get_student_fields() -> list:
    if not os.path.isfile(STUDENTS_CSV):
        return STUDENT_FIELDS.copy()
    with open(STUDENTS_CSV, "r", newline="", encoding="utf-8") as file:
        header = next(csv.reader(file), None)
    fields = header if header else STUDENT_FIELDS.copy()
    # Self-heal: a students.csv left over from an older/broken run of this script
    # may have a header missing "student_id" or "name" (e.g. just ["student_id"]).
    # Blindly trusting that header made every later write silently drop the
    # missing column and then crash ("dict contains fields not in fieldnames")
    # the moment a row with that column was written. Always guarantee the two
    # required columns are present, in front, regardless of what's on disk.
    missing_required = [f for f in STUDENT_FIELDS if f not in fields]
    return missing_required + fields if missing_required else fields

def load_students() -> list:
    return read_csv(STUDENTS_CSV)

def save_students(students: list):
    fields = get_student_fields()
    if not fields:
        fields = STUDENT_FIELDS.copy()
    write_csv(STUDENTS_CSV, students, fields)

def load_retired_ids() -> list:
    return read_csv(RETIRED_CSV)

def save_retired_ids(rows: list):
    write_csv(RETIRED_CSV, rows, ["student_id", "date_retired"])

def load_quizzes() -> list:
    return read_csv(QUIZZES_CSV)

def save_quizzes(quizzes: list):
    write_csv(QUIZZES_CSV, quizzes, QUIZ_FIELDS)

def questions_path(quiz_id: str) -> str:
    os.makedirs(QUESTIONS_DIR, exist_ok=True)
    return os.path.join(QUESTIONS_DIR, f"{quiz_id}.json")

def load_questions(quiz_id: str) -> list:
    path = questions_path(quiz_id)
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)

def save_questions(quiz_id: str, questions: list):
    with open(questions_path(quiz_id), "w", encoding="utf-8") as file:
        json.dump(questions, file, indent=2)

def generate_quiz_id(category: str) -> str:
    prefix = CATEGORY_PREFIXES.get(category, category[:3].upper())
    highest = 0
    for quiz in load_quizzes():
        quiz_id = quiz.get("quiz_id", "")
        if quiz_id.startswith(prefix + "-"):
            suffix = quiz_id[len(prefix) + 1:]
            if suffix.isdigit():
                highest = max(highest, int(suffix))
    return f"{prefix}-{highest + 1:03d}"

def compute_total_and_remark(student: dict, quizzes: list):
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

    return total_score, total_possible, calculate_remarks(total_score, total_possible)

# ==========================================
# SESSION & CONFLICT LOGGING
# ==========================================
def load_sessions() -> list:
    return read_csv(SESSIONS_CSV)

def save_sessions(rows: list):
    write_csv(SESSIONS_CSV, rows, SESSION_FIELDS)

def start_session(student_id: str) -> str:
    sessions = load_sessions()
    device_id = get_device_id()

    for session in sessions:
        if session.get("student_id") == student_id:
            if session.get("device_id") == device_id:
                return "ok"
            log_conflict(student_id, "Device Conflict / Multiple Logins")
            return "conflict"

    sessions.append({
        "session_id": f"SESS_{len(sessions) + 1:04d}",
        "student_id": student_id,
        "quiz_id": "",
        "score": "0",
        "date_taken": get_spaced_now(),
        "tab_switches": "0",
        "remarks": "",
        "device_id": device_id,
        "started_at": get_spaced_now()
    })
    save_sessions(sessions)
    return "ok"

def end_session(student_id: str):
    sessions = [s for s in load_sessions() if s.get("student_id") != student_id]
    save_sessions(sessions)

def log_conflict(student_id: str, issue_type: str = "Device Conflict"):
    conflicts = read_csv(CONFLICTS_CSV)
    conflicts.append({
        "conflict_id": f"CONF_{len(conflicts) + 1:04d}",
        "student_id": student_id,
        "device_id": get_device_id(),
        "issue_type": issue_type,
        "description": f"Incident recorded for student {student_id}",
        "attempted_at": get_spaced_now(),
        "status": "Flagged"
    })
    write_csv(CONFLICTS_CSV, conflicts, CONFLICT_FIELDS)

# ==========================================
# QUESTION GENERATOR & DEFAULT INITIALIZATION
# ==========================================
QUESTION_BANK_MC = [
    ("Which data structure operates on a First In, First Out (FIFO) protocol?", ["Stack", "Queue", "Binary Tree", "Hash Map"], 1),
    ("What is the main function of the CPU in a computer architecture?", ["Data Storage", "Executing Instructions", "Network Routing", "Power Supply"], 1),
    ("Which protocol is used to securely transfer web pages over the Internet?", ["HTTP", "HTTPS", "FTP", "SMTP"], 1),
    ("What is the average time complexity of searching in a balanced Binary Search Tree?", ["O(1)", "O(log n)", "O(n)", "O(n^2)"], 1),
    ("Which programming language is predominantly used for data science and AI development?", ["C++", "HTML", "Python", "Assembly"], 2),
    ("What component in a computer temporarily holds data currently in use?", ["Hard Disk Drive", "RAM", "ROM", "Power Supply"], 1),
    ("Which keyword is used in Python to define a user function?", ["func", "def", "define", "function"], 1),
    ("What does SQL stand for in database systems?", ["Sequential Query Language", "Structured Query Language", "Standardized Question Language", "System Query Logic"], 1),
    ("What is the boiling point of water at standard sea level atmospheric pressure?", ["90°C", "100°C", "120°C", "80°C"], 1),
    ("Which gas do plants absorb during the process of photosynthesis?", ["Oxygen", "Carbon Dioxide", "Nitrogen", "Hydrogen"], 1),
    ("What is the hardest naturally occurring substance on Earth?", ["Gold", "Iron", "Diamond", "Quartz"], 2),
    ("Which planet in our solar system is known as the Red Planet?", ["Venus", "Mars", "Jupiter", "Saturn"], 1),
    ("What chemical symbol represents gold on the periodic table?", ["Ag", "Au", "Fe", "Pb"], 1),
    ("What is the derivative of f(x) = x^2 with respect to x?", ["x", "2x", "x^2", "2"], 1),
    ("What is the value of 2 raised to the power of 8 (2^8)?", ["128", "256", "512", "1024"], 1),
    ("In geometry, what is the sum of interior angles in a triangle?", ["180°", "360°", "90°", "270°"], 0),
    ("Which unit measures electrical resistance in a circuit?", ["Volt", "Ampere", "Ohm", "Watt"], 2),
    ("What primary energy source powers the Earth's climate system?", ["The Moon", "Geothermal Core", "The Sun", "Ocean Currents"], 2),
]

QUESTION_BANK_TF = [
    ("Python tuples are immutable sequence structures.", ["True", "False"], 0),
    ("In binary representation, the number 10 corresponds to the decimal number 2.", ["True", "False"], 0),
    ("RAM retains stored data even when the computer is powered off.", ["True", "False"], 1),
    ("HTTP operates on top of the TCP/IP transport protocol stack.", ["True", "False"], 0),
    ("An equilateral triangle has three sides of different lengths.", ["True", "False"], 1),
    ("Light travels faster than sound in a vacuum.", ["True", "False"], 0),
    ("The atomic number corresponds to the number of protons in an atomic nucleus.", ["True", "False"], 0),
    ("DNA stands for Deoxyribonucleic Acid.", ["True", "False"], 0),
    ("Solid ice is less dense than liquid water, causing it to float.", ["True", "False"], 0),
    ("A leap year in the Gregorian calendar contains 366 total days.", ["True", "False"], 0),
]

def generate_auto_questions(count=10):
    questions = []
    mc_count = int(count * 0.7)
    tf_count = count - mc_count

    mc_selected = random.sample(QUESTION_BANK_MC, min(mc_count, len(QUESTION_BANK_MC)))
    for q_txt, opts, c_idx in mc_selected:
        questions.append({
            "qtype": "MCQ",
            "text": q_txt,
            "choices": opts,
            "correct_index": c_idx
        })

    tf_selected = random.sample(QUESTION_BANK_TF, min(tf_count, len(QUESTION_BANK_TF)))
    for q_txt, opts, c_idx in tf_selected:
        questions.append({
            "qtype": "TF",
            "text": q_txt,
            "choices": opts,
            "correct_index": c_idx
        })

    random.shuffle(questions)
    return questions[:count]

def ensure_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(QUESTIONS_DIR, exist_ok=True)

    files = [
        (STUDENTS_CSV, STUDENT_FIELDS),
        (RETIRED_CSV, ["student_id", "date_retired"]),
        (QUIZZES_CSV, QUIZ_FIELDS),
        (SESSIONS_CSV, SESSION_FIELDS),
        (CONFLICTS_CSV, CONFLICT_FIELDS)
    ]

    for path, headers in files:
        if not os.path.exists(path):
            with open(path, "w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=headers).writeheader()

    if not os.path.exists(AUTH_CSV):
        with open(AUTH_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["password_hash"])
            writer.writeheader()
            writer.writerow({"password_hash": hash_password("jabaiskript")})

    quizzes = read_csv(QUIZZES_CSV)
    if not quizzes:
        now_date = get_spaced_now()
        default_quizzes = [
            {"quiz_id": "CPE-001", "title": "Comprehensive CS & Science Assessment", "category": "Computer", "max_item": "10", "time_limit_minutes": "15", "published": "yes", "date_published": now_date},
            {"quiz_id": "MTH-001", "title": "Midterm Exam - STEM Fundamentals", "category": "Math", "max_item": "10", "time_limit_minutes": "10", "published": "yes", "date_published": now_date}
        ]
        for q in default_quizzes:
            qs = generate_auto_questions(int(q["max_item"]))
            save_questions(q["quiz_id"], qs)

        write_csv(QUIZZES_CSV, default_quizzes, QUIZ_FIELDS)

        students = load_students()
        if not students:
            sample_student = {"student_id": "2026-0001", "name": "Student Demo"}
            for q in default_quizzes:
                sample_student[q["quiz_id"]] = ""
            students.append(sample_student)
            # Use the sample student's own keys as the header — get_student_fields()/
            # save_students() would read the CSV header written moments ago (just
            # student_id, name) and crash on the extra quiz-id columns below.
            write_csv(STUDENTS_CSV, students, list(sample_student.keys()))

def table_cell(text: str) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
    return item

# ==========================================
# CUSTOM ANIMATED BUTTON (T.I.P. GOLD)
# ==========================================
class GradientButton(QPushButton):
    """T.I.P. Gold button with animated hover elevation and sheen shift."""
    def __init__(self, text="", parent=None, clicked=None):
        super().__init__(text, parent)
        self._shift = 0.0
        self._hover = 0.0
        self._press = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(40)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet("background: transparent; border: none; color: #111111;")
        if clicked is not None:
            super().clicked.connect(clicked)

    def enterEvent(self, event):
        self._timer.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._timer.start()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self._press = 1.0
        self._timer.start()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

    def _tick(self):
        target = 1.0 if self.underMouse() else 0.0
        self._hover += (target - self._hover) * 0.16
        if self.underMouse():
            self._shift = (self._shift + 0.018) % 1.0
        self._press *= 0.82
        if self._hover < 0.01 and self._press < 0.01 and not self.underMouse():
            self._hover = 0.0
            self._press = 0.0
            self._timer.stop()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Lift and scale on hover
        rect = QRectF(self.rect()).adjusted(2, 2 - self._hover * 2, -2, -2 - self._hover * 2)
        
        # Gold Gradient Palette (T.I.P. Gold)
        c1 = QColor("#FFD54F")
        c2 = QColor("#FFC700")
        c3 = QColor("#FFA000")
        
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        shift = self._shift
        pairs = [
            ((0.0 + shift) % 1.0, c1),
            ((0.5 + shift) % 1.0, c2),
            ((0.85 + shift) % 1.0, c3),
        ]
        pairs.sort(key=lambda item: item[0])
        gradient.setColorAt(0.0, pairs[0][1])
        for pos, color in pairs:
            gradient.setColorAt(min(pos, 0.999), color)
        gradient.setColorAt(1.0, pairs[-1][1])
        
        path = QPainterPath()
        path.addRoundedRect(rect, 10, 10)
        painter.fillPath(path, QBrush(gradient))
        
        # Glow border when hovered
        if self._hover > 0.05:
            painter.setPen(QPen(QColor(255, 255, 255, int(180 * self._hover)), 2))
            painter.drawPath(path)
            
        painter.setPen(QColor("#111111"))
        font = QFont(self.font())
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())
        painter.end()

# ==========================================
# CLEAN WHITE STYLESHEET
# ==========================================
APP_STYLE = """
QWidget {
    background-color: #FFFFFF;
    color: #1E293B;
    font-family: 'Inter', 'Segoe UI', -apple-system, sans-serif;
    font-size: 13px;
}

QFrame#Panel {
    background-color: #F8FAFC;
    border-radius: 12px;
    border: 1px solid #E2E8F0;
}

QFrame#HeaderCard {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFFBEB, stop:1 #FEF3C7);
    border-radius: 14px;
    border: 1px solid #FCD34D;
}

QFrame#RulesCard {
    background-color: #F8FAFC;
    border: 2px solid #FFC700;
    border-radius: 16px;
}

QFrame#WarningCardClean {
    background-color: #F0FDF4;
    border: 1px solid #86EFAC;
    border-radius: 10px;
}

QFrame#WarningCardWarn {
    background-color: #FEF2F2;
    border: 1px solid #FCA5A5;
    border-radius: 10px;
}

QLabel {
    background: transparent;
    color: #1E293B;
}

QPushButton {
    background-color: #FFC700;
    color: #111111;
    font-weight: 700;
    border-radius: 10px;
    padding: 10px 18px;
    border: none;
}
QPushButton:hover {
    background-color: #FFB300;
}
QPushButton:pressed {
    background-color: #FFA000;
}

QPushButton#BtnDanger {
    background-color: #EF4444;
    color: #FFFFFF;
}
QPushButton#BtnDanger:hover {
    background-color: #DC2626;
}

QPushButton#BtnSecondary {
    background-color: #F1F5F9;
    color: #475569;
    border: 1px solid #CBD5E1;
}
QPushButton#BtnSecondary:hover {
    background-color: #E2E8F0;
    color: #0F172A;
}

QLineEdit, QComboBox, QTextEdit, QSpinBox {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 10px;
    padding: 8px;
    color: #0F172A;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QSpinBox:focus {
    border: 2px solid #FFC700;
    background-color: #FFFEF5;
}

QRadioButton {
    background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 12px;
    padding: 12px;
    color: #1E293B;
    font-weight: 500;
}
QRadioButton:hover {
    border: 1px solid #FFC700;
    background-color: #FFFBEB;
}

QTableWidget, QListWidget {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    gridline-color: #F1F5F9;
}
QTableWidget::item:selected, QListWidget::item:selected {
    background-color: #FEF3C7;
    color: #1E293B;
}
QHeaderView::section {
    background-color: #F8FAFC;
    color: #475569;
    font-weight: bold;
    padding: 8px;
    border: none;
    border-bottom: 2px solid #E2E8F0;
}

QProgressBar {
    background-color: #F1F5F9;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    text-align: center;
    color: #1E293B;
    font-weight: bold;
}
QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFC700, stop:1 #10B981);
    border-radius: 7px;
}
"""

# ==========================================
# DIALOGS & SUBSIDIARY WINDOWS
# ==========================================
class AddStudentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        apply_app_icon(self)
        self.setWindowTitle("Add Student")
        self.setMinimumWidth(400)
        layout = QFormLayout(self)
        self.id_input = QLineEdit()
        self.name_input = QLineEdit()
        layout.addRow("Student ID:", self.id_input)
        layout.addRow("Student Name:", self.name_input)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self):
        return (self.id_input.text().strip(), self.name_input.text().strip())

class QuizDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        apply_app_icon(self)
        self.setWindowTitle("Create Quiz")
        self.setMinimumWidth(450)
        layout = QFormLayout(self)

        self.title_input = QLineEdit()
        self.category = QComboBox()
        self.category.addItems(CATEGORIES)

        self.quiz_id_preview = QLabel()
        self.quiz_id_preview.setStyleSheet("font-weight: bold; color: #D97706;")
        self.category.currentTextChanged.connect(self.update_quiz_id_preview)

        self.max_item = QSpinBox()
        self.max_item.setRange(10, 999)
        self.time_limit = QSpinBox()
        self.time_limit.setRange(1, 999)

        layout.addRow("Quiz Title:", self.title_input)
        layout.addRow("Category:", self.category)
        layout.addRow("Auto-generated Quiz ID:", self.quiz_id_preview)
        layout.addRow("Maximum Items:", self.max_item)
        layout.addRow("Time Limit (minutes):", self.time_limit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.update_quiz_id_preview(self.category.currentText())

    def update_quiz_id_preview(self, category):
        self.quiz_id_preview.setText(generate_quiz_id(category))

    def get_data(self):
        category = self.category.currentText()
        return {
            "quiz_id": generate_quiz_id(category),
            "title": self.title_input.text().strip(),
            "category": category,
            "max_item": str(self.max_item.value()),
            "time_limit_minutes": str(self.time_limit.value()),
        }

class QuestionDialog(QDialog):
    def __init__(self, parent=None, existing=None):
        super().__init__(parent)
        apply_app_icon(self)
        self.setWindowTitle("Edit Question" if existing else "Add Question")
        self.setMinimumWidth(480)
        layout = QFormLayout(self)

        self.text_input = QLineEdit()
        layout.addRow("Question Text:", self.text_input)

        self.type_box = QComboBox()
        self.type_box.addItems(["Multiple Choice Question", "True or False"])
        layout.addRow("Type:", self.type_box)

        self.choice_inputs = [QLineEdit() for _ in range(4)]
        self.choice_rows = []
        self.choice_letters = ["A", "B", "C", "D"]
        for i, box in enumerate(self.choice_inputs):
            box.setPlaceholderText(f"Choice {self.choice_letters[i]}")
            # Keep the "Correct Answer" dropdown's A/B/C/D labels in sync with
            # whatever the professor is currently typing in each choice box.
            box.textChanged.connect(self.refresh_correct_choices)
            layout.addRow(f"Choice {self.choice_letters[i]}:", box)
            self.choice_rows.append(layout.rowCount() - 1)

        # Was a QSpinBox limited to typing a bare number (and the TF toggle
        # capped it at 1-2, which read as "only 1 or 2 can ever be correct").
        # A dropdown of A/B/C/D (or True/False) is both clearer and removes
        # the chance of an out-of-range number ever reaching correct_index.
        self.correct_combo = QComboBox()
        layout.addRow("Correct Answer:", self.correct_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.type_box.currentTextChanged.connect(self.toggle_choice_fields)

        if existing:
            self.text_input.setText(existing.get("text", ""))
            qtype_mapped = "Multiple Choice Question" if existing.get("qtype") == "MCQ" else "True or False"
            self.type_box.setCurrentText(qtype_mapped)
            choices = existing.get("choices", [])
            for i, box in enumerate(self.choice_inputs):
                if i < len(choices):
                    box.setText(choices[i])
            self.correct_combo.setCurrentIndex(existing.get("correct_index", 0))

        self.toggle_choice_fields(self.type_box.currentText())

    def toggle_choice_fields(self, qtype):
        is_mcq = (qtype == "Multiple Choice Question")
        form = self.layout()
        for row in self.choice_rows:
            form.setRowVisible(row, is_mcq)
        self.refresh_correct_choices()
        self.adjustSize()

    def refresh_correct_choices(self):
        is_mcq = (self.type_box.currentText() == "Multiple Choice Question")
        previous_index = self.correct_combo.currentIndex()
        self.correct_combo.blockSignals(True)
        self.correct_combo.clear()
        if is_mcq:
            for i, box in enumerate(self.choice_inputs):
                entered = box.text().strip()
                label = f"{self.choice_letters[i]}. {entered}" if entered else f"{self.choice_letters[i]} (empty)"
                self.correct_combo.addItem(label)
        else:
            self.correct_combo.addItems(["True", "False"])
        if 0 <= previous_index < self.correct_combo.count():
            self.correct_combo.setCurrentIndex(previous_index)
        self.correct_combo.blockSignals(False)

    def get_data(self):
        qtype_ui = self.type_box.currentText()
        qtype = "MCQ" if qtype_ui == "Multiple Choice Question" else "TF"
        text = self.text_input.text().strip()
        if qtype == "MCQ":
            # Keep all four slots (even a still-blank one) so that choice index
            # i always lines up with letter choice_letters[i] and with whatever
            # the professor picked in the Correct Answer dropdown. Filtering
            # out blanks here used to silently shift later choices down a slot,
            # which could save the wrong option as "correct".
            choices = [box.text().strip() for box in self.choice_inputs]
        else:
            choices = ["True", "False"]
        correct_index = self.correct_combo.currentIndex()
        return {"qtype": qtype, "text": text, "choices": choices, "correct_index": correct_index}

class GradebookDialog(QDialog):
    def __init__(self, student_id=None, parent=None):
        super().__init__(parent)
        apply_app_icon(self)
        self.setWindowTitle("Quiz System - Anti-Cheat Audit Logs")
        self.resize(850, 480)
        self.student_id = student_id
        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self)

        top_panel = QFrame()
        top_panel.setObjectName("Panel")
        tp_layout = QHBoxLayout(top_panel)

        tp_layout.addWidget(QLabel("Filter by Student ID:"))
        self.cmb_filter = QComboBox()
        self.cmb_filter.currentIndexChanged.connect(self.load_results)
        tp_layout.addWidget(self.cmb_filter)

        layout.addWidget(top_panel)

        self.table = QTableWidget(0, 6)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setHorizontalHeaderLabels(["Student ID", "Device ID", "Issue Type", "Description", "Timestamp", "Status"])
        header = self.table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.table)

        btn_close = QPushButton("Close Audit Logs")
        btn_close.setObjectName("BtnSecondary")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

        self.fill_filter()
        self.load_results()

    def fill_filter(self):
        conflicts = read_csv(CONFLICTS_CSV)
        sids = sorted(list({c.get("student_id", "").strip() for c in conflicts if c.get("student_id")}))
        
        self.cmb_filter.blockSignals(True)
        self.cmb_filter.clear()
        self.cmb_filter.addItem("All Students")
        for sid in sids:
            self.cmb_filter.addItem(sid)
        if self.student_id and self.student_id in sids:
            self.cmb_filter.setCurrentText(self.student_id)
        self.cmb_filter.blockSignals(False)

    def load_results(self):
        self.table.setRowCount(0)
        conflicts = read_csv(CONFLICTS_CSV)
        selected_sid = self.cmb_filter.currentText()

        for conf in conflicts:
            sid = conf.get("student_id", "")
            if selected_sid != "All Students" and sid != selected_sid:
                continue

            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, table_cell(sid))
            self.table.setItem(row, 1, table_cell(conf.get("device_id", "")))
            self.table.setItem(row, 2, table_cell(conf.get("issue_type", "")))
            self.table.setItem(row, 3, table_cell(conf.get("description", conf.get("attempted_at", ""))))
            self.table.setItem(row, 4, table_cell(conf.get("attempted_at", "")))
            
            st_item = table_cell(conf.get("status", "Flagged"))
            st_item.setForeground(QColor("#EF4444"))
            self.table.setItem(row, 5, st_item)

class FullscreenPromptDialog(QDialog):
    def __init__(self, quiz_title: str, duration: str, total_q: str, parent=None):
        super().__init__(parent)
        apply_app_icon(self)
        self.setWindowTitle("Quiz Portal - Proctoring Guidelines")
        self.setFixedWidth(460)

        layout = QVBoxLayout(self)
        card = QFrame()
        card.setObjectName("RulesCard")
        c_layout = QVBoxLayout(card)
        c_layout.setSpacing(12)

        icon_lbl = QLabel("🛡️")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 38px;")
        c_layout.addWidget(icon_lbl)

        title = QLabel(f"<b>{quiz_title}</b>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 17px; color: #D97706;")
        c_layout.addWidget(title)

        info = QLabel(
            f"⏱️ Allocated Duration: <b>{duration} Minutes</b><br>"
            f"❓ Questions Count: <b>{total_q} Items</b>"
        )
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("color: #475569; font-size: 13px;")
        c_layout.addWidget(info)

        rules = QLabel(
            "<b>Proctoring Guidelines:</b><br>"
            "1. Quiz opens locked in <b>FULLSCREEN MODE</b>.<br>"
            "2. Focus shifts or tab switching (<b>Alt + Tab</b>) are strictly recorded.<br>"
            "3. Ensure all questions are answered before submitting."
        )
        rules.setStyleSheet("color: #64748B; font-size: 12px;")
        rules.setWordWrap(True)
        c_layout.addWidget(rules)

        layout.addWidget(card)

        btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("BtnSecondary")
        btn_cancel.clicked.connect(self.reject)

        btn_start = GradientButton("Enter Fullscreen & Start")
        btn_start.clicked.connect(self.accept)

        btns.addWidget(btn_cancel)
        btns.addWidget(btn_start)
        layout.addLayout(btns)

class QuestionManagerWindow(QDialog):
    def __init__(self, quiz_id, quiz_title, parent=None):
        super().__init__(parent)
        apply_app_icon(self)
        self.quiz_id = quiz_id
        self.setWindowTitle(f"Questions — {quiz_title}")
        self.setMinimumSize(600, 520)
        layout = QVBoxLayout(self)

        self.count_label = QLabel()
        layout.addWidget(self.count_label)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Type", "Question"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table, 1)

        button_layout = QHBoxLayout()
        add_button = GradientButton("Add Question", clicked=self.add_question)
        edit_button = QPushButton("Edit Question", clicked=self.edit_question)
        delete_button = QPushButton("Delete Question", clicked=self.delete_question)
        close_button = QPushButton("Close", clicked=self.accept)
        for b in (add_button, edit_button, delete_button, close_button):
            button_layout.addWidget(b)
        layout.addLayout(button_layout)

        self.load_list()

    def load_list(self):
        questions = load_questions(self.quiz_id)
        self.count_label.setText(f"{len(questions)} question(s) saved. (Minimum 10 required before publishing.)")
        self.table.setRowCount(len(questions))
        for row, question in enumerate(questions):
            qtype_mapped = "Multiple Choice Question" if question.get("qtype") == "MCQ" else "True or False"
            self.table.setItem(row, 0, QTableWidgetItem(qtype_mapped))
            self.table.setItem(row, 1, QTableWidgetItem(question.get("text", "")))
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def _question_validation_error(self, data):
        """Returns an error message if data isn't safe to save, else None.
        Also guards against a blank MCQ choice, which used to get silently
        dropped at save time and shift the remaining choices (and therefore
        correct_index) out of alignment with the Correct Answer dropdown."""
        if not data["text"]:
            return "Enter the question text."
        if data["qtype"] == "MCQ":
            if any(not choice for choice in data["choices"]):
                return "Fill in all four choices (A-D) for a Multiple Choice Question."
            if not (0 <= data["correct_index"] < len(data["choices"])):
                return "Select which choice (A-D) is correct."
        else:
            if not (0 <= data["correct_index"] < len(data["choices"])):
                return "Select True or False as the correct answer."
        return None

    def add_question(self):
        dialog = QuestionDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()

        error = self._question_validation_error(data)
        if error:
            QMessageBox.warning(self, "Missing Information", error)
            return

        questions = load_questions(self.quiz_id)
        questions.append(data)
        save_questions(self.quiz_id, questions)
        self.load_list()

    def edit_question(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Question Selected", "Select a question first.")
            return

        questions = load_questions(self.quiz_id)
        if row >= len(questions):
            return

        dialog = QuestionDialog(self, existing=questions[row])
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()

        error = self._question_validation_error(data)
        if error:
            QMessageBox.warning(self, "Missing Information", error)
            return

        questions[row] = data
        save_questions(self.quiz_id, questions)
        self.load_list()

    def delete_question(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Question Selected", "Select a question first.")
            return

        questions = load_questions(self.quiz_id)
        if row >= len(questions):
            return

        reply = QMessageBox.question(self, "Delete Question", "Delete this question?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        questions.pop(row)
        save_questions(self.quiz_id, questions)
        self.load_list()

class QuizManagerWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        apply_app_icon(self)
        self.setWindowTitle("Professor — Quiz Manager")
        self.setMinimumSize(950, 560)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("QUIZ MANAGER"))

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Quiz ID", "Title", "Category", "Max Items", "Time Limit", "Published", "Date Published"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table, 1)

        button_layout = QHBoxLayout()
        create_button = GradientButton("Create Quiz", clicked=self.create_quiz)
        questions_button = QPushButton("Manage Questions", clicked=self.manage_questions)
        publish_button = QPushButton("Publish / Unpublish", clicked=self.toggle_publish)
        delete_button = QPushButton("Delete Quiz", clicked=self.delete_quiz)
        refresh_button = QPushButton("Refresh", clicked=self.load_table)

        for btn in (create_button, questions_button, publish_button, delete_button, refresh_button):
            button_layout.addWidget(btn)

        layout.addLayout(button_layout)
        self.load_table()

    def load_table(self):
        quizzes = load_quizzes()
        self.table.setRowCount(len(quizzes))
        for row, quiz in enumerate(quizzes):
            values = [quiz.get("quiz_id", ""), quiz.get("title", ""), quiz.get("category", ""), quiz.get("max_item", ""), quiz.get("time_limit_minutes", ""), quiz.get("published", ""), quiz.get("date_published", "")]
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def create_quiz(self):
        dialog = QuizDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()

        if not data["title"]:
            QMessageBox.warning(self, "Missing Information", "Quiz title is required.")
            return

        if int(data["max_item"]) < 10:
            QMessageBox.warning(self, "Invalid Quiz", "The system requires at least 10 questions/items.")
            return

        quizzes = load_quizzes()
        if any(quiz["quiz_id"] == data["quiz_id"] for quiz in quizzes):
            QMessageBox.warning(self, "Duplicate Quiz ID", "That Quiz ID already exists.")
            return

        data["published"], data["date_published"] = "no", ""
        quizzes.append(data)
        save_quizzes(quizzes)

        students = load_students()
        if students:
            fields = get_student_fields()
            if data["quiz_id"] not in fields:
                fields.append(data["quiz_id"])
            for student in students:
                if data["quiz_id"] not in student:
                    student[data["quiz_id"]] = ""
            write_csv(STUDENTS_FILE, students, fields)

        self.load_table()
        QMessageBox.information(self, "Quiz Created", f"Quiz '{data['quiz_id']}' created successfully.\nUse \"Manage Questions\" to build its question bank before publishing.")

    def manage_questions(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Quiz Selected", "Select a quiz first.")
            return

        quizzes = load_quizzes()
        if row >= len(quizzes):
            return

        quiz = quizzes[row]
        QuestionManagerWindow(quiz["quiz_id"], quiz["title"], self).exec()

    def toggle_publish(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Quiz Selected", "Select a quiz first.")
            return

        quizzes = load_quizzes()
        if row >= len(quizzes):
            return

        quiz = quizzes[row]
        if quiz["published"] == "yes":
            quiz["published"], quiz["date_published"] = "no", ""
        else:
            question_count = len(load_questions(quiz["quiz_id"]))
            if question_count < 10:
                QMessageBox.warning(self, "Not Enough Questions",
                    f"'{quiz['title']}' only has {question_count} question(s) saved. Add at least 10 via \"Manage Questions\" before publishing.")
                return
            quiz["published"] = "yes"
            quiz["date_published"] = get_spaced_now()

        save_quizzes(quizzes)
        self.load_table()

    def delete_quiz(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Quiz Selected", "Select a quiz first.")
            return

        quizzes = load_quizzes()
        if row >= len(quizzes):
            return

        quiz = quizzes[row]
        reply = QMessageBox.question(self, "Delete Quiz", f"Delete quiz '{quiz['title']}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        quizzes.pop(row)
        save_quizzes(quizzes)
        self.load_table()

# ==========================================
# PROFESSOR GUI MODULES
# ==========================================
class ProfessorLogin(QWidget):
    def __init__(self, launcher_window=None):
        super().__init__()
        apply_app_icon(self)
        self.launcher_window = launcher_window
        self.setWindowTitle("Professor Login — Portal")
        self.resize(480, 300)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 35, 40, 35)
        layout.setSpacing(15)

        title = QLabel("QUIZ SYSTEM — PROFESSOR PORTAL")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.login)
        layout.addWidget(self.password_input)

        login_button = GradientButton("Login", clicked=self.login)
        layout.addWidget(login_button)

        back_button = QPushButton("Back to Portal", clicked=self.back_to_portal)
        back_button.setObjectName("BtnSecondary")
        layout.addWidget(back_button)

        hint = QLabel("Demo password: jabaiskript")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: gray;")
        layout.addWidget(hint)

        layout.addStretch()

    def login(self):
        password = self.password_input.text()
        if password == "":
            QMessageBox.warning(self, "Missing Password", "Please enter the professor password.")
            return
        saved = read_csv(AUTH_CSV)
        if not saved:
            QMessageBox.critical(self, "Authentication Error", "Professor authentication data was not found.")
            return
        if hash_password(password) == saved[0]["password_hash"]:
            self.hide()
            self.dashboard = ProfessorDashboard(self, self.launcher_window)
            self.dashboard.show()
        else:
            QMessageBox.warning(self, "Access Denied", "Incorrect professor password.")

    def back_to_portal(self):
        self.password_input.clear()
        if self.launcher_window:
            self.hide()
            self.launcher_window.show()
        else:
            self.close()

    def closeEvent(self, event):
        if self.launcher_window and not getattr(self.launcher_window, "_closing", False):
            self.launcher_window.show()
        event.accept()

class ProfessorDashboard(QWidget):
    def __init__(self, login_window, launcher_window=None):
        super().__init__()
        apply_app_icon(self)
        self.login_window = login_window
        self.launcher_window = launcher_window
        self.setWindowTitle("Professor Dashboard — Control Panel")
        self.resize(1280, 768)
        self.selected_student_id = None
        self.initUI()
        self.load_grade_table()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(12)

        title = QLabel("PROFESSOR DASHBOARD")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(title)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search Student by Name:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type student name to filter rows dynamically...")
        self.search_input.textChanged.connect(self.filter_students_by_name)
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)

        self.student_table = QTableWidget()
        self.student_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.student_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.student_table.cellClicked.connect(self.select_student)
        main_layout.addWidget(self.student_table, 1)

        row1 = QHBoxLayout()
        row1.addWidget(GradientButton("Add Student", clicked=self.add_student))
        row1.addWidget(QPushButton("Import CSV", clicked=self.import_students))
        row1.addWidget(QPushButton("Delete Student", clicked=self.delete_student))
        row1.addWidget(QPushButton("Export Grade Report", clicked=self.export_grade_report))
        row1.addWidget(QPushButton("View Anti-Cheat Audit Logs", clicked=self.open_audit_logs))
        row1.addWidget(QPushButton("Refresh", clicked=self.load_grade_table))
        main_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QPushButton("Edit Grade", clicked=self.edit_grade))
        row2.addWidget(QPushButton("Reopen Quiz", clicked=self.reopen_quiz))
        row2.addWidget(QPushButton("Lock Grade", clicked=self.lock_grade))
        row2.addWidget(QPushButton("Quiz Manager", clicked=self.quiz_manager))
        row2.addWidget(QPushButton("Logout", clicked=self.logout))
        main_layout.addLayout(row2)

        self.status_label = QLabel("Select a student row to perform student-specific actions.")
        main_layout.addWidget(self.status_label)

    def open_audit_logs(self):
        dlg = GradebookDialog(student_id=self.selected_student_id, parent=self)
        dlg.exec()

    def load_grade_table(self):
        self.search_input.clear()
        self.populate_table_with_data(load_students())

    def populate_table_with_data(self, students):
        quizzes = load_quizzes()
        quiz_title_by_id = {q["quiz_id"]: q.get("title", q["quiz_id"]) for q in quizzes}

        self.student_table.clear()
        if not students:
            self.student_table.setRowCount(0)
            self.student_table.setColumnCount(2)
            self.student_table.setHorizontalHeaderLabels(["Student ID", "Name"])
            return

        all_fields = get_student_fields()
        quiz_columns = [f for f in all_fields if f not in ("student_id", "name") and not f.startswith("locked_")]

        headers = ["Student ID", "Name"] + [quiz_title_by_id.get(qid, qid) for qid in quiz_columns] + ["Total Score", "Remarks"]
        self.student_table.setColumnCount(len(headers))
        self.student_table.setRowCount(len(students))
        self.student_table.setHorizontalHeaderLabels(headers)

        for row_index, student in enumerate(students):
            self.student_table.setItem(row_index, 0, QTableWidgetItem(student.get("student_id", "")))
            self.student_table.setItem(row_index, 1, QTableWidgetItem(student.get("name", "")))

            for col_offset, quiz_id in enumerate(quiz_columns):
                value = student.get(quiz_id, "")
                locked = student.get(f"locked_{quiz_id}", "") == "yes"
                display = value if value else "-"
                if value and locked:
                    display = f"{value} 🔒"
                self.student_table.setItem(row_index, 2 + col_offset, QTableWidgetItem(display))

            total_score, total_possible, remark = compute_total_and_remark(student, quizzes)
            total_col = 2 + len(quiz_columns)
            score_text = f"{total_score} / {total_possible}" if total_possible else "-"
            self.student_table.setItem(row_index, total_col, QTableWidgetItem(score_text))
            self.student_table.setItem(row_index, total_col + 1, QTableWidgetItem(remark))

        self.student_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def filter_students_by_name(self, query):
        query = query.strip().lower()
        students = load_students()
        if not query:
            self.populate_table_with_data(students)
            return
        filtered = [s for s in students if query in s.get("name", "").lower()]
        self.populate_table_with_data(filtered)

    def export_grade_report(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Export Grade Report", "grade_report.csv", "CSV Files (*.csv)")
        if not filename:
            return
        try:
            students = load_students()
            quizzes = load_quizzes()
            fields = get_student_fields() + ["Total Score", "Remarks"]
            
            export_rows = []
            for s in students:
                row_copy = s.copy()
                t_score, t_poss, remark = compute_total_and_remark(s, quizzes)
                row_copy["Total Score"] = f"{t_score}/{t_poss}"
                row_copy["Remarks"] = remark
                export_rows.append(row_copy)
                
            write_csv(filename, export_rows, fields)
            QMessageBox.information(self, "Export Successful", f"Grade report exported successfully to:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export report:\n{e}")

    def select_student(self, row, column):
        item = self.student_table.item(row, 0)
        if item:
            self.selected_student_id = item.text()
            self.status_label.setText(f"Selected Student ID: {self.selected_student_id}")

    def _quiz_picker(self, student, exclude_locked=False):
        quizzes = {q["quiz_id"]: q for q in load_quizzes()}
        options = []
        display_to_id = {}
        for field in student.keys():
            if field in ("student_id", "name") or field.startswith("locked_"):
                continue
            if exclude_locked and student.get(f"locked_{field}", "") == "yes":
                continue
            title = quizzes.get(field, {}).get("title", field)
            label = f"{title} ({field})"
            options.append(label)
            display_to_id[label] = field
        return options, display_to_id

    def add_student(self):
        dialog = AddStudentDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        student_id, name = dialog.get_data()

        if not student_id or not name:
            QMessageBox.warning(self, "Missing Information", "Student ID and Name are required.")
            return

        students, retired = load_students(), load_retired_ids()
        if student_id in {s["student_id"] for s in students}:
            QMessageBox.warning(self, "Duplicate ID", "This Student ID already exists.")
            return
        if student_id in {s["student_id"] for s in retired}:
            QMessageBox.warning(self, "Retired ID", "This Student ID was previously deleted and cannot be reused.")
            return

        new_student = {"student_id": student_id, "name": name}
        quizzes = load_quizzes()
        for quiz in quizzes:
            if quiz["quiz_id"] not in new_student:
                new_student[quiz["quiz_id"]] = ""

        students.append(new_student)
        existing_fields = get_student_fields()

        for quiz in quizzes:
            if quiz["quiz_id"] not in existing_fields:
                existing_fields.append(quiz["quiz_id"])

        for student in students:
            for field in existing_fields:
                if field not in student:
                    student[field] = ""

        write_csv(STUDENTS_FILE, students, existing_fields)
        self.load_grade_table()
        QMessageBox.information(self, "Student Added", f"{name} has been added successfully.")

    def import_students(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Select Student CSV", "", "CSV Files (*.csv)")
        if not filename:
            return

        try:
            with open(filename, "r", newline="", encoding="utf-8-sig") as file:
                imported = list(csv.DictReader(file))
            if not imported:
                QMessageBox.warning(self, "Empty File", "The selected CSV file has no student records.")
                return

            if not {"student_id", "name"}.issubset(imported[0].keys()):
                QMessageBox.warning(self, "Invalid CSV", "The CSV must contain student_id and name columns.")
                return

            students, retired = load_students(), load_retired_ids()
            active_ids = {s["student_id"] for s in students}
            retired_ids = {s["student_id"] for s in retired}
            quizzes, fields = load_quizzes(), get_student_fields()
            added, rejected = 0, []

            for new_student in imported:
                student_id = new_student["student_id"].strip()
                name = new_student["name"].strip()
                if not student_id or not name or student_id in active_ids or student_id in retired_ids:
                    rejected.append(student_id if student_id else "(blank ID/name)")
                    continue

                record = {"student_id": student_id, "name": name}
                for quiz in quizzes:
                    record[quiz["quiz_id"]] = ""
                    if quiz["quiz_id"] not in fields:
                        fields.append(quiz["quiz_id"])

                students.append(record)
                active_ids.add(student_id)
                added += 1

            for student in students:
                for field in fields:
                    if field not in student:
                        student[field] = ""

            write_csv(STUDENTS_FILE, students, fields)
            self.load_grade_table()
            message = f"{added} student(s) imported."
            if rejected:
                message += "\n\nRejected IDs:\n" + "\n".join(rejected)
            QMessageBox.information(self, "Import Complete", message)

        except Exception as error:
            QMessageBox.critical(self, "Import Error", f"Could not import the CSV.\n\n{error}")

    def edit_grade(self):
        if not self.selected_student_id:
            QMessageBox.warning(self, "No Student Selected", "Select a student first.")
            return

        students = load_students()
        student = next((item for item in students if item["student_id"] == self.selected_student_id), None)
        if student is None:
            return

        options, display_to_id = self._quiz_picker(student)
        if not options:
            QMessageBox.information(self, "No Quizzes", "There are no quiz grade columns yet.")
            return

        label, ok = QInputDialog.getItem(self, "Select Quiz", "Quiz:", options, 0, False)
        if not ok:
            return
        quiz_id = display_to_id[label]

        current = student.get(quiz_id, "")
        lock_field = f"locked_{quiz_id}"
        if student.get(lock_field, "") == "yes":
            QMessageBox.warning(self, "Grade Locked", "This grade has been permanently locked.")
            return

        score, ok = QInputDialog.getInt(self, "Edit Grade", f"Enter score for {label}:", int(current) if current.isdigit() else 0, 0, 999999, 1)
        if not ok:
            return

        for record in students:
            if record["student_id"] == self.selected_student_id:
                record[quiz_id] = str(score)
                break

        fields = get_student_fields()
        if lock_field not in fields:
            fields.append(lock_field)

        for record in students:
            if lock_field not in record:
                record[lock_field] = ""

        write_csv(STUDENTS_FILE, students, fields)
        self.load_grade_table()
        QMessageBox.information(self, "Grade Updated", "The student's grade has been updated.")

    def delete_student(self):
        if not self.selected_student_id:
            QMessageBox.warning(self, "No Student Selected", "Select a student first.")
            return

        reply = QMessageBox.question(self, "Delete Student", f"Delete Student ID {self.selected_student_id}?\n\nThe ID will be retired and cannot be reused.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        students = load_students()
        deleted_student, remaining = None, []
        for student in students:
            if student["student_id"] == self.selected_student_id:
                deleted_student = student
            else:
                remaining.append(student)

        if deleted_student is None:
            return

        save_students(remaining)

        retired = load_retired_ids()
        retired.append({"student_id": self.selected_student_id, "date_retired": get_spaced_now()})
        save_retired_ids(retired)

        self.selected_student_id = None
        self.load_grade_table()
        QMessageBox.information(self, "Student Deleted", "Student deleted and ID retired.")

    def reopen_quiz(self):
        if not self.selected_student_id:
            QMessageBox.warning(self, "No Student Selected", "Select a student first.")
            return

        students = load_students()
        student = next((item for item in students if item["student_id"] == self.selected_student_id), None)
        if not student:
            return

        options, display_to_id = self._quiz_picker(student, exclude_locked=True)
        if not options:
            QMessageBox.information(self, "No Quizzes", "There are no reopenable quiz columns.")
            return

        label, ok = QInputDialog.getItem(self, "Reopen Quiz", "Select quiz:", options, 0, False)
        if not ok:
            return
        quiz_id = display_to_id[label]

        for record in students:
            if record["student_id"] == self.selected_student_id:
                record[quiz_id] = ""
                break

        save_students(students)
        self.load_grade_table()
        QMessageBox.information(self, "Quiz Reopened", "The quiz is now available again for this student.")

    def lock_grade(self):
        if not self.selected_student_id:
            QMessageBox.warning(self, "No Student Selected", "Select a student first.")
            return

        students = load_students()
        student = next((item for item in students if item["student_id"] == self.selected_student_id), None)
        if not student:
            return

        options, display_to_id = self._quiz_picker(student, exclude_locked=True)
        if not options:
            return

        label, ok = QInputDialog.getItem(self, "Lock Grade", "Select quiz:", options, 0, False)
        if not ok:
            return
        quiz_id = display_to_id[label]

        if student.get(quiz_id, "") == "":
            QMessageBox.warning(self, "No Grade", "This quiz has no grade yet.")
            return

        lock_field = f"locked_{quiz_id}"
        for record in students:
            if record["student_id"] == self.selected_student_id:
                record[lock_field] = "yes"

        fields = get_student_fields()
        if lock_field not in fields:
            fields.append(lock_field)

        for record in students:
            if lock_field not in record:
                record[lock_field] = ""

        write_csv(STUDENTS_FILE, students, fields)
        self.load_grade_table()
        QMessageBox.information(self, "Grade Locked", "The grade is now permanently locked.")

    def quiz_manager(self):
        QuizManagerWindow(self).exec()
        self.load_grade_table()

    def logout(self):
        reply = QMessageBox.question(
            self,
            "Logout",
            "Return to the main role selection portal?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.close()

    def closeEvent(self, event):
        self.login_window.password_input.clear()
        if self.launcher_window:
            self.login_window.hide()
            self.launcher_window.show()
        else:
            self.login_window.show()
        event.accept()

# ==========================================
# STUDENT GUI MODULES
# ==========================================
class StudentLogin(QWidget):
    def __init__(self, launcher_window=None):
        super().__init__()
        apply_app_icon(self)
        self.launcher_window = launcher_window
        self.setWindowTitle("Student Login — Portal")
        self.resize(480, 260)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 35, 40, 35)
        layout.setSpacing(15)

        title = QLabel("QUIZ SYSTEM — STUDENT PORTAL")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        layout.addWidget(QLabel("Student ID:"))
        self.id_input = QLineEdit()
        self.id_input.returnPressed.connect(self.login)
        layout.addWidget(self.id_input)

        continue_button = GradientButton("Continue", clicked=self.login)
        layout.addWidget(continue_button)

        back_button = QPushButton("Back to Portal", clicked=self.back_to_portal)
        back_button.setObjectName("BtnSecondary")
        layout.addWidget(back_button)

        layout.addStretch()

    def login(self):
        student_id = self.id_input.text().strip()
        if not student_id:
            QMessageBox.warning(self, "Missing ID", "Please enter your Student ID.")
            return

        retired_ids = {row["student_id"] for row in load_retired_ids()}
        if student_id in retired_ids:
            QMessageBox.warning(self, "Access Denied", "This Student ID is no longer active.")
            return

        student = next((s for s in load_students() if s["student_id"] == student_id), None)
        if student is None:
            QMessageBox.warning(self, "Not Found", "That Student ID was not found.")
            return

        result = start_session(student_id)
        if result == "conflict":
            QMessageBox.warning(self, "Already Logged In",
                "This Student ID is already active on another device. Ask your professor if this wasn't you.")
            return

        self.id_input.clear()
        self.hide()
        self.dashboard = StudentDashboard(student, self, self.launcher_window)
        self.dashboard.show()

    def back_to_portal(self):
        self.id_input.clear()
        if self.launcher_window:
            self.hide()
            self.launcher_window.show()
        else:
            self.close()

    def closeEvent(self, event):
        if self.launcher_window and not getattr(self.launcher_window, "_closing", False):
            self.launcher_window.show()
        event.accept()

class StudentDashboard(QWidget):
    def __init__(self, student, login_window, launcher_window=None):
        super().__init__()
        apply_app_icon(self)
        self.student = student
        self.login_window = login_window
        self.launcher_window = launcher_window
        self.setWindowTitle("Student Dashboard — Portal")
        self.resize(800, 560)
        self.selected_category = None
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(12)

        greeting = QLabel(f"Welcome, {self.student.get('name', 'Student')} (ID: {self.student.get('student_id', '')})")
        greeting.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(greeting)

        main_layout.addWidget(QLabel("Choose a category:"))
        category_row = QGridLayout()
        for i, category in enumerate(CATEGORIES):
            btn = QPushButton(category, clicked=lambda checked, c=category: self.show_category(c))
            category_row.addWidget(btn, 0, i)
        main_layout.addLayout(category_row)

        main_layout.addWidget(QLabel("Available quizzes in this category:"))
        self.quiz_list = QListWidget()
        self.quiz_list.itemDoubleClicked.connect(self.open_selected_quiz)
        main_layout.addWidget(self.quiz_list, 1)

        action_row = QHBoxLayout()
        action_row.addWidget(GradientButton("Take Selected Quiz", clicked=self.open_selected_quiz))
        action_row.addWidget(QPushButton("My Grades", clicked=self.open_my_grades))
        action_row.addWidget(QPushButton("Logout", clicked=self.logout))
        main_layout.addLayout(action_row)
        apply_fade_in(self)

    def show_category(self, category):
        self.selected_category = category
        self.load_quiz_list()

    def load_quiz_list(self):
        self.quiz_list.clear()
        if not self.selected_category:
            return

        fresh_student = next((s for s in load_students() if s["student_id"] == self.student["student_id"]), self.student)
        self.student = fresh_student

        quizzes = [q for q in load_quizzes() if q.get("published") == "yes" and q.get("category") == self.selected_category]
        available = [q for q in quizzes if self.student.get(q["quiz_id"], "") == ""]

        if not available:
            self.quiz_list.addItem("No available quizzes in this category right now.")
            return

        for quiz in available:
            item = QListWidgetItem(f"{quiz['title']}  ({quiz['max_item']} items, {quiz['time_limit_minutes']} min)")
            item.setData(1000, quiz["quiz_id"])
            self.quiz_list.addItem(item)

    def open_selected_quiz(self):
        item = self.quiz_list.currentItem()
        if item is None or item.data(1000) is None:
            QMessageBox.information(self, "No Quiz Selected", "Select or double-click an available quiz first.")
            return

        quiz_id = item.data(1000)
        quiz = next(q for q in load_quizzes() if q["quiz_id"] == quiz_id)
        questions = load_questions(quiz_id)

        if not questions:
            QMessageBox.warning(self, "No Questions", "This quiz has no questions yet. Tell your professor.")
            return

        prompt = FullscreenPromptDialog(quiz["title"], quiz.get("time_limit_minutes", "10"), str(len(questions)), self)
        if prompt.exec() == QDialog.DialogCode.Accepted:
            self.hide()
            self.take_quiz_window = TakeQuizWindow(self.student, quiz, questions, self)
            self.take_quiz_window.showFullScreen()

    def open_my_grades(self):
        fresh_student = next((s for s in load_students() if s["student_id"] == self.student["student_id"]), self.student)
        self.student = fresh_student
        self.grades_window = MyGradesWindow(self.student, self)
        self.grades_window.exec()

    def logout(self):
        reply = QMessageBox.question(
            self,
            "Logout",
            "Return to the main role selection portal?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.close()

    def closeEvent(self, event):
        end_session(self.student["student_id"])
        if self.launcher_window:
            self.login_window.hide()
            self.launcher_window.show()
        else:
            self.login_window.show()
        event.accept()

class MyGradesWindow(QDialog):
    def __init__(self, student, parent=None):
        super().__init__(parent)
        apply_app_icon(self)
        self.student = student
        self.setWindowTitle(f"My Grades — {student.get('name', '')}")
        self.setMinimumSize(520, 460)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        header = QLabel(f"{self.student.get('name', '')} (ID: {self.student.get('student_id', '')})")
        header.setStyleSheet("font-size: 15px; font-weight: bold;")
        layout.addWidget(header)

        quizzes = load_quizzes()
        grades_list = QListWidget()

        any_grade = False
        for quiz in quizzes:
            value = self.student.get(quiz["quiz_id"], "")
            if value == "":
                continue
            any_grade = True
            locked = self.student.get(f"locked_{quiz['quiz_id']}", "") == "yes"
            lock_text = " 🔒" if locked else ""
            grades_list.addItem(f"{quiz['title']} ({quiz['category']}): {value} / {quiz.get('max_item', '?')}{lock_text}")

        if not any_grade:
            grades_list.addItem("No quizzes taken yet.")
        layout.addWidget(grades_list, 1)

        total_score, total_possible, remark = compute_total_and_remark(self.student, quizzes)
        summary_text = f"Overall: {total_score} / {total_possible}  —  Remark: {remark}" if total_possible else "Overall: No grades yet"
        summary = QLabel(summary_text)
        summary.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(summary)

        close_button = QPushButton("Close", clicked=self.accept)
        layout.addWidget(close_button)

class TakeQuizWindow(QWidget):
    def __init__(self, student, quiz, questions, dashboard):
        super().__init__()
        apply_app_icon(self)
        self.student = student
        self.quiz = quiz
        self.questions = questions
        self.dashboard = dashboard
        self.index = 0
        self.answers = {}
        self.finished = False
        self.tab_switches = 0
        self.is_fully_initialized = False

        self.seconds_left = int(quiz.get("time_limit_minutes", 10)) * 60
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)

        self.setWindowTitle(f"Taking Proctored Quiz: {quiz['title']}")
        self.installEventFilter(self)
        self.initUI()
        self.render_question()

        QTimer.singleShot(1500, self.mark_initialized)

    def mark_initialized(self):
        self.is_fully_initialized = True

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)

        top_row = QHBoxLayout()
        self.timer_label = QLabel()
        self.timer_label.setStyleSheet("font-weight: bold; color: #EF4444; font-size: 16px;")
        
        self.warning_label = QLabel("🛡️ Anti-Cheat Active — Tab switching or focus shifts are strictly recorded.")
        self.warning_label.setStyleSheet("font-weight: bold; color: #10B981; font-size: 13px;")
        
        top_row.addWidget(self.warning_label)
        top_row.addStretch()
        top_row.addWidget(self.timer_label)
        layout.addLayout(top_row)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.progress_label = QLabel()
        self.progress_label.setWordWrap(True)
        self.progress_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(self.progress_label)

        self.choice_group = QButtonGroup(self)
        self.choice_radios = []
        for i in range(4):
            radio = QRadioButton()
            radio.setStyleSheet("font-size: 14px; padding: 10px;")
            self.choice_group.addButton(radio, i)
            self.choice_radios.append(radio)
            layout.addWidget(radio)

        layout.addStretch()

        nav_box = QHBoxLayout()
        self.btn_prev = QPushButton("◄ Previous")
        self.btn_prev.setObjectName("BtnSecondary")
        self.btn_prev.clicked.connect(self.prev_question)

        self.btn_next = QPushButton("Next Question ►")
        self.btn_next.clicked.connect(self.next_question)

        self.btn_submit = QPushButton("Submit Quiz", clicked=self.confirm_submit)
        self.btn_submit.setObjectName("BtnDanger")

        nav_box.addWidget(self.btn_prev)
        nav_box.addWidget(self.btn_next)
        nav_box.addWidget(self.btn_submit)
        layout.addLayout(nav_box)

    def eventFilter(self, obj, event):
        if obj == self and not self.finished and self.isVisible():
            if event.type() in [QEvent.Type.WindowDeactivate, QEvent.Type.Hide]:
                if self.is_fully_initialized:
                    self.tab_switches += 1
                    self.warning_label.setText(f"⚠️ Focus Loss Detected! (Switch count: {self.tab_switches})")
                    self.warning_label.setStyleSheet("font-weight: bold; color: #EF4444; font-size: 13px;")
                    log_conflict(self.student["student_id"], f"Tab Switch / Window Focus Loss #{self.tab_switches}")
        return super().eventFilter(obj, event)

    def render_question(self):
        total = len(self.questions)
        self.progress_bar.setValue(int(((self.index + 1) / total) * 100))
        q = self.questions[self.index]
        q_type_label = "Multiple Choice" if q.get("qtype") == "MCQ" else "True/False"
        self.progress_label.setText(f"[{q_type_label}] Q{self.index + 1}/{total}: {q['text']}")

        opts = q.get("choices", [])
        self.choice_group.setExclusive(False)
        for i, radio in enumerate(self.choice_radios):
            if i < len(opts):
                radio.setText(opts[i])
                radio.setVisible(True)
                radio.setChecked(False)
            else:
                radio.setVisible(False)
        self.choice_group.setExclusive(True)

        if self.index in self.answers:
            self.choice_radios[self.answers[self.index]].setChecked(True)

        self.btn_prev.setEnabled(self.index > 0)
        self.btn_next.setEnabled(self.index < total - 1)

    def tick(self):
        self.seconds_left -= 1
        minutes, seconds = divmod(max(self.seconds_left, 0), 60)
        self.timer_label.setText(f"⏱️ {minutes:02d}:{seconds:02d}")
        if self.seconds_left <= 0:
            self.timer.stop()
            QMessageBox.information(self, "Time's Up", "Time is up — submitting what you've answered so far.")
            self.finish_quiz(quit_early=False)

    def prev_question(self):
        checked_id = self.choice_group.checkedId()
        if checked_id != -1:
            self.answers[self.index] = checked_id
        if self.index > 0:
            self.index -= 1
            self.render_question()

    def next_question(self):
        checked_id = self.choice_group.checkedId()
        if checked_id != -1:
            self.answers[self.index] = checked_id

        if self.index + 1 < len(self.questions):
            self.index += 1
            self.render_question()

    def confirm_submit(self):
        checked_id = self.choice_group.checkedId()
        if checked_id != -1:
            self.answers[self.index] = checked_id

        unanswered = [i + 1 for i in range(len(self.questions)) if i not in self.answers]
        if unanswered:
            un_str = ", ".join(map(str, unanswered[:10]))
            if len(unanswered) > 10:
                un_str += f" (+{len(unanswered) - 10} more)"
            QMessageBox.warning(
                self, "Unanswered Questions", 
                f"You still have unanswered items: #{un_str}\n\nPlease complete all items before submitting!"
            )
            return

        reply = QMessageBox.question(
            self, "Confirm Submission", 
            "Are you sure you want to finalize and submit your quiz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.finish_quiz(quit_early=False)

    def finish_quiz(self, quit_early):
        if self.finished:
            return
        self.finished = True
        self.timer.stop()

        correct = 0
        breakdown = []
        for i, q in enumerate(self.questions):
            chosen = self.answers.get(i)
            is_correct = chosen == q.get("correct_index", 0)
            correct += 1 if is_correct else 0
            choices = q.get("choices", [])
            chosen_text = choices[chosen] if (chosen is not None and chosen < len(choices)) else "(no answer)"
            c_idx = q.get("correct_index", 0)
            correct_text = choices[c_idx] if c_idx < len(choices) else "N/A"
            breakdown.append((q.get("text", ""), chosen_text, correct_text, is_correct))

        students = load_students()
        for record in students:
            if record["student_id"] == self.student["student_id"]:
                record[self.quiz["quiz_id"]] = str(correct)
        fields = get_student_fields()
        if self.quiz["quiz_id"] not in fields:
            fields.append(self.quiz["quiz_id"])
        for record in students:
            if self.quiz["quiz_id"] not in record:
                record[self.quiz["quiz_id"]] = ""
        write_csv(STUDENTS_FILE, students, fields)

        sessions = load_sessions()
        sessions.append({
            "session_id": f"SESS_{len(sessions) + 1:04d}",
            "student_id": self.student["student_id"],
            "quiz_id": self.quiz["quiz_id"],
            "score": str(correct),
            "date_taken": get_spaced_now(),
            "tab_switches": str(self.tab_switches),
            "remarks": calculate_remarks(correct, len(self.questions)),
            "device_id": get_device_id(),
            "started_at": get_spaced_now()
        })
        save_sessions(sessions)

        self.showNormal()
        self.result_window = ResultWindow(self.quiz["title"], correct, len(self.questions), self.tab_switches, breakdown, self.dashboard)
        self.result_window.show()
        self.close()

    def closeEvent(self, event):
        if not self.finished:
            self.finish_quiz(quit_early=True)
        event.accept()

class ResultWindow(QWidget):
    def __init__(self, quiz_title, correct, total, tab_switches, breakdown, dashboard):
        super().__init__()
        apply_app_icon(self)
        self.dashboard = dashboard
        self.setWindowTitle(f"Results — {quiz_title}")
        self.resize(720, 520)
        self.initUI(correct, total, tab_switches, breakdown)

    def initUI(self, correct, total, tab_switches, breakdown):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        
        score_lbl = QLabel(f"<b>Final Score: {correct}/{total}</b> | Focus Shifts: {tab_switches}")
        score_lbl.setStyleSheet("font-size: 16px; color: #D97706;")
        layout.addWidget(score_lbl)

        results_list = QListWidget()
        for text, chosen_text, correct_text, is_correct in breakdown:
            mark = "CORRECT" if is_correct else "WRONG"
            results_list.addItem(f"[{mark}] {text}\n   Your answer: {chosen_text} | Correct answer: {correct_text}\n")
        layout.addWidget(results_list, 1)

        back_button = GradientButton("Back to Dashboard", clicked=self.back_to_dashboard)
        layout.addWidget(back_button)

    def back_to_dashboard(self):
        self.close()

    def closeEvent(self, event):
        if self.dashboard is not None:
            self.dashboard.load_quiz_list()
            self.dashboard.show()
        event.accept()

# ==========================================
# MAIN PORTAL LAUNCHER
# ==========================================
class MainLauncher(QWidget):
    def __init__(self):
        super().__init__()
        apply_app_icon(self)
        self.setWindowTitle("Quiz System — Unified Portal Launcher")
        self.resize(480, 300)
        self._closing = False
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 35, 40, 35)
        layout.setSpacing(15)

        title = QLabel("QUIZ SYSTEM PORTAL")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #D97706;")
        layout.addWidget(title)

        subtitle = QLabel("Please select your role to continue:")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        prof_button = GradientButton("Professor Portal", clicked=self.open_professor)
        layout.addWidget(prof_button)

        student_button = GradientButton("Student Portal", clicked=self.open_student)
        layout.addWidget(student_button)

        layout.addStretch()
        self.show()

    def _reuse_or_create(self, attr_name, factory):
        old = getattr(self, attr_name, None)
        if old is not None:
            try:
                old.show()
                old.raise_()
                return
            except RuntimeError:
                pass
        window = factory()
        setattr(self, attr_name, window)
        window.show()

    def open_professor(self):
        self.hide()
        self._reuse_or_create("prof_login", lambda: ProfessorLogin(launcher_window=self))

    def open_student(self):
        self.hide()
        self._reuse_or_create("student_login", lambda: StudentLogin(launcher_window=self))

    def closeEvent(self, event):
        self._closing = True
        app = QApplication.instance()
        if app is not None:
            app.quit()
        event.accept()

# ==========================================
# ENTRY POINT
# ==========================================
def main():
    # Force Windows to treat this app as a distinct process on the taskbar
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("group4.quizsystem.app.1")
    except Exception:
        pass

    ensure_files()
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)

    if os.path.exists(ICON_PATH):
        app.setWindowIcon(QIcon(ICON_PATH))

    launcher = MainLauncher()
    launcher.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()