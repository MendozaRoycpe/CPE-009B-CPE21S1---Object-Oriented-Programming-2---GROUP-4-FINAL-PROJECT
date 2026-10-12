import sys, socket, json
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QApplication, QPushButton, QLineEdit, QLabel, QMessageBox,
    QVBoxLayout, QHBoxLayout, QGridLayout, QListWidget, QListWidgetItem)
from PyQt6.QtCore import QTimer, Qt
from ui_theme import (
    apply_app_theme, start_yellow_canvas, GradientButton, QuizizzChoiceButton,
    qtype_label, is_mcq, tf_choices,
)

#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# FUNCTIONS / METHODS LIST:
# - get_device_id()
# - load_sessions() / save_sessions(rows)
# - start_session(student_id) -> "ok" | "conflict"
# - end_session(student_id)
# - log_conflict(student_id)
#
# CLASSES & METHODS:
# - StudentLogin: __init__(), initUI(), login(), back_to_portal(), closeEvent()
# - StudentDashboard: __init__(), initUI(), show_category(), load_quiz_list(),
#                      open_selected_quiz(), logout(), closeEvent()
# - TakeQuizWindow: __init__(), initUI(), render_question(), tick(), next_question(),
#                    finish_quiz(quit_early), closeEvent()
# - ResultWindow: __init__(), initUI(), back_to_dashboard()
#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Reuses every file/CSV helper and constant teacher_system.py already defines, instead of
# duplicating them here — the "class of teacher and students... imported/used on another
# file" setup, just applied to the shared data layer too.
from teacher_system import (
    ensure_files, read_csv, write_csv, get_student_fields,
    load_students, save_students, load_retired_ids, load_quizzes, load_questions,
    STUDENTS_FILE, SESSIONS_FILE, CONFLICTS_FILE, SESSION_FIELDS, CONFLICT_FIELDS,
)

ensure_files()


# gumagamit ng hostname bilang device_id — sapat na para sa "isang estudyante per device"
# na rule sa loob ng isang computer lab; palitan ng tunay na machine-UUID kapag na-deploy na
def get_device_id():
    return socket.gethostname()

# kukunin lahat ng currently-active na sessions (isang row bawat naka-login na estudyante)
def load_sessions():
    return read_csv(SESSIONS_FILE)

def save_sessions(rows):
    write_csv(SESSIONS_FILE, rows, SESSION_FIELDS)

# susubukan i-start ang session ng student_id na ito sa device na ito;
# "ok" kung pumayag, "conflict" kung naka-login na ang ID na ito sa ibang device
def start_session(student_id):
    sessions = load_sessions()
    device_id = get_device_id()

    for session in sessions:
        if session["student_id"] == student_id:
            if session["device_id"] == device_id:
                return "ok" # <-- parehong device lang, tuloy lang (e.g. nag-refresh)
            log_conflict(student_id)
            return "conflict"

    sessions.append({"student_id": student_id, "device_id": device_id,
                      "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    save_sessions(sessions)
    return "ok"

# tatanggalin yung session row ng student_id na ito (tapos na sila mag-quiz o sumara sila)
def end_session(student_id):
    sessions = [s for s in load_sessions() if s["student_id"] != student_id]
    save_sessions(sessions)

# ililista sa session_conflicts.csv ang sinumang sumubok mag-login gamit ang ID na naka-active
# na sa ibang device — dito babasahin ng professor dashboard sa susunod na stage
def log_conflict(student_id):
    conflicts = read_csv(CONFLICTS_FILE)
    conflicts.append({"student_id": student_id, "device_id": get_device_id(),
                       "attempted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    write_csv(CONFLICTS_FILE, conflicts, CONFLICT_FIELDS)


# login window kung saan magla-lagay lang ng Student ID ang estudyante — walang password
class StudentLogin(QWidget):
    # setup ng window size at title para sa login page
    # portal_window = RoleSelect mula sa main.py; None kung standalone run
    def __init__(self, portal_window=None):
        super().__init__()
        self.portal_window = portal_window
        self.setWindowTitle("Student Login")
        self.setGeometry(400, 200, 480, 280)
        start_yellow_canvas(self)
        self.initUI()

    # gawa ng label, text box, continue button, at back-to-portal button
    def initUI(self):
        QLabel("QUIZ SYSTEM - STUDENT", self).move(120, 30)
        QLabel("Student ID:", self).move(70, 90)
        self.id_input = QLineEdit(self)
        self.id_input.setGeometry(160, 85, 240, 32)
        continue_button = GradientButton("Continue", self, clicked=self.login)
        continue_button.setGeometry(160, 140, 240, 42)
        back_button = GradientButton("Back to Portal", self, clicked=self.back_to_portal)
        back_button.setGeometry(160, 190, 240, 42)
        self.show()

    # ibabalik sa Teacher/Student picker kung galing sa main.py
    def back_to_portal(self):
        self.id_input.clear()
        if self.portal_window is not None:
            self.hide()
            self.portal_window.show()
        else:
            self.close()

    # X button ng login window — same destination as Back to Portal
    def closeEvent(self, event):
        if self.portal_window is not None and not getattr(self.portal_window, "_closing", False):
            self.portal_window.show()
        event.accept()

    # hahanapin yung ID sa students.csv, che-check ang status, tapos che-check ang session
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
        if result == "conflict": # <-- NOTE: naka-login na ang ID na ito sa ibang device; naka-log na sa session_conflicts.csv para makita ng professor
            QMessageBox.warning(self, "Already Logged In",
                "This Student ID is already active on another device. Ask your professor if this wasn't you.")
            return

        self.id_input.clear()
        self.hide()
        self.dashboard = StudentDashboard(student, self)
        self.dashboard.show()


# dashboard kung saan pipiliin ng estudyante ang category tapos ang specific quiz
class StudentDashboard(QWidget):
    # constructor: itago yung student record at login window reference
    def __init__(self, student, login_window):
        super().__init__()
        self.student = student
        self.login_window = login_window
        self.portal_window = getattr(login_window, "portal_window", None)
        self.setWindowTitle("Student Dashboard")
        self.setGeometry(150, 100, 640, 480)
        self.selected_category = None
        start_yellow_canvas(self)
        self.initUI()

    # ilalagay yung greeting, category buttons, quiz list, at logout button
    def initUI(self):
        QLabel(f"Welcome, {self.student['name']} (ID: {self.student['student_id']})", self).move(25, 20)
        QLabel("Choose a category:", self).move(25, 55)

        categories = ["English", "Math", "Science", "Computer"]
        for i, category in enumerate(categories):
            GradientButton(category, self, clicked=lambda checked=False, c=category: self.show_category(c)).setGeometry(25 + i * 150, 85, 140, 42)

        QLabel("Available quizzes in this category:", self).move(25, 140)
        self.quiz_list = QListWidget(self)
        self.quiz_list.setGeometry(25, 170, 590, 210)
        self.quiz_list.itemDoubleClicked.connect(self.open_selected_quiz)

        GradientButton("Take Selected Quiz", self, clicked=self.open_selected_quiz).setGeometry(25, 400, 220, 44)
        GradientButton("Logout", self, clicked=self.logout).setGeometry(455, 400, 160, 44)

    # ipapakita lang ang mga quizzes ng napiling category na published at wala pang grade
    def show_category(self, category):
        self.selected_category = category
        self.load_quiz_list()

    def load_quiz_list(self):
        self.quiz_list.clear()
        if not self.selected_category:
            return

        fresh_student = next((s for s in load_students() if s["student_id"] == self.student["student_id"]), self.student)
        self.student = fresh_student

        quizzes = [q for q in load_quizzes() if q["published"] == "yes" and q["category"] == self.selected_category]
        available = [q for q in quizzes if self.student.get(q["quiz_id"], "") == ""] # <-- blangko pa ang grade cell nito = pwede pang kunin

        if not available:
            self.quiz_list.addItem("No available quizzes in this category right now.")
            return

        for quiz in available:
            item = QListWidgetItem(f"{quiz['title']}  ({quiz['max_item']} items, {quiz['time_limit_minutes']} min)")
            item.setData(1000, quiz["quiz_id"]) # <-- itinatago ang tunay na quiz_id sa custom data role
            self.quiz_list.addItem(item)

    # bubukas ng TakeQuizWindow para sa currently selected na quiz sa listahan
    def open_selected_quiz(self):
        item = self.quiz_list.currentItem()
        if item is None or item.data(1000) is None:
            QMessageBox.information(self, "No Quiz Selected", "Double-click or select an available quiz first.")
            return

        quiz_id = item.data(1000)
        quiz = next(q for q in load_quizzes() if q["quiz_id"] == quiz_id)
        questions = load_questions(quiz_id)

        if not questions:
            QMessageBox.warning(self, "No Questions", "This quiz has no questions yet. Tell your professor.")
            return

        self.hide()
        self.take_quiz_window = TakeQuizWindow(self.student, quiz, questions, self)
        self.take_quiz_window.show()

    # tatapusin ang session tapos babalik sa role-selection portal (o login kung standalone)
    def logout(self):
        reply = QMessageBox.question(
            self,
            "Logout",
            "Return to the role selection portal?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.close()  # closeEvent() ang mag-e-end ng session at magbabalik sa portal

    # X button o Logout — i-clear ang session para hindi ma-lock ang Student ID
    def closeEvent(self, event):
        end_session(self.student["student_id"])
        if self.portal_window is not None:
            self.login_window.hide()
            self.portal_window.show()
        else:
            self.login_window.show()
        event.accept()


# window kung saan sinasagutan ng estudyante ang isang tanong sa bawat pagkakataon,
# may visible na countdown timer base sa time_limit_minutes ng quiz
class TakeQuizWindow(QWidget):
    def __init__(self, student, quiz, questions, dashboard):
        super().__init__()
        self.student = student
        self.quiz = quiz
        self.questions = questions
        self.dashboard = dashboard
        self.index = 0
        self.answers = {}
        self.finished = False # <-- NOTE: ginagamit para hindi ma-double-finalize sa closeEvent

        self.seconds_left = int(quiz["time_limit_minutes"]) * 60
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)

        self.setWindowTitle(f"Taking: {quiz['title']}")
        self.setGeometry(200, 150, 550, 400)
        self.initUI()
        self.render_question()

    def initUI(self):
        layout = QVBoxLayout(self)

        self.timer_label = QLabel()
        layout.addWidget(self.timer_label)

        self.progress_label = QLabel()
        layout.addWidget(self.progress_label)

        self.choice_group = QButtonGroup(self)
        self.choice_radios = []
        for i in range(4):
            radio = QRadioButton()
            self.choice_group.addButton(radio, i)
            self.choice_radios.append(radio)
            layout.addWidget(radio)

        next_button = QPushButton("Next")
        next_button.clicked.connect(self.next_question)
        layout.addWidget(next_button)

    # ipapakita ang kasalukuyang tanong at ang mga choices nito
    def render_question(self):
        q = self.questions[self.index]
        self.progress_label.setText(f"Q{self.index + 1}/{len(self.questions)}: {q['text']}")
        for i, radio in enumerate(self.choice_radios):
            if i < len(q["choices"]):
                radio.setText(q["choices"][i])
                radio.setVisible(True)
                radio.setChecked(False)
            else:
                radio.setVisible(False)

    # tumatawag bawat segundo mula sa QTimer; kapag naubos na ang oras, auto-finalize
    def tick(self):
        self.seconds_left -= 1
        minutes, seconds = divmod(max(self.seconds_left, 0), 60)
        self.timer_label.setText(f"Time left: {minutes:02d}:{seconds:02d}")
        if self.seconds_left <= 0:
            self.timer.stop()
            QMessageBox.information(self, "Time's Up", "Time is up — submitting what you've answered so far.")
            self.finish_quiz(quit_early=False)

    # itatala ang sagot sa kasalukuyang tanong tapos lilipat sa susunod, o tatapusin na
    def next_question(self):
        checked_id = self.choice_group.checkedId()
        if checked_id != -1:
            self.answers[self.index] = checked_id

        if self.index + 1 < len(self.questions):
            self.index += 1
            self.render_question()
        else:
            self.finish_quiz(quit_early=False)

    # kukuwentahin ang score, isusulat sa students.csv, tapos bubuksan ang ResultWindow
    def finish_quiz(self, quit_early):
        if self.finished:
            return
        self.finished = True
        self.timer.stop()

        correct = 0
        breakdown = []
        for i, q in enumerate(self.questions):
            chosen = self.answers.get(i)
            is_correct = chosen == q["correct_index"]
            correct += 1 if is_correct else 0
            chosen_text = q["choices"][chosen] if chosen is not None else "(no answer)"
            correct_text = q["choices"][q["correct_index"]]
            breakdown.append((q["text"], chosen_text, correct_text, is_correct))

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

        # huwag i-end_session dito — naka-login pa ang estudyante hanggang Logout
        self.result_window = ResultWindow(self.quiz["title"], correct, len(self.questions), breakdown, self.dashboard)
        self.result_window.show()
        self.close()

    # tinatapat bilang "isinumite na" ang attempt kahit isinara lang ang window nang bigla —
    # katumbas ito ng pag-expire ng timer (Framework v3, Quiz Lifecycle)
    def closeEvent(self, event):
        if not self.finished:
            self.finish_quiz(quit_early=True)
        event.accept()


# ipapakita ang score tsaka ang tamang sagot sa bawat tanong pagkatapos sumagot
class ResultWindow(QWidget):
    def __init__(self, quiz_title, correct, total, breakdown, dashboard):
        super().__init__()
        self.dashboard = dashboard
        self.setWindowTitle(f"Results — {quiz_title}")
        self.setGeometry(200, 150, 600, 450)
        self.initUI(correct, total, breakdown)
        self.show()

    def initUI(self, correct, total, breakdown):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Score: {correct}/{total}"))

        results_list = QListWidget()
        for text, chosen_text, correct_text, is_correct in breakdown:
            mark = "CORRECT" if is_correct else "WRONG"
            results_list.addItem(f"[{mark}] {text}  |  your answer: {chosen_text}  |  correct answer: {correct_text}")
        layout.addWidget(results_list)

        back_button = QPushButton("Back to Dashboard")
        back_button.clicked.connect(self.back_to_dashboard)
        layout.addWidget(back_button)

    def back_to_dashboard(self):
        self.close()

    def closeEvent(self, event):
        if self.dashboard is not None:
            self.dashboard.load_quiz_list()
            self.dashboard.show()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = StudentLogin()
    sys.exit(app.exec())