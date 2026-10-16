#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# CLASSES & METHODS:
# - StudentLogin: __init__(), initUI(), login(), back_to_portal(), closeEvent()
# - StudentDashboard: __init__(), initUI(), show_category(), load_quiz_list(),
#                      open_selected_quiz(), open_my_grades(), logout(), closeEvent()
# - MyGradesWindow: __init__(), initUI()
# - TakeQuizWindow: __init__(), initUI(), eventFilter(), render_question(), tick(),
#                    next_question(), finish_quiz(quit_early), closeEvent()
# - ResultWindow: __init__(), initUI(), back_to_dashboard(), closeEvent()
#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

import sys
from PyQt6.QtWidgets import (
    QWidget, QApplication, QPushButton, QLineEdit, QLabel, QMessageBox,
    QVBoxLayout, QHBoxLayout, QGridLayout, QRadioButton, QButtonGroup,
    QListWidget, QListWidgetItem, QDialog, QGraphicsOpacityEffect,
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QEvent

from PROFESSOR_FUNCTS import (
    ensure_files, load_students, load_retired_ids,
    load_quizzes, load_questions, compute_total_and_remark,
    get_student_fields, write_csv, STUDENTS_FILE, CATEGORIES,
)
from STUDENT_FUNCTS import start_session, end_session, log_conflict

ensure_files()

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

class StudentLogin(QWidget):
    def __init__(self, launcher_window=None):
        super().__init__()
        self.launcher_window = launcher_window
        self.setWindowTitle("Student Login — HD Portal")
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

        continue_button = QPushButton("Continue", clicked=self.login)
        layout.addWidget(continue_button)

        back_button = QPushButton("Back to Portal", clicked=self.back_to_portal)
        layout.addWidget(back_button)

        layout.addStretch()
        self.show()

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

    # ibabalik sa Teacher/Student picker kung galing sa launcher
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
        self.student = student
        self.login_window = login_window
        self.launcher_window = launcher_window
        self.setWindowTitle("Student Dashboard — HD Layout")
        self.resize(800, 560)
        self.selected_category = None
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(12)

        greeting = QLabel(f"Welcome, {self.student['name']} (ID: {self.student['student_id']})")
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
        action_row.addWidget(QPushButton("Take Selected Quiz", clicked=self.open_selected_quiz))
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

        quizzes = [q for q in load_quizzes() if q["published"] == "yes" and q["category"] == self.selected_category]
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
            self.close()  # closeEvent() ang mag-e-end ng session at magbabalik sa portal

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
            lock_text = " \U0001F512" if locked else ""
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
        self.student = student
        self.quiz = quiz
        self.questions = questions
        self.dashboard = dashboard
        self.index = 0
        self.answers = {}
        self.finished = False
        self.tab_switches = 0

        self.seconds_left = int(quiz["time_limit_minutes"]) * 60
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)

        self.setWindowTitle(f"Taking Proctored Quiz: {quiz['title']}")
        self.resize(720, 520)
        self.installEventFilter(self)
        self.initUI()
        self.render_question()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)

        top_row = QHBoxLayout()
        self.timer_label = QLabel()
        self.timer_label.setStyleSheet("font-weight: bold; color: #d63031; font-size: 14px;")
        
        self.warning_label = QLabel("🛡️ Proctored Exam Active")
        self.warning_label.setStyleSheet("font-weight: bold; color: #00b894; font-size: 13px;")
        
        top_row.addWidget(self.warning_label)
        top_row.addStretch()
        top_row.addWidget(self.timer_label)
        layout.addLayout(top_row)

        self.progress_label = QLabel()
        self.progress_label.setWordWrap(True)
        self.progress_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        layout.addWidget(self.progress_label)

        self.choice_group = QButtonGroup(self)
        self.choice_radios = []
        for i in range(4):
            radio = QRadioButton()
            radio.setStyleSheet("padding: 8px; font-size: 14px;")
            self.choice_group.addButton(radio, i)
            self.choice_radios.append(radio)
            layout.addWidget(radio)

        layout.addStretch()

        next_button = QPushButton("Next Question")
        next_button.clicked.connect(self.next_question)
        layout.addWidget(next_button)

    def eventFilter(self, obj, event):
        if obj == self and not self.finished and self.isVisible():
            if event.type() in [QEvent.Type.WindowDeactivate, QEvent.Type.Hide]:
                self.tab_switches += 1
                self.warning_label.setText(f"⚠️ Focus Loss Detected! (Switch count: {self.tab_switches})")
                self.warning_label.setStyleSheet("font-weight: bold; color: #d63031; font-size: 13px;")
                log_conflict(self.student["student_id"], f"Tab Switch / Window Focus Loss #{self.tab_switches}")
        return super().eventFilter(obj, event)

    def render_question(self):
        q = self.questions[self.index]
        q_type_label = "Multiple Choice Question" if q.get("qtype") == "MCQ" else "True or False"
        self.progress_label.setText(f"[{q_type_label}] Q{self.index + 1}/{len(self.questions)}: {q['text']}")
        for i, radio in enumerate(self.choice_radios):
            if i < len(q["choices"]):
                radio.setText(q["choices"][i])
                radio.setVisible(True)
                radio.setChecked(False)
            else:
                radio.setVisible(False)
        apply_fade_in(self)

    def tick(self):
        self.seconds_left -= 1
        minutes, seconds = divmod(max(self.seconds_left, 0), 60)
        self.timer_label.setText(f"Time left: {minutes:02d}:{seconds:02d}")
        if self.seconds_left <= 0:
            self.timer.stop()
            QMessageBox.information(self, "Time's Up", "Time is up — submitting what you've answered so far.")
            self.finish_quiz(quit_early=False)

    def next_question(self):
        checked_id = self.choice_group.checkedId()
        if checked_id != -1:
            self.answers[self.index] = checked_id

        if self.index + 1 < len(self.questions):
            self.index += 1
            self.render_question()
        else:
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

        # huwag i-end_session dito — naka-login pa hanggang Logout
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
        self.dashboard = dashboard
        self.setWindowTitle(f"Results — {quiz_title}")
        self.resize(700, 500)
        self.initUI(correct, total, tab_switches, breakdown)
        self.show()

    def initUI(self, correct, total, tab_switches, breakdown):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.addWidget(QLabel(f"Score: {correct}/{total}  |  Focus Loss Incidents: {tab_switches}"))

        results_list = QListWidget()
        for text, chosen_text, correct_text, is_correct in breakdown:
            mark = "CORRECT" if is_correct else "WRONG"
            results_list.addItem(f"[{mark}] {text}  |  your answer: {chosen_text}  |  correct answer: {correct_text}")
        layout.addWidget(results_list, 1)

        back_button = QPushButton("Back to Dashboard", clicked=self.back_to_dashboard)
        layout.addWidget(back_button)

    def back_to_dashboard(self):
        self.close()

    def closeEvent(self, event):
        if self.dashboard is not None:
            self.dashboard.load_quiz_list()
            self.dashboard.show()
        event.accept()