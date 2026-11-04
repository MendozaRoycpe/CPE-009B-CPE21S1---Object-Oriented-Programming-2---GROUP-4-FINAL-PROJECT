"""QUIZ SYSTEM — MAIN APPLICATION

PURPOSE
  Entry point, shared CSV/JSON data layer, quiz validation/randomization, student-session tracking,
  reusable visual helpers, and role-selection launcher for the professor/student GUI modules.

RUN / DEPENDENCIES
  Run `python main.py` from this folder. Requires Python and PyQt6. Keep this file beside
  professor_system.py and student_system.py. Data files are stored under data/.

FUNCTION AND METHOD INDEX
  Line numbers refer to this file, including this documentation block.
  apply_app_icon: line 136 (function)
  hash_password: line 145 (function)
  get_device_id: line 150 (function)
  get_spaced_now: line 155 (function)
  now_str: line 160 (function)
  calculate_remarks: line 165 (function)
  apply_fade_in: line 179 (function)
  read_csv: line 192 (function)
  write_csv: line 204 (function)
  get_student_fields: line 216 (function)
  quiz_columns: line 225 (function)
  load_students: line 230 (function)
  save_students: line 234 (function)
  load_retired_ids: line 244 (function)
  save_retired_ids: line 248 (function)
  load_quizzes: line 252 (function)
  save_quizzes: line 256 (function)
  find_quiz: line 260 (function)
  questions_path: line 265 (function)
  load_questions: line 271 (function)
  save_questions: line 284 (function)
  count_questions: line 290 (function)
  required_questions: line 294 (function)
  validate_question: line 303 (function)
  generate_quiz_id: line 331 (function)
  ensure_quiz_column: line 344 (function)
  remove_quiz_column: line 355 (function)
  delete_quiz_data: line 366 (function)
  set_student_field: line 375 (function)
  select_quiz_questions: line 392 (function)
  compute_total_and_remark: line 415 (function)
  load_sessions: line 443 (function)
  save_sessions: line 447 (function)
  load_conflicts: line 455 (function)
  save_conflicts: line 459 (function)
  log_conflict: line 463 (function)
  clear_conflicts: line 474 (function)
  start_session: line 478 (function)
  end_session: line 504 (function)
  end_all_sessions_on_this_device: line 516 (function)
  is_default_password: line 522 (function)
  set_professor_password: line 527 (function)
  ensure_files: line 535 (function)
  build_spinbox_arrows: line 589 (function)
  table_cell: line 614 (function)
  GradientButton: line 624 (class)
  GradientButton.__init__: line 628 (method)
  GradientButton.enterEvent: line 644 (method)
  GradientButton.leaveEvent: line 648 (method)
  GradientButton.mousePressEvent: line 652 (method)
  GradientButton._tick: line 662 (method)
  GradientButton.paintEvent: line 674 (method)
  MainLauncher: line 756 (class)
  MainLauncher.__init__: line 758 (method)
  MainLauncher.initUI: line 766 (method)
  MainLauncher._reuse_or_create: line 781 (method)
  MainLauncher.open_professor: line 794 (method)
  MainLauncher.open_student: line 799 (method)
  MainLauncher.closeEvent: line 804 (method)
  main: line 812 (function)
MAINTENANCE NOTES
  Back up data/ before replacing code or testing destructive actions. CSV files are not a
  transactional database; simultaneous writes from multiple computers can overwrite changes.
  Student IDs are retired after deletion. Deleting a quiz removes its question bank, grade column,
  and lock column. Starter records are created only when the corresponding files are first created.
"""
import sys
import os
import csv
import json
import copy
import random
import socket
import hashlib
import ctypes
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidgetItem,
    QSizePolicy, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRectF, QPointF
from PyQt6.QtGui import (
    QIcon, QColor, QPainter, QLinearGradient, QFont, QPainterPath,
    QBrush, QPen, QPixmap, QPolygonF
)

# ---------------------------------------------------------------------------
# Paths 
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
QUESTIONS_DIR = os.path.join(DATA_DIR, "questions")
STUDENTS_CSV = os.path.join(DATA_DIR, "students.csv")
RETIRED_CSV = os.path.join(DATA_DIR, "retired_ids.csv")
QUIZZES_CSV = os.path.join(DATA_DIR, "quizzes.csv")
AUTH_CSV = os.path.join(DATA_DIR, "professor_auth.csv")
SESSIONS_CSV = os.path.join(DATA_DIR, "sessions.csv")
CONFLICTS_CSV = os.path.join(DATA_DIR, "session_conflicts.csv")
ICON_PATH = os.path.join(BASE_DIR, "TIPlogo.ico")

STUDENT_FIELDS = ["student_id", "name"]
QUIZ_FIELDS = [
    "quiz_id", "title", "category", "max_item", "time_limit_minutes",
    "published", "date_published"
]

SESSION_FIELDS = [
    "session_id", "student_id", "quiz_id", "score", "date_taken",
    "remarks", "device_id", "started_at"
]
CONFLICT_FIELDS = ["student_id", "device_id", "attempted_at", "issue_type"]
CATEGORIES = ["English", "Science", "Math", "Computer"]
CATEGORY_PREFIXES = {
    "English": "100",
    "Science": "200",
    "Math": "300",
    "Computer": "400",
}
MIN_QUESTIONS_PER_QUIZ = 10
DEFAULT_PROFESSOR_PASSWORD = "jabaiskript"


def apply_app_icon(widget: QWidget):
    """Apply the project icon when TIPlogo.ico exists."""
    if os.path.exists(ICON_PATH):
        widget.setWindowIcon(QIcon(ICON_PATH))


# ---------------------------------------------------------------------------
# Shared utilities and CSV functions
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    """Return the SHA-256 digest used by the professor login."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_device_id() -> str:
    """Return the current computer's hostname for basic session tracking."""
    return socket.gethostname()


def get_spaced_now() -> str:
    """Return local time in the common CSV timestamp format."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def now_str() -> str:
    """Alias retained for compatibility with the shared data-layer version."""
    return get_spaced_now()


def calculate_remarks(score: int, total: int) -> str:
    """Convert a score percentage into the application's remark label."""
    if total <= 0:
        return "No grades yet"
    percentage = (score / total) * 100
    if percentage >= 90:
        return "Excellent"
    if percentage >= 75:
        return "Good"
    if percentage >= 50:
        return "Fair"
    return "Poor"


def apply_fade_in(widget, duration=350):
    """Fade a widget in when the caller uses this optional visual helper."""
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
    """Read a CSV into dictionaries; tolerate UTF-8 BOMs and short rows."""
    if not os.path.isfile(filename):
        return []
    with open(filename, "r", newline="", encoding="utf-8-sig") as file:
        return [
            {key: (value if value is not None else "")
             for key, value in row.items() if key is not None}
            for row in csv.DictReader(file)
        ]


def write_csv(filename: str, rows: list, fieldnames: list):
    """Write dictionaries to CSV, creating parent folders if needed."""
    parent = os.path.dirname(os.path.abspath(filename))
    os.makedirs(parent, exist_ok=True)
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file, fieldnames=list(fieldnames), extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(rows)


def get_student_fields() -> list:
    """Read the students.csv header so dynamic quiz/lock columns are preserved."""
    if not os.path.isfile(STUDENTS_CSV):
        return STUDENT_FIELDS.copy()
    with open(STUDENTS_CSV, "r", newline="", encoding="utf-8-sig") as file:
        header = next(csv.reader(file), None)
    return header if header else STUDENT_FIELDS.copy()


def quiz_columns(fields: list) -> list:
    """Return dynamic grade columns, excluding identity and lock columns."""
    return [f for f in fields if f not in STUDENT_FIELDS and not f.startswith("locked_")]


def load_students() -> list:
    return read_csv(STUDENTS_CSV)


def save_students(students: list, fields=None):
    """Save student rows without discarding existing dynamic columns."""
    output_fields = list(fields) if fields else get_student_fields()
    for student in students:
        for field in student:
            if field not in output_fields:
                output_fields.append(field)
    write_csv(STUDENTS_CSV, students, output_fields)


def load_retired_ids() -> list:
    return read_csv(RETIRED_CSV)


def save_retired_ids(rows: list):
    write_csv(RETIRED_CSV, rows, ["student_id", "date_retired"])


def load_quizzes() -> list:
    return read_csv(QUIZZES_CSV)


def save_quizzes(quizzes: list):
    write_csv(QUIZZES_CSV, quizzes, QUIZ_FIELDS)


def find_quiz(quiz_id: str):
    """Find a quiz by ID, or return None."""
    return next((q for q in load_quizzes() if q.get("quiz_id") == quiz_id), None)


def questions_path(quiz_id: str) -> str:
    """Return the JSON path for a quiz question bank."""
    os.makedirs(QUESTIONS_DIR, exist_ok=True)
    return os.path.join(QUESTIONS_DIR, f"{quiz_id}.json")


def load_questions(quiz_id: str) -> list:
    """Load a quiz question bank; malformed or missing files return []."""
    path = questions_path(quiz_id)
    if not os.path.isfile(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_questions(quiz_id: str, questions: list):
    """Save a quiz's question bank as UTF-8 JSON."""
    with open(questions_path(quiz_id), "w", encoding="utf-8") as file:
        json.dump(questions, file, indent=2, ensure_ascii=False)


def count_questions(quiz_id: str) -> int:
    return len(load_questions(quiz_id))


def required_questions(quiz: dict) -> int:
    """Publishing requires at least ten questions and at least max_item."""
    try:
        maximum = int(quiz.get("max_item", 0) or 0)
    except (TypeError, ValueError):
        maximum = 0
    return max(MIN_QUESTIONS_PER_QUIZ, maximum)


def validate_question(question: dict) -> str:
    """Return a validation message, or an empty string for a valid question."""
    text = str(question.get("text", question.get("question", ""))).strip()
    if not text:
        return "Enter the question text."
    choices = question.get("choices", question.get("options", []))
    qtype = question.get("qtype", "MCQ")
    if qtype == "MCQ":
        if not isinstance(choices, list) or len(choices) != 4:
            return "A Multiple Choice question must have exactly four options."
        if any(not isinstance(choice, str) or not choice.strip() for choice in choices):
            return "Fill in all four Multiple Choice options."
        if len({choice.strip().casefold() for choice in choices}) != 4:
            return "Each Multiple Choice option must be different."
    elif qtype == "TF":
        if choices != ["True", "False"]:
            return "A True or False question must have exactly True and False."
    else:
        return "Choose a supported question type."
    try:
        index = int(question.get("correct_index", question.get("correct_option_index", -1)))
    except (TypeError, ValueError):
        return "Pick the correct answer."
    if not 0 <= index < len(choices):
        return "Pick the correct answer."
    return ""


def generate_quiz_id(category: str) -> str:
    """Generate the next numeric quiz ID using the configured category prefix."""
    prefix = CATEGORY_PREFIXES.get(category, "100")
    highest = 0
    for quiz in load_quizzes():
        quiz_id = str(quiz.get("quiz_id", ""))
        if quiz_id.startswith(prefix):
            suffix = quiz_id[len(prefix):]
            if suffix.isdigit():
                highest = max(highest, int(suffix))
    return f"{prefix}{highest + 1}"


def ensure_quiz_column(quiz_id: str):
    """Add a blank grade column for a quiz without losing existing columns."""
    fields = get_student_fields()
    students = load_students()
    if quiz_id not in fields:
        fields.append(quiz_id)
    for student in students:
        student.setdefault(quiz_id, "")
    write_csv(STUDENTS_CSV, students, fields)


def remove_quiz_column(quiz_id: str):
    """Remove a quiz's grade and lock columns from every student row."""
    lock_field = f"locked_{quiz_id}"
    fields = [field for field in get_student_fields() if field not in (quiz_id, lock_field)]
    students = load_students()
    for student in students:
        student.pop(quiz_id, None)
        student.pop(lock_field, None)
    write_csv(STUDENTS_CSV, students, fields)


def delete_quiz_data(quiz_id: str):
    """Delete quiz metadata, its question bank, and its grade/lock columns."""
    save_quizzes([q for q in load_quizzes() if q.get("quiz_id") != quiz_id])
    path = questions_path(quiz_id)
    if os.path.isfile(path):
        os.remove(path)
    remove_quiz_column(quiz_id)


def set_student_field(student_id: str, field: str, value):
    """Set a field for one student; return False when the ID does not exist."""
    fields = get_student_fields()
    students = load_students()
    if field not in fields:
        fields.append(field)
    found = False
    for student in students:
        student.setdefault(field, "")
        if student.get("student_id") == student_id:
            student[field] = value
            found = True
    if found:
        write_csv(STUDENTS_CSV, students, fields)
    return found


def select_quiz_questions(quiz: dict) -> list:
    """Randomize the selected quiz questions and adjust MCQ answer indexes."""
    pool = copy.deepcopy(load_questions(quiz.get("quiz_id", "")))
    try:
        limit = int(quiz.get("max_item", len(pool)) or len(pool))
    except (TypeError, ValueError):
        limit = len(pool)
    random.shuffle(pool)
    chosen = pool[:max(0, limit)]
    for question in chosen:
        choices = question.get("choices", question.get("options", []))
        if question.get("qtype") == "MCQ" and isinstance(choices, list) and choices:
            try:
                correct_index = int(question.get("correct_index", question.get("correct_option_index", -1)))
                correct_text = choices[correct_index]
            except (TypeError, ValueError, IndexError):
                continue
            random.shuffle(choices)
            question["choices"] = choices
            question["correct_index"] = choices.index(correct_text)
    return chosen


def compute_total_and_remark(student: dict, quizzes: list):
    """Return total earned points, total possible points, and a remark."""
    total_score = 0
    total_possible = 0
    attempted = False
    for quiz in quizzes:
        quiz_id = quiz.get("quiz_id", "")
        value = student.get(quiz_id, "")
        if value in ("", None):
            continue
        try:
            score = int(value)
        except (TypeError, ValueError):
            continue
        attempted = True
        total_score += score
        try:
            total_possible += int(quiz.get("max_item", 0) or 0)
        except (TypeError, ValueError):
            pass
    if not attempted or total_possible <= 0:
        return total_score, total_possible, "No grades yet"
    return total_score, total_possible, calculate_remarks(total_score, total_possible)


# ---------------------------------------------------------------------------
# Login sessions and conflict log
# ---------------------------------------------------------------------------
def load_sessions() -> list:
    return read_csv(SESSIONS_CSV)


def save_sessions(rows: list):
    save_rows = []
    for row in rows:
        # Accept legacy/minimal session rows while keeping one canonical header.
        save_rows.append({field: row.get(field, "") for field in SESSION_FIELDS})
    write_csv(SESSIONS_CSV, save_rows, SESSION_FIELDS)


def load_conflicts() -> list:
    return read_csv(CONFLICTS_CSV)


def save_conflicts(rows: list):
    write_csv(CONFLICTS_CSV, rows, CONFLICT_FIELDS)


def log_conflict(student_id: str, issue_type: str):
    rows = load_conflicts()
    rows.append({
        "student_id": student_id,
        "device_id": get_device_id(),
        "attempted_at": get_spaced_now(),
        "issue_type": issue_type,
    })
    save_conflicts(rows)


def clear_conflicts():
    save_conflicts([])


def start_session(student_id: str) -> str:
    """Start a student session; reject an active session on another device."""
    sessions = load_sessions()
    device_id = get_device_id()
    for session in sessions:
        if session.get("student_id") != student_id:
            continue
        if session.get("device_id") == device_id:
            # The student already has a session on this same computer.
            return "ok"
        log_conflict(student_id, "active_session_on_another_device")
        return "conflict"
    sessions.append({
        "session_id": f"SESS_{len(sessions) + 1:04d}",
        "student_id": student_id,
        "quiz_id": "",
        "score": "",
        "date_taken": "",
        "remarks": "",
        "device_id": device_id,
        "started_at": get_spaced_now(),
    })
    save_sessions(sessions)
    return "ok"


def end_session(student_id: str):
    """End this computer's session for a student without clearing another device."""
    device_id = get_device_id()
    save_sessions([
        session for session in load_sessions()
        if not (
            session.get("student_id") == student_id
            and session.get("device_id", device_id) == device_id
        )
    ])


def end_all_sessions_on_this_device():
    """Clear sessions whose device ID matches the current computer."""
    device_id = get_device_id()
    save_sessions([s for s in load_sessions() if s.get("device_id") != device_id])


def is_default_password() -> bool:
    saved = read_csv(AUTH_CSV)
    return bool(saved) and saved[0].get("password_hash") == hash_password(DEFAULT_PROFESSOR_PASSWORD)


def set_professor_password(new_password: str):
    """Save a new professor password hash."""
    write_csv(AUTH_CSV, [{"password_hash": hash_password(new_password)}], ["password_hash"])


# ---------------------------------------------------------------------------
# File initialization
# ---------------------------------------------------------------------------
def ensure_files():
    """Create required files and seed demo data only on a genuinely fresh setup.

    Tracking which CSV files were absent before initialization prevents a user
    who intentionally deletes every quiz from having demo quizzes re-created
    every time the application starts.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(QUESTIONS_DIR, exist_ok=True)
    students_file_was_missing = not os.path.isfile(STUDENTS_CSV)
    quizzes_file_was_missing = not os.path.isfile(QUIZZES_CSV)
    defaults = [
        (STUDENTS_CSV, STUDENT_FIELDS),
        (RETIRED_CSV, ["student_id", "date_retired"]),
        (QUIZZES_CSV, QUIZ_FIELDS),
        (SESSIONS_CSV, SESSION_FIELDS),
        (CONFLICTS_CSV, CONFLICT_FIELDS),
    ]
    quizzes_file_was_missing = not os.path.isfile(QUIZZES_CSV)
    students_file_was_missing = not os.path.isfile(STUDENTS_CSV)
    for path, headers in defaults:
        if not os.path.isfile(path):
            write_csv(path, [], headers)

    if not os.path.isfile(AUTH_CSV):
        write_csv(
            AUTH_CSV,
            [{"password_hash": hash_password(DEFAULT_PROFESSOR_PASSWORD)}],
            ["password_hash"],
        )

    # Seed starter content only on a fresh setup. If a professor later deletes
    # every quiz, do not silently recreate the demo quizzes on the next launch.
    if quizzes_file_was_missing:
        default_quizzes = [
            {"quiz_id": "4001", "title": "Comprehensive Computer Systems",
             "category": "Computer", "max_item": "10", "time_limit_minutes": "15",
             "published": "no", "date_published": ""},
            {"quiz_id": "3001", "title": "STEM Mathematics Exam",
             "category": "Math", "max_item": "10", "time_limit_minutes": "10",
             "published": "no", "date_published": ""},
        ]
        save_quizzes(default_quizzes)
        for quiz in default_quizzes:
            if not os.path.isfile(questions_path(quiz["quiz_id"])):
                save_questions(quiz["quiz_id"], [])
        students = load_students()
        if students_file_was_missing and not students:
            sample = {"student_id": "2026-0001", "name": "Student Demo"}
            for quiz in default_quizzes:
                sample[quiz["quiz_id"]] = ""
            save_students([sample], STUDENT_FIELDS + [q["quiz_id"] for q in default_quizzes])


def build_spinbox_arrows() -> tuple:
    """Create small arrow image assets for the styled QSpinBox controls."""
    assets_dir = os.path.join(DATA_DIR, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    paths = {}
    for name in ("up", "down"):
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor("#111111"))
        painter.setPen(Qt.PenStyle.NoPen)
        points = (
            [QPointF(10, 5), QPointF(3, 15), QPointF(17, 15)]
            if name == "up"
            else [QPointF(3, 5), QPointF(17, 5), QPointF(10, 15)]
        )
        painter.drawPolygon(QPolygonF(points))
        painter.end()
        path = os.path.join(assets_dir, f"spin_{name}.png")
        pixmap.save(path, "PNG")
        paths[name] = path.replace("\\", "/")
    return paths["up"], paths["down"]


def table_cell(text: str) -> QTableWidgetItem:
    """Return a read-only table item."""
    item = QTableWidgetItem(text)
    item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
    return item


# ---------------------------------------------------------------------------
# Animated buttons and global style
# ---------------------------------------------------------------------------
class GradientButton(QPushButton):
    """Animated gold gradient button with hover and selected states."""
    active_button = None

    def __init__(self, text="", parent=None, clicked=None):
        super().__init__(text, parent)
        self._shift = 0.0
        self._hover = 0.0
        self._press = 0.0
        self._is_selected = False
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(40)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet("background: transparent; border: none; color: #111111;")
        if clicked is not None:
            self.clicked.connect(clicked)

    def enterEvent(self, event):
        self._timer.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._timer.start()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self._press = 1.0
        if GradientButton.active_button and GradientButton.active_button != self:
            GradientButton.active_button._is_selected = False
            GradientButton.active_button.update()
        GradientButton.active_button = self
        self._is_selected = True
        self._timer.start()
        super().mousePressEvent(event)

    def _tick(self):
        target_hover = 1.0 if self.underMouse() else 0.0
        self._hover += (target_hover - self._hover) * 0.16
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
        rect = QRectF(self.rect()).adjusted(3, 3, -3, -3)
        colors = [QColor("#FFD54F"), QColor("#FFC700"), QColor("#FFA000")]
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        shift = self._shift
        pairs = [
            ((0.0 + shift) % 1.0, colors[0]),
            ((0.5 + shift) % 1.0, colors[1]),
            ((0.85 + shift) % 1.0, colors[2]),
        ]
        pairs.sort(key=lambda item: item[0])
        gradient.setColorAt(0.0, pairs[0][1])
        for pos, color in pairs:
            gradient.setColorAt(min(pos, 0.999), color)
        gradient.setColorAt(1.0, pairs[-1][1])
        path = QPainterPath()
        path.addRoundedRect(rect, 10, 10)
        painter.fillPath(path, QBrush(gradient))
        if self._hover > 0.05:
            painter.setPen(QPen(QColor(255, 255, 255, int(180 * self._hover)), 2))
            painter.drawPath(path)
        if self._is_selected or self.hasFocus():
            painter.setPen(QPen(QColor(217, 119, 6), 3))
            painter.drawPath(path)
        painter.setPen(QColor("#111111"))
        font = QFont(self.font())
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())
        painter.end()


APP_STYLE = """
QWidget {
    background-color: #FFFFFF; color: #1E293B;
    font-family: 'Inter', 'Segoe UI', sans-serif; font-size: 13px;
}
QFrame#Panel { background-color: #F8FAFC; border-radius: 12px; border: 1px solid #E2E8F0; }
QLabel { background: transparent; color: #1E293B; }
QPushButton { background-color: #FFC700; color: #111111; font-weight: 700;
    border-radius: 10px; padding: 10px 18px; border: 2px solid transparent; }
QPushButton:hover { background-color: #FFB300; border: 2px solid #FFD54F; }
QPushButton:pressed, QPushButton:focus { background-color: #FFA000; border: 2px solid #D97706; }
QPushButton#BtnDanger { background-color: #EF4444; color: #FFFFFF; }
QPushButton#BtnDanger:hover { background-color: #DC2626; border: 2px solid #F87171; }
QPushButton#BtnSecondary { background-color: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; }
QPushButton#BtnSecondary:hover { background-color: #E2E8F0; color: #0F172A; border: 2px solid #94A3B8; }
QLineEdit, QComboBox, QTextEdit { background-color: #FFFFFF; border: 1px solid #CBD5E1;
    border-radius: 10px; padding: 8px; color: #0F172A; }
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QSpinBox:focus { border: 2px solid #D97706; background-color: #FFFEF5; }
QSpinBox { background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 10px;
    padding: 6px 32px 6px 8px; min-height: 24px; color: #0F172A; }
QSpinBox::up-button { subcontrol-origin: border; subcontrol-position: top right; width: 24px;
    height: 16px; border-top-right-radius: 9px; border-left: 1px solid #CBD5E1;
    border-bottom: 1px solid #E2E8F0; background-color: #F8FAFC; margin-top: 1px; margin-right: 1px; }
QSpinBox::up-button:hover, QSpinBox::down-button:hover { background-color: #FEF3C7; }
QSpinBox::up-arrow { image: url(@UP_ARROW@); width: 10px; height: 10px; }
QSpinBox::down-button { subcontrol-origin: border; subcontrol-position: bottom right; width: 24px;
    height: 16px; border-bottom-right-radius: 9px; border-left: 1px solid #CBD5E1;
    background-color: #F8FAFC; margin-bottom: 1px; margin-right: 1px; }
QSpinBox::down-arrow { image: url(@DOWN_ARROW@); width: 10px; height: 10px; }
QRadioButton { background-color: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 12px;
    padding: 12px; color: #1E293B; font-weight: 500; }
QRadioButton:hover { border: 2px solid #FFC700; background-color: #FFFBEB; }
QRadioButton:checked { border: 2px solid #D97706; background-color: #FEF3C7; }
QTableWidget, QListWidget { background-color: #FFFFFF; border: 1px solid #E2E8F0;
    border-radius: 12px; gridline-color: #F1F5F9; }
QTableWidget::item:selected, QListWidget::item:selected { background-color: #FEF3C7; color: #1E293B; }
QHeaderView::section { background-color: #F8FAFC; color: #475569; font-weight: bold;
    padding: 8px; border: none; border-bottom: 2px solid #E2E8F0; }
QProgressBar { background-color: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 8px;
    text-align: center; color: #1E293B; font-weight: bold; }
QProgressBar::chunk { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
    stop:0 #FFC700, stop:1 #10B981); border-radius: 7px; }
"""


# ---------------------------------------------------------------------------
# Launcher and application entry point
# ---------------------------------------------------------------------------
class MainLauncher(QWidget):
    """Role selector that opens the professor or student login window."""
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
        layout.addWidget(GradientButton("Professor Portal", clicked=self.open_professor))
        layout.addWidget(GradientButton("Student Portal", clicked=self.open_student))
        layout.addStretch()

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
        from professor_system import ProfessorLogin
        self.hide()
        self._reuse_or_create("prof_login", lambda: ProfessorLogin(launcher_window=self))

    def open_student(self):
        from student_system import StudentLogin
        self.hide()
        self._reuse_or_create("student_login", lambda: StudentLogin(launcher_window=self))

    def closeEvent(self, event):
        self._closing = True
        app = QApplication.instance()
        if app is not None:
            app.quit()
        event.accept()


def main():
    """Initialize data and Qt, then run the launcher event loop."""
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("group4.quizsystem.app.1")
    except Exception:
        pass
    ensure_files()
    app = QApplication(sys.argv)
    up_arrow, down_arrow = build_spinbox_arrows()
    app.setStyleSheet(APP_STYLE.replace("@UP_ARROW@", up_arrow).replace("@DOWN_ARROW@", down_arrow))
    if os.path.exists(ICON_PATH):
        app.setWindowIcon(QIcon(ICON_PATH))
    launcher = MainLauncher()
    launcher.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
