import os 
from PyQt6.QtWidgets import (  # GUI widgets
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QRadioButton, QButtonGroup,
    QProgressBar, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QTimer  # Qt constants, countdown timer

import main  # shared app functions


class MyGradesWindow(QDialog):  # shows the student's grades
    """Displays student grade history and overall score summary."""
    def __init__(self, student, parent=None):  # set up the window
        super().__init__(parent)
        main.apply_app_icon(self)
        self.student = student
        self.setWindowTitle(f"My Grades — {student.get('name', '')}")
        self.setMinimumSize(520, 460)
        self.initUI()

    def initUI(self):  # build the grades layout
        layout = QVBoxLayout(self)

        header = QLabel(f"{self.student.get('name', '')} (ID: {self.student.get('student_id', '')})")
        header.setStyleSheet("font-size: 15px; font-weight: bold;")
        layout.addWidget(header)

        quizzes = main.load_quizzes()  # load all quizzes
        grades_list = QListWidget()

        any_grade = False
        for quiz in quizzes:
            value = self.student.get(quiz["quiz_id"], "")
            if value == "":
                continue  # skip quizzes not taken
            any_grade = True
            locked = self.student.get(f"locked_{quiz['quiz_id']}", "") == "yes"
            lock_text = " 🔒" if locked else ""  # lock icon if grade is locked
            grades_list.addItem(f"{quiz['title']} ({quiz['category']}): {value} / {quiz.get('max_item', '?')}{lock_text}")

        if not any_grade:
            grades_list.addItem("No quizzes taken yet.")
        layout.addWidget(grades_list, 1)

        total_score, total_possible, remark = main.compute_total_and_remark(self.student, quizzes)  # compute total score and remark
        summary_text = f"Overall: {total_score} / {total_possible}  —  Remark: {remark}" if total_possible else "Overall: No grades yet"
        summary = QLabel(summary_text)
        summary.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(summary)

        close_button = QPushButton("Close", clicked=self.accept)  # close the dialog
        layout.addWidget(close_button)


class ResultWindow(QWidget):  # shows results after a quiz
    """Displays score breakdown immediately after finishing a quiz."""
    def __init__(self, quiz_title, correct, total, breakdown, dashboard):  # set up the window
        super().__init__()
        main.apply_app_icon(self)
        self.dashboard = dashboard
        self.setWindowTitle(f"Results — {quiz_title}")
        self.resize(720, 520)
        self.initUI(correct, total, breakdown)

    def initUI(self, correct, total, breakdown):  # build the results layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        
        score_lbl = QLabel(f"<b>Final Score: {correct}/{total}</b>")
        score_lbl.setStyleSheet("font-size: 16px; color: #D97706;")
        layout.addWidget(score_lbl)

        results_list = QListWidget()
        for text, chosen_text, correct_text, is_correct in breakdown:  # loop through each question
            mark = "CORRECT" if is_correct else "WRONG"
            results_list.addItem(f"[{mark}] {text}\n   Your answer: {chosen_text} | Correct answer: {correct_text}\n")
        layout.addWidget(results_list, 1)

        back_button = main.GradientButton("Back to Dashboard", clicked=self.back_to_dashboard)
        layout.addWidget(back_button)

    def back_to_dashboard(self):  # close this window
        self.close()

    def closeEvent(self, event):  # runs when window closes
        if self.dashboard is not None:
            self.dashboard.load_quiz_list()  # refresh the quiz list
            self.dashboard.show()
        event.accept()


class TakeQuizWindow(QWidget):  # the quiz screen
    """Clean quiz interface with timer and navigation."""
    def __init__(self, student, quiz, questions, dashboard):  # set up quiz state and timer
        super().__init__()
        main.apply_app_icon(self)
        self.student = student
        self.quiz = quiz
        self.questions = questions
        self.dashboard = dashboard
        self.index = 0  # current question number
        self.answers = {}  # saved answers
        self.finished = False  # True once quiz is submitted

        self.seconds_left = int(quiz.get("time_limit_minutes", 10)) * 60  # time limit in seconds
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)  # tick every 1 second

        self.setWindowTitle(f"Quiz: {quiz['title']}")
        self.initUI()
        self.render_question()  # show first question

    def initUI(self):  # build the quiz layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)

        top_row = QHBoxLayout()
        self.timer_label = QLabel()  # countdown label
        self.timer_label.setStyleSheet("font-weight: bold; color: #EF4444; font-size: 16px;")
        
        top_row.addStretch()
        top_row.addWidget(self.timer_label)
        layout.addLayout(top_row)

        self.progress_bar = QProgressBar()  # progress bar
        layout.addWidget(self.progress_bar)

        self.progress_label = QLabel()
        self.progress_label.setWordWrap(True)
        self.progress_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(self.progress_label)

        self.choice_group = QButtonGroup(self)  # group so only one choice is picked
        self.choice_radios = []
        for i in range(4):
            radio = QRadioButton()
            radio.setStyleSheet("font-size: 14px; padding: 10px;")
            self.choice_group.addButton(radio, i)
            self.choice_radios.append(radio)
            layout.addWidget(radio)

        layout.addStretch()  # push buttons to the bottom

        nav_box = QHBoxLayout()  # navigation buttons
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

    def render_question(self):  # show the current question
        total = len(self.questions)
        self.progress_bar.setValue(int(((self.index + 1) / total) * 100))  # update progress bar
        q = self.questions[self.index]
        q_type_label = "Multiple Choice" if q.get("qtype") == "MCQ" or len(q.get("choices", [])) == 4 else "True/False"
        q_text = q.get("text", q.get("question", ""))
        self.progress_label.setText(f"[{q_type_label}] Q{self.index + 1}/{total}: {q_text}")

        opts = q.get("choices", q.get("options", []))  # get the answer choices
        self.choice_group.setExclusive(False)
        for i, radio in enumerate(self.choice_radios):
            if i < len(opts):
                radio.setText(opts[i])
                radio.setVisible(True)
                radio.setChecked(False)
            else:
                radio.setVisible(False)  # hide unused choices
        self.choice_group.setExclusive(True)

        if self.index in self.answers:  # restore saved answer
            self.choice_radios[self.answers[self.index]].setChecked(True)

        self.btn_prev.setEnabled(self.index > 0)  # disable Previous on first question
        
        # Hide "Next Question" on the last question, show it otherwise
        is_last = (self.index >= total - 1)
        self.btn_next.setVisible(not is_last)

    def tick(self):  # runs every second for the timer
        self.seconds_left -= 1
        minutes, seconds = divmod(max(self.seconds_left, 0), 60)  # split into minutes and seconds
        self.timer_label.setText(f"⏱️ {minutes:02d}:{seconds:02d}")
        if self.seconds_left <= 0:
            self.timer.stop()  # stop the timer
            QMessageBox.information(self, "Time's Up", "Time is up — submitting what you've answered so far.")
            self.finish_quiz()  # submit the quiz

    def prev_question(self):  # go to previous question
        checked_id = self.choice_group.checkedId()  # get the selected choice
        if checked_id != -1:  # -1 means nothing selected
            self.answers[self.index] = checked_id  # save the answer
        if self.index > 0:  # not on the first question
            self.index -= 1  # move back one
            self.render_question()  # show that question

    def next_question(self):  # go to next question
        checked_id = self.choice_group.checkedId()  # get the selected choice
        if checked_id != -1:
            self.answers[self.index] = checked_id  # save the answer

        if self.index + 1 < len(self.questions):  # not on the last question
            self.index += 1  # move forward one
            self.render_question()  # show that question

    def confirm_submit(self):  # ask before submitting
        checked_id = self.choice_group.checkedId()  # get the selected choice
        if checked_id != -1:
            self.answers[self.index] = checked_id  # save the answer

        unanswered = [i + 1 for i in range(len(self.questions)) if i not in self.answers]  # list of unanswered question numbers
        if unanswered:  # if some are unanswered
            un_str = ", ".join(map(str, unanswered[:10]))  # show up to 10 numbers
            if len(unanswered) > 10:
                un_str += f" (+{len(unanswered) - 10} more)"  # count the rest
            QMessageBox.warning(  # warn the student
                self, "Unanswered Questions", 
                f"You still have unanswered items: #{un_str}\n\nPlease complete all items before submitting!"
            )
            return  # stop, don't submit

        reply = QMessageBox.question(  # ask for confirmation
            self, "Confirm Submission", 
            "Are you sure you want to finalize and submit your quiz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:  # if the student clicked Yes
            self.finish_quiz()  # submit the quiz

    def finish_quiz(self):  # grade the quiz and save results
        if self.finished:  # already submitted, do nothing
            return
        self.finished = True  # mark as submitted
        self.timer.stop()  # stop the timer

        correct = 0  # number of correct answers
        breakdown = []  # details for the results window
        for i, q in enumerate(self.questions):  # loop through each question
            chosen = self.answers.get(i)  # student's chosen answer
            c_idx = q.get("correct_index", q.get("correct_option_index", 0))  # index of the correct answer
            is_correct = chosen == c_idx  # True if the answer is right
            correct += 1 if is_correct else 0  # add 1 to the score if correct
            choices = q.get("choices", q.get("options", []))  # get the answer choices
            chosen_text = choices[chosen] if (chosen is not None and chosen < len(choices)) else "(no answer)"  # text of the chosen answer
            correct_text = choices[c_idx] if c_idx < len(choices) else "N/A"  # text of the correct answer
            q_text = q.get("text", q.get("question", ""))  # question text
            breakdown.append((q_text, chosen_text, correct_text, is_correct))  # add to the breakdown list

        students = main.load_students()
        for record in students:
            if record["student_id"] == self.student["student_id"]:
                record[self.quiz["quiz_id"]] = str(correct)  # save the score under this quiz's column
        fields = main.get_student_fields()
        if self.quiz["quiz_id"] not in fields:
            fields.append(self.quiz["quiz_id"])  # add a new csv column for this quiz if missing
        for record in students:
            if self.quiz["quiz_id"] not in record:
                record[self.quiz["quiz_id"]] = ""  # fill blanks so every row has the column
        main.write_csv(main.STUDENTS_CSV, students, fields)  # write everything back to the csv

        sessions = main.load_sessions()
        sessions.append({
            "session_id": f"SESS_{len(sessions) + 1:04d}",  # make an id like sess_0001 from the count
            "student_id": self.student["student_id"],
            "quiz_id": self.quiz["quiz_id"],
            "score": str(correct),
            "date_taken": main.get_spaced_now(),
            "remarks": main.calculate_remarks(correct, len(self.questions)),  # pass/fail style remark
            "device_id": main.get_device_id(),
            "started_at": main.get_spaced_now()
        })
        main.save_sessions(sessions)  # save the new session record

        self.result_window = ResultWindow(self.quiz["title"], correct, len(self.questions), breakdown, self.dashboard)
        self.result_window.show()  # show the results screen
        self.close()

    def closeEvent(self, event):
        if not self.finished:
            self.finish_quiz()  # auto grade and save if closed before submitting
        event.accept()


class StudentDashboard(QWidget):
    """Main dashboard for category selection and quiz access."""
    def __init__(self, student, login_window, launcher_window=None):
        super().__init__()
        main.apply_app_icon(self)
        self.student = student  # the logged in student
        self.login_window = login_window  # window to return to on close
        self.launcher_window = launcher_window
        self.setWindowTitle("Student Dashboard — Portal")
        self.resize(800, 560)
        self.selected_category = None  # nothing picked yet
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout(self)  # vertical layout for the whole window
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(12)

        greeting = QLabel(f"Welcome, {self.student.get('name', 'Student')} (ID: {self.student.get('student_id', '')})")
        greeting.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(greeting)

        main_layout.addWidget(QLabel("Choose a category:"))
        category_row = QGridLayout()
        for i, category in enumerate(main.CATEGORIES):  # one button per category
            btn = QPushButton(category, clicked=lambda checked, c=category: self.show_category(c))
            category_row.addWidget(btn, 0, i)  # place buttons side by side
        main_layout.addLayout(category_row)

        main_layout.addWidget(QLabel("Available quizzes in this category:"))
        self.quiz_list = QListWidget()
        self.quiz_list.itemDoubleClicked.connect(self.open_selected_quiz)  # double click opens the quiz
        main_layout.addWidget(self.quiz_list, 1)

        action_row = QHBoxLayout()
        action_row.addWidget(main.GradientButton("Take Selected Quiz", clicked=self.open_selected_quiz))
        action_row.addWidget(QPushButton("My Grades", clicked=self.open_my_grades))
        action_row.addWidget(QPushButton("Logout", clicked=self.logout))
        main_layout.addLayout(action_row)

    def show_category(self, category):
        self.selected_category = category  # remember the choice
        self.load_quiz_list()  # refresh the list

    def load_quiz_list(self):
        self.quiz_list.clear()
        if not self.selected_category:
            return

        fresh_student = next((s for s in main.load_students() if s["student_id"] == self.student["student_id"]), self.student)  # reload latest student data
        self.student = fresh_student

        quizzes = [q for q in main.load_quizzes() if q.get("published") == "yes" and q.get("category") == self.selected_category]  # published quizzes in this category
        available = [q for q in quizzes if self.student.get(q["quiz_id"], "") == ""]  # only quizzes not taken yet

        if not available:
            self.quiz_list.addItem("No available quizzes in this category right now.")
            return

        for quiz in available:
            item = QListWidgetItem(f"{quiz['title']}  ({quiz['max_item']} items, {quiz['time_limit_minutes']} min)")
            item.setData(1000, quiz["quiz_id"])  # hide the quiz id inside the item
            self.quiz_list.addItem(item)

    def open_selected_quiz(self):
        item = self.quiz_list.currentItem()
        if item is None or item.data(1000) is None:  # nothing selected or just a message row
            QMessageBox.information(self, "No Quiz Selected", "Select or double-click an available quiz first.")
            return

        quiz_id = item.data(1000)
        quiz = next(q for q in main.load_quizzes() if q["quiz_id"] == quiz_id)  # find the full quiz record
        questions = main.load_questions(quiz_id)

        if not questions:  # block empty quizzes
            QMessageBox.warning(self, "No Questions", "This quiz has no questions yet. Tell your professor.")
            return

        self.hide()  # hide dashboard while taking the quiz
        self.take_quiz_window = TakeQuizWindow(self.student, quiz, questions, self)
        self.take_quiz_window.show()

    def open_my_grades(self):
        fresh_student = next((s for s in main.load_students() if s["student_id"] == self.student["student_id"]), self.student)
        self.student = fresh_student
        self.grades_window = MyGradesWindow(self.student, self)
        self.grades_window.exec()  # show the grades dialog and wait until it closes

    def logout(self):
        reply = QMessageBox.question(
            self,
            "Logout",
            "Return to the main role selection portal?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.close()  # closing triggers closeEvent below

    def closeEvent(self, event):
        main.end_session(self.student["student_id"])  # mark the session as ended
        if self.launcher_window:
            self.login_window.hide()
            self.launcher_window.show()  # go back to the launcher
        else:
            self.login_window.show()  # go back to the login window
        event.accept()


class StudentLogin(QWidget): # window for student log in
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
        self.id_input.returnPressed.connect(self.login)  # pressing enter logs in
        layout.addWidget(self.id_input)

        continue_button = main.GradientButton("Continue", clicked=self.login)
        layout.addWidget(continue_button)

        back_button = QPushButton("Back to Portal", clicked=self.back_to_portal)
        back_button.setObjectName("BtnSecondary")  # name used for secondary button styling
        layout.addWidget(back_button)

        layout.addStretch()  # push everything up

    def login(self):
        student_id = self.id_input.text().strip()  # get typed id without extra spaces
        if not student_id:
            QMessageBox.warning(self, "Missing ID", "Please enter your Student ID.")
            return

        retired_ids = {row["student_id"] for row in main.load_retired_ids()}  # set of deactivated ids
        if student_id in retired_ids:
            QMessageBox.warning(self, "Access Denied", "This Student ID is no longer active.")
            return

        student = next((s for s in main.load_students() if s["student_id"] == student_id), None)  # look up the student
        if student is None:
            QMessageBox.warning(self, "Not Found", "That Student ID was not found.")
            return

        result = main.start_session(student_id)  # try to start a session
        if result == "conflict":  # already logged in on another device
            QMessageBox.warning(self, "Already Logged In",
                "This Student ID is already active on another device. Ask your professor if this wasn't you.")
            return

        self.id_input.clear()
        self.dashboard = StudentDashboard(student, self, self.launcher_window)  # open the dashboard
        self.dashboard.show()
        self.hide()  # hide the login window

    def back_to_portal(self): # goes back to the main portal
        self.id_input.clear() # empties the text box
        if self.launcher_window:
            self.hide()
            self.launcher_window.show()
        else:
            self.close()

    def closeEvent(self, event):
        if self.launcher_window and not getattr(self.launcher_window, "_closing", False):  # launcher exists and is not shutting down
            self.launcher_window.show()
        event.accept()