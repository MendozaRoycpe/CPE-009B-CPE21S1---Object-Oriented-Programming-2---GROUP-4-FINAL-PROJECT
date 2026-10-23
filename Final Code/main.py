import sys
import os
import csv
import json
import socket
import hashlib
import ctypes
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidgetItem,
    QSizePolicy, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRectF, QPointF
from PyQt6.QtGui import QIcon, QColor, QPainter, QLinearGradient, QFont, QPainterPath, QBrush, QPen, QPixmap, QPolygonF

# File Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
QUESTIONS_DIR = os.path.join(DATA_DIR, "questions")

STUDENTS_CSV = os.path.join(DATA_DIR, "students.csv")
RETIRED_CSV = os.path.join(DATA_DIR, "retired_ids.csv")
QUIZZES_CSV = os.path.join(DATA_DIR, "quizzes.csv")
AUTH_CSV = os.path.join(DATA_DIR, "professor_auth.csv")
SESSIONS_CSV = os.path.join(DATA_DIR, "sessions.csv")

# Dynamic icon path resolution
ICON_PATH = os.path.join(BASE_DIR, "TIPlogo.ico")

STUDENT_FIELDS = ["student_id", "name"]
QUIZ_FIELDS = ["quiz_id", "title", "category", "max_item", "time_limit_minutes", "published", "date_published"]
SESSION_FIELDS = ["session_id", "student_id", "quiz_id", "score", "date_taken", "remarks", "device_id", "started_at"]

CATEGORIES = ["English", "Science", "Math", "Computer"]
CATEGORY_PREFIXES = {
    "English": "100",
    "Science": "200",
    "Math": "300",
    "Computer": "400",
}

def apply_app_icon(widget: QWidget):
    if os.path.exists(ICON_PATH):
        widget.setWindowIcon(QIcon(ICON_PATH))

# Helper & Data Functions

# Hashing function for password storage
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

# Get the device hostname for session tracking 
def get_device_id() -> str:
    return socket.gethostname()

# Get the current time 
def get_spaced_now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# For calculating the grades
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

# Responsible for animation effect when the widget is opened
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

# Read, write, getter for CSV files
def read_csv(filename: str) -> list:
    if not os.path.isfile(filename):
        return []
    with open(filename, "r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))

def write_csv(filename: str, rows: list, fieldnames: list):
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

def get_student_fields() -> list:
    if not os.path.isfile(STUDENTS_CSV):
        return STUDENT_FIELDS.copy()
    with open(STUDENTS_CSV, "r", newline="", encoding="utf-8") as file:
        header = next(csv.reader(file), None)
    return header if header else STUDENT_FIELDS.copy()

#loads the csv files of the students, retired ids, quizzes, and sessions
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

# Responsible for generating a quiz id that is based on the subeject 
# e.g english = 100n, science = 200n, math = 300n, computer = 400n where n is the number of quizzes in that category

def generate_quiz_id(category: str) -> str:
    base_prefix = CATEGORY_PREFIXES.get(category, "100")
    highest = 0
    for quiz in load_quizzes():
        quiz_id = quiz.get("quiz_id", "")
        if quiz_id.startswith(base_prefix):
            suffix = quiz_id[len(base_prefix):]
            if suffix.isdigit():
                highest = max(highest, int(suffix))
    return f"{base_prefix}{highest + 1}"

#Responsible for computing the total score and remarks of a student based on the quizzes they have taken
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

#responsible for loading, saving, starting, and ending sessions for students
def load_sessions() -> list:
    return read_csv(SESSIONS_CSV)

def save_sessions(rows: list):
    write_csv(SESSIONS_CSV, rows, SESSION_FIELDS)

def start_session(student_id: str) -> str:
    sessions = load_sessions()
    device_id = get_device_id()

    for session in sessions:
        if session.get("student_id") == student_id and session.get("device_id") == device_id:
            return "ok"

# this function is responsible for creating a new session for a student and saving it to the sessions csv file
    sessions.append({
        "session_id": f"SESS_{len(sessions) + 1:04d}", # creates a unique session id that is only 4 numbers long because of 1:04d
        "student_id": student_id,
        "quiz_id": "",
        "score": "0",
        "date_taken": get_spaced_now(),
        "remarks": "",
        "device_id": device_id,
        "started_at": get_spaced_now()
    })
    save_sessions(sessions)
    return "ok"

def end_session(student_id: str):
    sessions = [s for s in load_sessions() if s.get("student_id") != student_id]
    save_sessions(sessions)


# Ensuring the files are created and initialized with default data if they don't exist
def ensure_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(QUESTIONS_DIR, exist_ok=True)

    files = [
        (STUDENTS_CSV, STUDENT_FIELDS),
        (RETIRED_CSV, ["student_id", "date_retired"]),
        (QUIZZES_CSV, QUIZ_FIELDS),
        (SESSIONS_CSV, SESSION_FIELDS)
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

    # If no quizzes exist, create default quizzes and a sample student
    if not quizzes:
        default_quizzes = [
            {"quiz_id": "4001", "title": "Comprehensive Computer Systems", "category": "Computer", "max_item": "10", "time_limit_minutes": "15", "published": "no", "date_published": ""},
            {"quiz_id": "3001", "title": "STEM Mathematics Exam", "category": "Math", "max_item": "10", "time_limit_minutes": "10", "published": "no", "date_published": ""}
        ]
        for q in default_quizzes:
            save_questions(q["quiz_id"], [])

        write_csv(QUIZZES_CSV, default_quizzes, QUIZ_FIELDS)

        students = load_students()
        if not students:
            sample_student = {"student_id": "2026-0001", "name": "Student Demo"}
            for q in default_quizzes:
                sample_student[q["quiz_id"]] = ""
            students.append(sample_student)
            save_students(students)
            
# Create up and down arrow images for QSpinBox buttons and save them in the assets directory
def build_spinbox_arrows() -> tuple:
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
        if name == "up":
            points = [QPointF(10, 5), QPointF(3, 15), QPointF(17, 15)]
        else:
            points = [QPointF(3, 5), QPointF(17, 5), QPointF(10, 15)]
        painter.drawPolygon(QPolygonF(points))
        painter.end()
        path = os.path.join(assets_dir, f"spin_{name}.png")
        pixmap.save(path, "PNG")
        paths[name] = path.replace("\\", "/")
    return paths["up"], paths["down"]

#Returns a QTableWidgetItem with the given text and sets it to be selectable and enabled
def table_cell(text: str) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
    return item


#Custom Animated buttons
class GradientButton(QPushButton):
    active_button = None
    
#Responsible for creating a gradient button with hover and click effects
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
            super().clicked.connect(clicked)

#Responsible for starting the timer when the mouse enters or leaves the button area
    def enterEvent(self, event):
        self._timer.start()
        super().enterEvent(event)
#Responsible for starting the timer when the mouse leaves the button area
    def leaveEvent(self, event):
        self._timer.start()
        super().leaveEvent(event)
#Responsible for starting the timer when the mouse is pressed on the button
    def mousePressEvent(self, event):
        self._press = 1.0
        
        if GradientButton.active_button and GradientButton.active_button != self:
            GradientButton.active_button._is_selected = False
            GradientButton.active_button.update()
            
        GradientButton.active_button = self
        self._is_selected = True
        
        self._timer.start()
        super().mousePressEvent(event)

#Animation step that runs about every 16 ms while the button is animating.
#It eases the hover glow in or out, scrolls the gradient colors while the mouse is over the
#button, fades out the click effect, and stops the timer once everything has settled.
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

#Draws the button by hand: a rounded rectangle filled with the moving gold gradient,
#a white glow border while hovering, an orange border when selected or focused,
#and the bold button text centered on top.
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = QRectF(self.rect()).adjusted(3, 3, -3, -3)
        
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
        
        if self._hover > 0.05:
            painter.setPen(QPen(QColor(255, 255, 255, int(180 * self._hover)), 2))
            painter.drawPath(path)

        if self._is_selected or self.hasFocus():
            highlight_pen = QPen(QColor(217, 119, 6), 3)
            painter.setPen(highlight_pen)
            painter.drawPath(path)
            
        painter.setPen(QColor("#111111"))
        font = QFont(self.font())
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())
        painter.end()


# Background and widget styles for the whole application
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
    border: 2px solid transparent;
}
QPushButton:hover {
    background-color: #FFB300;
    border: 2px solid #FFD54F;
}
QPushButton:pressed, QPushButton:focus {
    background-color: #FFA000;
    border: 2px solid #D97706;
}

QPushButton#BtnDanger {
    background-color: #EF4444;
    color: #FFFFFF;
}
QPushButton#BtnDanger:hover {
    background-color: #DC2626;
    border: 2px solid #F87171;
}
QPushButton#BtnDanger:pressed, QPushButton#BtnDanger:focus {
    border: 2px solid #991B1B;
}

QPushButton#BtnSecondary {
    background-color: #F1F5F9;
    color: #475569;
    border: 1px solid #CBD5E1;
}
QPushButton#BtnSecondary:hover {
    background-color: #E2E8F0;
    color: #0F172A;
    border: 2px solid #94A3B8;
}
QPushButton#BtnSecondary:pressed, QPushButton#BtnSecondary:focus {
    border: 2px solid #D97706;
}

QLineEdit, QComboBox, QTextEdit {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 10px;
    padding: 8px;
    color: #0F172A;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QSpinBox:focus {
    border: 2px solid #D97706;
    background-color: #FFFEF5;
}

/* QSpinBox styled with black '+' and '-' buttons */
QSpinBox {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 10px;
    padding: 6px 32px 6px 8px;
    min-height: 24px;
    color: #0F172A;
}

QSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 24px;
    height: 16px;
    border-top-right-radius: 9px;
    border-left: 1px solid #CBD5E1;
    border-bottom: 1px solid #E2E8F0;
    background-color: #F8FAFC;
    margin-top: 1px;
    margin-right: 1px;
}
QSpinBox::up-button:hover {
    background-color: #FEF3C7;
}
QSpinBox::up-arrow {
    image: url(@UP_ARROW@);
    width: 10px;
    height: 10px;
}

QSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 24px;
    height: 16px;
    border-bottom-right-radius: 9px;
    border-left: 1px solid #CBD5E1;
    background-color: #F8FAFC;
    margin-bottom: 1px;
    margin-right: 1px;
}
QSpinBox::down-button:hover {
    background-color: #FEF3C7;
}
QSpinBox::down-arrow {
    image: url(@DOWN_ARROW@);
    width: 10px;
    height: 10px;
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
    border: 2px solid #FFC700;
    background-color: #FFFBEB;
}
QRadioButton:checked {
    border: 2px solid #D97706;
    background-color: #FEF3C7;
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


# Launcher Window
class MainLauncher(QWidget):
    #Sets up the launcher window (icon, title, size) and builds its layout.
    #_closing is a flag that tells the login windows the whole app is shutting down.
    def __init__(self):
        super().__init__()
        apply_app_icon(self)
        self.setWindowTitle("Quiz System — Unified Portal Launcher")
        self.resize(480, 300)
        self._closing = False
        self.initUI()

    #Builds the launcher screen: the title, the subtitle, and the Professor Portal
    #and Student Portal buttons that open each login window.
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

        layout.addStratch() if hasattr(layout, 'addStratch') else layout.addStretch()
        self.show()

    #Shows a window that was already created (so the same login window is not duplicated).
    #If none exists yet, or Qt already deleted it (RuntimeError), it creates a new one
    #by calling factory(), saves it on self under attr_name, and shows it.
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

    #Hides the launcher and opens the Professor login window.
    #The import is done here instead of at the top because professor_system imports main,
    #and importing it at the top would cause a circular import.
    def open_professor(self):
        from professor_system import ProfessorLogin
        self.hide()
        self._reuse_or_create("prof_login", lambda: ProfessorLogin(launcher_window=self))

    #Hides the launcher and opens the Student login window.
    #Imported here for the same reason: student_system also imports main.
    def open_student(self):
        from student_system import StudentLogin
        self.hide()
        self._reuse_or_create("student_login", lambda: StudentLogin(launcher_window=self))

    #Runs when the launcher window is closed. Sets the _closing flag and quits the
    #whole application so no other window is left running in the background.
    def closeEvent(self, event):
        self._closing = True
        app = QApplication.instance()
        if app is not None:
            app.quit()
        event.accept()


# Starting point of the program. It sets the Windows taskbar app ID (so the taskbar shows
# our icon instead of Python's), creates the data files if they are missing, starts the Qt
# application, applies the stylesheet (with the spin box arrow images), sets the app icon,
# shows the launcher, and runs the event loop until the app is closed.
def main():
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