import os
from PyQt6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QRadioButton, QButtonGroup,
    QProgressBar, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QTimer

import main


class MyGradesWindow(QDialog):
    """Displays student grade history and overall score summary."""
    def __init__(self, student, parent=None):
        super().__init__(parent)
        main.apply_app_icon(self)
        self.student = student
        self.setWindowTitle(f"My Grades — {student.get('name', '')}")
        self.setMinimumSize(520, 460)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        header = QLabel(f"{self.student.get('name', '')} (ID: {self.student.get('student_id', '')})")
        header.setStyleSheet("font-size: 15px; font-weight: bold;")
        layout.addWidget(header)

        quizzes = main.load_quizzes()
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

        total_score, total_possible, remark = main.compute_total_and_remark(self.student, quizzes)
        summary_text = f"Overall: {total_score} / {total_possible}  —  Remark: {remark}" if total_possible else "Overall: No grades yet"
        summary = QLabel(summary_text)
        summary.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(summary)

        close_button = QPushButton("Close", clicked=self.accept)
        layout.addWidget(close_button)


class ResultWindow(QWidget):
    """Displays score breakdown immediately after finishing a quiz."""
    def __init__(self, quiz_title, correct, total, breakdown, dashboard):
        super().__init__()
        main.apply_app_icon(self)
        self.dashboard = dashboard
        self.setWindowTitle(f"Results — {quiz_title}")
        self.resize(720, 520)
        self.initUI(correct, total, breakdown)

    def initUI(self, correct, total, breakdown):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        
        score_lbl = QLabel(f"<b>Final Score: {correct}/{total}</b>")
        score_lbl.setStyleSheet("font-size: 16px; color: #D97706;")
        layout.addWidget(score_lbl)

        results_list = QListWidget()
        for text, chosen_text, correct_text, is_correct in breakdown:
            mark = "CORRECT" if is_correct else "WRONG"
            results_list.addItem(f"[{mark}] {text}\n   Your answer: {chosen_text} | Correct answer: {correct_text}\n")
        layout.addWidget(results_list, 1)

        back_button = main.GradientButton("Back to Dashboard", clicked=self.back_to_dashboard)
        layout.addWidget(back_button)

    def back_to_dashboard(self):
        self.close()

    def closeEvent(self, event):
        if self.dashboard is not None:
            self.dashboard.load_quiz_list()
            self.dashboard.show()
        event.accept()


class TakeQuizWindow(QWidget):
    """Clean quiz interface with timer and navigation."""
    def __init__(self, student, quiz, questions, dashboard):
        super().__init__()
        main.apply_app_icon(self)
        self.student = student
        self.quiz = quiz
        self.questions = questions
        self.dashboard = dashboard
        self.index = 0
        self.answers = {}
        self.finished = False

        self.seconds_left = int(quiz.get("time_limit_minutes", 10)) * 60
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)

        self.setWindowTitle(f"Quiz: {quiz['title']}")
        self.initUI()
        self.render_question()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)

        top_row = QHBoxLayout()
        self.timer_label = QLabel()
        self.timer_label.setStyleSheet("font-weight: bold; color: #EF4444; font-size: 16px;")
        
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

    def render_question(self):
        total = len(self.questions)
        self.progress_bar.setValue(int(((self.index + 1) / total) * 100))
        q = self.questions[self.index]
        q_type_label = "Multiple Choice" if q.get("qtype") == "MCQ" or len(q.get("choices", [])) == 4 else "True/False"
        q_text = q.get("text", q.get("question", ""))
        self.progress_label.setText(f"[{q_type_label}] Q{self.index + 1}/{total}: {q_text}")

        opts = q.get("choices", q.get("options", []))
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
        
        # Hide "Next Question" on the last question, show it otherwise
        is_last = (self.index >= total - 1)
        self.btn_next.setVisible(not is_last)

    def tick(self):
        self.seconds_left -= 1
        minutes, seconds = divmod(max(self.seconds_left, 0), 60)
        self.timer_label.setText(f"⏱️ {minutes:02d}:{seconds:02d}")
        if self.seconds_left <= 0:
            self.timer.stop()
            QMessageBox.information(self, "Time's Up", "Time is up — submitting what you've answered so far.")
            self.finish_quiz()

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
            self.finish_quiz()

    def finish_quiz(self):
        if self.finished:
            return
        self.finished = True
        self.timer.stop()

        correct = 0
        breakdown = []
        for i, q in enumerate(self.questions):
            chosen = self.answers.get(i)
            c_idx = q.get("correct_index", q.get("correct_option_index", 0))
            is_correct = chosen == c_idx
            correct += 1 if is_correct else 0
            choices = q.get("choices", q.get("options", []))
            chosen_text = choices[chosen] if (chosen is not None and chosen < len(choices)) else "(no answer)"
            correct_text = choices[c_idx] if c_idx < len(choices) else "N/A"
            q_text = q.get("text", q.get("question", ""))
            breakdown.append((q_text, chosen_text, correct_text, is_correct))

        students = main.load_students()
        for record in students:
            if record["student_id"] == self.student["student_id"]:
                record[self.quiz["quiz_id"]] = str(correct)
        fields = main.get_student_fields()
        if self.quiz["quiz_id"] not in fields:
            fields.append(self.quiz["quiz_id"])
        for record in students:
            if self.quiz["quiz_id"] not in record:
                record[self.quiz["quiz_id"]] = ""
        main.write_csv(main.STUDENTS_CSV, students, fields)

        sessions = main.load_sessions()
        sessions.append({
            "session_id": f"SESS_{len(sessions) + 1:04d}",
            "student_id": self.student["student_id"],
            "quiz_id": self.quiz["quiz_id"],
            "score": str(correct),
            "date_taken": main.get_spaced_now(),
            "remarks": main.calculate_remarks(correct, len(self.questions)),
            "device_id": main.get_device_id(),
            "started_at": main.get_spaced_now()
        })
        main.save_sessions(sessions)

        self.result_window = ResultWindow(self.quiz["title"], correct, len(self.questions), breakdown, self.dashboard)
        self.result_window.show()
        self.close()

    def closeEvent(self, event):
        if not self.finished:
            self.finish_quiz()
        event.accept()


class StudentDashboard(QWidget):
    """Main dashboard for category selection and quiz access."""
    def __init__(self, student, login_window, launcher_window=None):
        super().__init__()
        main.apply_app_icon(self)
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
        for i, category in enumerate(main.CATEGORIES):
            btn = QPushButton(category, clicked=lambda checked, c=category: self.show_category(c))
            category_row.addWidget(btn, 0, i)
        main_layout.addLayout(category_row)

        main_layout.addWidget(QLabel("Available quizzes in this category:"))
        self.quiz_list = QListWidget()
        self.quiz_list.itemDoubleClicked.connect(self.open_selected_quiz)
        main_layout.addWidget(self.quiz_list, 1)

        action_row = QHBoxLayout()
        action_row.addWidget(main.GradientButton("Take Selected Quiz", clicked=self.open_selected_quiz))
        action_row.addWidget(QPushButton("My Grades", clicked=self.open_my_grades))
        action_row.addWidget(QPushButton("Logout", clicked=self.logout))
        main_layout.addLayout(action_row)

    def show_category(self, category):
        self.selected_category = category
        self.load_quiz_list()

    def load_quiz_list(self):
        self.quiz_list.clear()
        if not self.selected_category:
            return

        fresh_student = next((s for s in main.load_students() if s["student_id"] == self.student["student_id"]), self.student)
        self.student = fresh_student

        quizzes = [q for q in main.load_quizzes() if q.get("published") == "yes" and q.get("category") == self.selected_category]
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
        quiz = next(q for q in main.load_quizzes() if q["quiz_id"] == quiz_id)
        questions = main.load_questions(quiz_id)

        if not questions:
            QMessageBox.warning(self, "No Questions", "This quiz has no questions yet. Tell your professor.")
            return

        self.hide()
        self.take_quiz_window = TakeQuizWindow(self.student, quiz, questions, self)
        self.take_quiz_window.show()

    def open_my_grades(self):
        fresh_student = next((s for s in main.load_students() if s["student_id"] == self.student["student_id"]), self.student)
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
        main.end_session(self.student["student_id"])
        if self.launcher_window:
            self.login_window.hide()
            self.launcher_window.show()
        else:
            self.login_window.show()
        event.accept()


class StudentLogin(QWidget):
    """Student portal login interface."""
    def __init__(self, launcher_window=None):
        super().__init__()
        main.apply_app_icon(self)
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

        continue_button = main.GradientButton("Continue", clicked=self.login)
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

        retired_ids = {row["student_id"] for row in main.load_retired_ids()}
        if student_id in retired_ids:
            QMessageBox.warning(self, "Access Denied", "This Student ID is no longer active.")
            return

        student = next((s for s in main.load_students() if s["student_id"] == student_id), None)
        if student is None:
            QMessageBox.warning(self, "Not Found", "That Student ID was not found.")
            return

        result = main.start_session(student_id)
        if result == "conflict":
            QMessageBox.warning(self, "Already Logged In",
                "This Student ID is already active on another device. Ask your professor if this wasn't you.")
            return

        self.id_input.clear()
        self.dashboard = StudentDashboard(student, self, self.launcher_window)
        self.dashboard.show()
        self.hide()

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