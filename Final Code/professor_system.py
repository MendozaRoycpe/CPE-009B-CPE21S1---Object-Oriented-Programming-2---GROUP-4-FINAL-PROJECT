"""PROFESSOR SYSTEM — GUI MODULE

PURPOSE
  Professor authentication, roster and grade management, quiz publication, question editing, grade locking, and reports.

DEPENDENCIES
  - PyQt6.
  - Project main.py must provide CSV/data functions, shared styling, category metadata, and quiz validation helpers.

FUNCTION / METHOD INDEX
  make_eye_icon: lines 90-125 (function)
  AddStudentDialog: lines 128-145 (class)
  AddStudentDialog.__init__: lines 129-142 (method)
  AddStudentDialog.get_data: lines 144-145 (method)
  QuizDialog: lines 148-193 (class)
  QuizDialog.__init__: lines 149-180 (method)
  QuizDialog.update_quiz_id_preview: lines 182-183 (method)
  QuizDialog.get_data: lines 185-193 (method)
  QuestionDialog: lines 196-272 (class)
  QuestionDialog.__init__: lines 197-242 (method)
  QuestionDialog.toggle_choice_fields: lines 244-261 (method)
  QuestionDialog.get_data: lines 263-272 (method)
  QuestionManagerWindow: lines 275-383 (class)
  QuestionManagerWindow.__init__: lines 276-303 (method)
  QuestionManagerWindow.load_list: lines 305-321 (method)
  QuestionManagerWindow.add_question: lines 323-339 (method)
  QuestionManagerWindow.edit_question: lines 341-365 (method)
  QuestionManagerWindow.delete_question: lines 367-383 (method)
  QuizManagerWindow: lines 386-521 (class)
  QuizManagerWindow.__init__: lines 387-413 (method)
  QuizManagerWindow.load_table: lines 415-423 (method)
  QuizManagerWindow.create_quiz: lines 425-459 (method)
  QuizManagerWindow.manage_questions: lines 461-472 (method)
  QuizManagerWindow.toggle_publish: lines 474-498 (method)
  QuizManagerWindow.delete_quiz: lines 500-521 (method)
  ProfessorLogin: lines 524-627 (class)
  ProfessorLogin.__init__: lines 525-531 (method)
  ProfessorLogin.initUI: lines 533-586 (method)
  ProfessorLogin.toggle_password_visibility: lines 588-594 (method)
  ProfessorLogin.reset_password_field: lines 596-598 (method)
  ProfessorLogin.login: lines 600-614 (method)
  ProfessorLogin.back_to_portal: lines 616-622 (method)
  ProfessorLogin.closeEvent: lines 624-627 (method)
  ProfessorDashboard: lines 630-1068 (class)
  ProfessorDashboard.__init__: lines 631-640 (method)
  ProfessorDashboard.initUI: lines 642-705 (method)
  ProfessorDashboard.load_grade_table: lines 707-709 (method)
  ProfessorDashboard.populate_table_with_data: lines 711-748 (method)
  ProfessorDashboard.filter_students_by_name: lines 750-757 (method)
  ProfessorDashboard.export_grade_report: lines 759-779 (method)
  ProfessorDashboard.select_student: lines 781-785 (method)
  ProfessorDashboard._quiz_picker: lines 787-800 (method)
  ProfessorDashboard.add_student: lines 802-840 (method)
  ProfessorDashboard.import_students: lines 842-894 (method)
  ProfessorDashboard.edit_grade: lines 896-946 (method)
  ProfessorDashboard.delete_student: lines 948-976 (method)
  ProfessorDashboard.reopen_quiz: lines 978-1005 (method)
  ProfessorDashboard.lock_grade: lines 1007-1045 (method)
  ProfessorDashboard.quiz_manager: lines 1047-1049 (method)
  ProfessorDashboard.logout: lines 1051-1059 (method)
  ProfessorDashboard.closeEvent: lines 1061-1068 (method)

IMPORTANT BEHAVIOR / LIMITATIONS
  - The professor login uses the password hash stored in the auth CSV. Change the demo password before using real student data.
  - Deleting a quiz should remove its metadata, question bank, grade column, and lock column when main.delete_quiz_data is available.
  - CSV files do not provide safe multi-process transactions; simultaneous writes from multiple devices can still conflict.
"""
import sys
import os
import csv
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QComboBox,
    QHeaderView, QFormLayout, QDialogButtonBox, QSpinBox, QFileDialog,
    QAbstractItemView, QInputDialog, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt, QSize, QPointF
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QPen, QColor, QPainterPath

import main

def make_eye_icon(crossed: bool) -> QIcon:
    """Draw an eye icon; with crossed=True a diagonal slash is added (password hidden)."""
    scale = 3
    size = 24 * scale
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(scale, scale)

    pen = QPen(QColor("#111111"), 2)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    outline = QPainterPath()
    outline.moveTo(2, 12)
    outline.quadTo(12, 1, 22, 12)
    outline.quadTo(12, 23, 2, 12)
    painter.drawPath(outline)

    painter.setBrush(QColor("#111111"))
    painter.drawEllipse(QPointF(12, 12), 3.2, 3.2)

    if crossed:
        # light halo so the slash stays readable over the eye outline
        halo = QPen(QColor("#F1F5F9"), 5)
        halo.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(halo)
        painter.drawLine(QPointF(4.5, 4.5), QPointF(19.5, 19.5))
        painter.setPen(pen)
        painter.drawLine(QPointF(4.5, 4.5), QPointF(19.5, 19.5))

    painter.end()
    return QIcon(pixmap)


class AddStudentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        main.apply_app_icon(self)
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
        main.apply_app_icon(self)
        self.setWindowTitle("Create Quiz")
        self.setMinimumWidth(450)
        layout = QFormLayout(self)

        self.title_input = QLineEdit()
        self.category = QComboBox()
        self.category.addItems(main.CATEGORIES)

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
        self.quiz_id_preview.setText(main.generate_quiz_id(category))

    def get_data(self):
        category = self.category.currentText()
        return {
            "quiz_id": main.generate_quiz_id(category),
            "title": self.title_input.text().strip(),
            "category": category,
            "max_item": str(self.max_item.value()),
            "time_limit_minutes": str(self.time_limit.value()),
        }


class QuestionDialog(QDialog):
    def __init__(self, parent=None, existing=None):
        super().__init__(parent)
        main.apply_app_icon(self)
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
        for i, box in enumerate(self.choice_inputs):
            box.setPlaceholderText(f"Option {i + 1}")
            layout.addRow(f"Option {i + 1}:", box)
            self.choice_rows.append(layout.rowCount() - 1)

        self.correct_box = QComboBox()
        layout.addRow("Correct Answer Choice:", self.correct_box)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.type_box.currentTextChanged.connect(self.toggle_choice_fields)

        if existing:
            self.text_input.setText(existing.get("text", existing.get("question", "")))
            qtype_mapped = "Multiple Choice Question" if existing.get("qtype") == "MCQ" or len(existing.get("choices", [])) == 4 else "True or False"
            self.type_box.setCurrentText(qtype_mapped)
            choices = existing.get("choices", existing.get("options", []))
            for i, box in enumerate(self.choice_inputs):
                if i < len(choices):
                    box.setText(choices[i])
            
            c_idx = existing.get("correct_index", existing.get("correct_option_index", 0))
            self.toggle_choice_fields(self.type_box.currentText())
            if 0 <= c_idx < self.correct_box.count():
                self.correct_box.setCurrentIndex(c_idx)
        else:
            self.toggle_choice_fields(self.type_box.currentText())

    def toggle_choice_fields(self, qtype):
        is_mcq = (qtype == "Multiple Choice Question")
        form = self.layout()
        for row in self.choice_rows:
            form.setRowVisible(row, is_mcq)
        
        current_idx = self.correct_box.currentIndex()
        self.correct_box.clear()
        if is_mcq:
            self.correct_box.addItems(["Option 1", "Option 2", "Option 3", "Option 4"])
        else:
            self.correct_box.addItems(["True", "False"])

        if 0 <= current_idx < self.correct_box.count():
            self.correct_box.setCurrentIndex(current_idx)
        else:
            self.correct_box.setCurrentIndex(0)
        self.adjustSize()

    def get_data(self):
        qtype_ui = self.type_box.currentText()
        qtype = "MCQ" if qtype_ui == "Multiple Choice Question" else "TF"
        text = self.text_input.text().strip()
        if qtype == "MCQ":
            choices = [box.text().strip() for box in self.choice_inputs]
        else:
            choices = ["True", "False"]
        correct_index = self.correct_box.currentIndex()
        return {"qtype": qtype, "text": text, "choices": choices, "correct_index": correct_index}


class QuestionManagerWindow(QDialog):
    def __init__(self, quiz_id, quiz_title, parent=None):
        super().__init__(parent)
        main.apply_app_icon(self)
        self.quiz_id = quiz_id
        self.setWindowTitle(f"Questions — {quiz_title}")
        self.setMinimumSize(700, 520)
        layout = QVBoxLayout(self)

        self.count_label = QLabel()
        layout.addWidget(self.count_label)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Type", "Question", "Correct Answer"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table, 1)

        button_layout = QHBoxLayout()
        add_button = main.GradientButton("Add Question", clicked=self.add_question)
        edit_button = QPushButton("Edit Question", clicked=self.edit_question)
        delete_button = QPushButton("Delete Question", clicked=self.delete_question)
        close_button = QPushButton("Close", clicked=self.accept)
        for b in (add_button, edit_button, delete_button, close_button):
            button_layout.addWidget(b)
        layout.addLayout(button_layout)

        self.load_list()

    def load_list(self):
        questions = main.load_questions(self.quiz_id)
        self.count_label.setText(f"{len(questions)} question(s) saved. (Minimum 10 required before publishing.)")
        self.table.setRowCount(len(questions))
        for row, question in enumerate(questions):
            qtype_mapped = "Multiple Choice Question" if question.get("qtype") == "MCQ" or len(question.get("choices", [])) == 4 else "True or False"
            q_text = question.get("text", question.get("question", ""))
            
            choices = question.get("choices", question.get("options", []))
            c_idx = question.get("correct_index", question.get("correct_option_index", 0))
            correct_text = choices[c_idx] if 0 <= c_idx < len(choices) else "N/A"

            self.table.setItem(row, 0, QTableWidgetItem(qtype_mapped))
            self.table.setItem(row, 1, QTableWidgetItem(q_text))
            self.table.setItem(row, 2, QTableWidgetItem(correct_text))

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def add_question(self):
        dialog = QuestionDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()

        validation_error = main.validate_question(data) if hasattr(main, "validate_question") else (
            "Enter the question text and options." if not data["text"] or len(data["choices"]) < 2 else ""
        )
        if validation_error:
            QMessageBox.warning(self, "Invalid Question", validation_error)
            return

        questions = main.load_questions(self.quiz_id)
        questions.append(data)
        main.save_questions(self.quiz_id, questions)
        self.load_list()

    def edit_question(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Question Selected", "Select a question first.")
            return

        questions = main.load_questions(self.quiz_id)
        if row >= len(questions):
            return

        dialog = QuestionDialog(self, existing=questions[row])
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()

        validation_error = main.validate_question(data) if hasattr(main, "validate_question") else (
            "Enter the question text and options." if not data["text"] or len(data["choices"]) < 2 else ""
        )
        if validation_error:
            QMessageBox.warning(self, "Invalid Question", validation_error)
            return

        questions[row] = data
        main.save_questions(self.quiz_id, questions)
        self.load_list()

    def delete_question(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Question Selected", "Select a question first.")
            return

        questions = main.load_questions(self.quiz_id)
        if row >= len(questions):
            return

        reply = QMessageBox.question(self, "Delete Question", "Delete this question?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        questions.pop(row)
        main.save_questions(self.quiz_id, questions)
        self.load_list()


class QuizManagerWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        main.apply_app_icon(self)
        self.setWindowTitle("Professor — Quiz Manager")
        self.setMinimumSize(950, 560)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("QUIZ MANAGER"))

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Quiz ID", "Title", "Category", "Max Items", "Time Limit", "Published", "Date Published"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table, 1)
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        button_layout = QHBoxLayout()
        create_button = main.GradientButton("Create Quiz", clicked=self.create_quiz)
        questions_button = QPushButton("Manage Questions", clicked=self.manage_questions)
        publish_button = QPushButton("Publish / Unpublish", clicked=self.toggle_publish)
        delete_button = QPushButton("Delete Quiz", clicked=self.delete_quiz)

        for btn in (create_button, questions_button, publish_button, delete_button):
            button_layout.addWidget(btn)

        layout.addLayout(button_layout)
        self.load_table()

    def load_table(self):

        quizzes = main.load_quizzes()
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

        quizzes = main.load_quizzes()
        if any(quiz["quiz_id"] == data["quiz_id"] for quiz in quizzes):
            QMessageBox.warning(self, "Duplicate Quiz ID", "That Quiz ID already exists.")
            return

        data["published"], data["date_published"] = "no", ""
        quizzes.append(data)
        main.save_quizzes(quizzes)

        students = main.load_students()
        if students:
            fields = main.get_student_fields()
            if data["quiz_id"] not in fields:
                fields.append(data["quiz_id"])
            for student in students:
                if data["quiz_id"] not in student:
                    student[data["quiz_id"]] = ""
            main.write_csv(main.STUDENTS_CSV, students, fields)

        self.load_table()
        QMessageBox.information(self, "Quiz Created", f"Quiz '{data['quiz_id']}' created successfully.\nUse \"Manage Questions\" to build its question bank before publishing.")

    def manage_questions(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Quiz Selected", "Select a quiz first.")
            return

        quizzes = main.load_quizzes()
        if row >= len(quizzes):
            return

        quiz = quizzes[row]
        QuestionManagerWindow(quiz["quiz_id"], quiz["title"], self).exec()

    def toggle_publish(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Quiz Selected", "Select a quiz first.")
            return

        quizzes = main.load_quizzes()
        if row >= len(quizzes):
            return

        quiz = quizzes[row]
        if quiz["published"] == "yes":
            quiz["published"], quiz["date_published"] = "no", ""
        else:
            question_count = len(main.load_questions(quiz["quiz_id"]))
            required = main.required_questions(quiz) if hasattr(main, "required_questions") else max(10, int(quiz.get("max_item", 10) or 10))
            if question_count < required:
                QMessageBox.warning(self, "Not Enough Questions",
                    f"'{quiz['title']}' has {question_count} question(s). Add at least {required} before publishing.")
                return
            quiz["published"] = "yes"
            quiz["date_published"] = main.get_spaced_now()

        main.save_quizzes(quizzes)
        self.load_table()

    def delete_quiz(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Quiz Selected", "Select a quiz first.")
            return

        quizzes = main.load_quizzes()
        if row >= len(quizzes):
            return

        quiz = quizzes[row]
        reply = QMessageBox.question(self, "Delete Quiz", f"Delete quiz '{quiz['title']}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Delete metadata, question bank, grades and lock column together when helper exists.
        if hasattr(main, "delete_quiz_data"):
            main.delete_quiz_data(quiz["quiz_id"])
        else:
            quizzes.pop(row)
            main.save_quizzes(quizzes)
        self.load_table()


class ProfessorLogin(QWidget):
    def __init__(self, launcher_window=None):
        super().__init__()
        main.apply_app_icon(self)
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

        self.eye_open_icon = make_eye_icon(crossed=False)
        self.eye_closed_icon = make_eye_icon(crossed=True)

        self.toggle_pw_button = QPushButton()
        self.toggle_pw_button.setObjectName("BtnSecondary")
        self.toggle_pw_button.setCheckable(True)
        self.toggle_pw_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_pw_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.toggle_pw_button.setStyleSheet("padding: 0px;")
        self.toggle_pw_button.setIcon(self.eye_closed_icon)
        self.toggle_pw_button.setIconSize(QSize(22, 22))
        self.toggle_pw_button.setToolTip("Show password")
        self.toggle_pw_button.setFixedSize(48, self.password_input.sizeHint().height())
        self.toggle_pw_button.toggled.connect(self.toggle_password_visibility)

        password_row = QHBoxLayout()
        password_row.setSpacing(8)
        password_row.addWidget(self.password_input, 1)
        password_row.addWidget(self.toggle_pw_button)
        layout.addLayout(password_row)

        login_button = main.GradientButton("Login", clicked=self.login)
        layout.addWidget(login_button)

        back_button = QPushButton("Back to Portal", clicked=self.back_to_portal)
        back_button.setObjectName("BtnSecondary")
        layout.addWidget(back_button)

        hint_text = (
            "Demo password: jabaiskript"
            if main.is_default_password()
            else "Use your configured professor password."
        )
        hint = QLabel(hint_text)
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: gray;")
        layout.addWidget(hint)

        layout.addStretch()

    def toggle_password_visibility(self, visible):
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Normal if visible else QLineEdit.EchoMode.Password
        )
        self.toggle_pw_button.setIcon(self.eye_open_icon if visible else self.eye_closed_icon)
        self.toggle_pw_button.setToolTip("Hide password" if visible else "Show password")
        self.password_input.setFocus()

    def reset_password_field(self):
        self.password_input.clear()
        self.toggle_pw_button.setChecked(False)

    def login(self):
        password = self.password_input.text()
        if password == "":
            QMessageBox.warning(self, "Missing Password", "Please enter the professor password.")
            return
        saved = main.read_csv(main.AUTH_CSV)
        if not saved:
            QMessageBox.critical(self, "Authentication Error", "Professor authentication data was not found.")
            return
        if main.hash_password(password) == saved[0]["password_hash"]:
            self.hide()
            self.dashboard = ProfessorDashboard(self, self.launcher_window)
            self.dashboard.show()
        else:
            QMessageBox.warning(self, "Access Denied", "Incorrect professor password.")

    def back_to_portal(self):
        self.reset_password_field()
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
        main.apply_app_icon(self)
        self.login_window = login_window
        self.launcher_window = launcher_window
        self.setWindowTitle("Professor Dashboard")
        self.resize(1100, 700)
        self.selected_student_id = None
        self.initUI()
        self.load_grade_table()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(15)

        header_layout = QHBoxLayout()
        title = QLabel("PROFESSOR DASHBOARD")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #111111;")
        
        header_layout.addStretch()
        header_layout.addWidget(title)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

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

        btn_grid = QGridLayout()
        btn_grid.setSpacing(12)

        btn_add = main.GradientButton("Add Student", clicked=self.add_student)
        btn_import = main.GradientButton("Import CSV", clicked=self.import_students)
        btn_edit = main.GradientButton("Edit Grade", clicked=self.edit_grade)
        btn_delete = main.GradientButton("Delete Student", clicked=self.delete_student)

        btn_export = main.GradientButton("Export Grade Report", clicked=self.export_grade_report)
        btn_reopen = main.GradientButton("Reopen Quiz", clicked=self.reopen_quiz)
        btn_lock = main.GradientButton("Lock Grade", clicked=self.lock_grade)
        btn_quiz_mgr = main.GradientButton("Quiz Manager", clicked=self.quiz_manager)

        btn_grid.addWidget(btn_add, 0, 0)
        btn_grid.addWidget(btn_import, 0, 1)
        btn_grid.addWidget(btn_edit, 0, 2)
        btn_grid.addWidget(btn_delete, 0, 3)

        btn_grid.addWidget(btn_export, 1, 0)
        btn_grid.addWidget(btn_reopen, 1, 1)
        btn_grid.addWidget(btn_lock, 1, 2)
        btn_grid.addWidget(btn_quiz_mgr, 1, 3)

        main_layout.addLayout(btn_grid)

        bottom_layout = QHBoxLayout()
        self.status_label = QLabel("Select a student row to perform student-specific actions.")
        
        btn_logout = main.GradientButton("Logout", clicked=self.logout)
        btn_logout.setFixedWidth(140)

        bottom_layout.addWidget(self.status_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(btn_logout)
        main_layout.addLayout(bottom_layout)

    def load_grade_table(self):
        self.search_input.clear()
        self.populate_table_with_data(main.load_students())

    def populate_table_with_data(self, students):
        quizzes = main.load_quizzes()
        quiz_title_by_id = {q["quiz_id"]: q.get("title", q["quiz_id"]) for q in quizzes}

        self.student_table.clear()
        if not students:
            self.student_table.setRowCount(0)
            self.student_table.setColumnCount(2)
            self.student_table.setHorizontalHeaderLabels(["Student ID", "Name"])
            return

        all_fields = main.get_student_fields()
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

            total_score, total_possible, remark = main.compute_total_and_remark(student, quizzes)
            total_col = 2 + len(quiz_columns)
            score_text = f"{total_score} / {total_possible}" if total_possible else "-"
            self.student_table.setItem(row_index, total_col, QTableWidgetItem(score_text))
            self.student_table.setItem(row_index, total_col + 1, QTableWidgetItem(remark))

        self.student_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def filter_students_by_name(self, query):
        query = query.strip().lower()
        students = main.load_students()
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
            students = main.load_students()
            quizzes = main.load_quizzes()
            fields = main.get_student_fields() + ["Total Score", "Remarks"]
            
            export_rows = []
            for s in students:
                row_copy = s.copy()
                t_score, t_poss, remark = main.compute_total_and_remark(s, quizzes)
                row_copy["Total Score"] = f"{t_score}/{t_poss}"
                row_copy["Remarks"] = remark
                export_rows.append(row_copy)
                
            main.write_csv(filename, export_rows, fields)
            QMessageBox.information(self, "Export Successful", f"Grade report exported successfully to:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export report:\n{e}")

    def select_student(self, row, column):
        item = self.student_table.item(row, 0)
        if item:
            self.selected_student_id = item.text()
            self.status_label.setText(f"Selected Student ID: {self.selected_student_id}")

    def _quiz_picker(self, student, exclude_locked=False):
        quizzes = {q["quiz_id"]: q for q in main.load_quizzes()}
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

        students, retired = main.load_students(), main.load_retired_ids()
        if student_id in {s["student_id"] for s in students}:
            QMessageBox.warning(self, "Duplicate ID", "This Student ID already exists.")
            return
        if student_id in {s["student_id"] for s in retired}:
            QMessageBox.warning(self, "Retired ID", "This Student ID was previously deleted and cannot be reused.")
            return

        new_student = {"student_id": student_id, "name": name}
        quizzes = main.load_quizzes()
        for quiz in quizzes:
            if quiz["quiz_id"] not in new_student:
                new_student[quiz["quiz_id"]] = ""

        students.append(new_student)
        existing_fields = main.get_student_fields()

        for quiz in quizzes:
            if quiz["quiz_id"] not in existing_fields:
                existing_fields.append(quiz["quiz_id"])

        for student in students:
            for field in existing_fields:
                if field not in student:
                    student[field] = ""

        main.write_csv(main.STUDENTS_CSV, students, existing_fields)
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

            students, retired = main.load_students(), main.load_retired_ids()
            active_ids = {s["student_id"] for s in students}
            retired_ids = {s["student_id"] for s in retired}
            quizzes, fields = main.load_quizzes(), main.get_student_fields()
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

            main.write_csv(main.STUDENTS_CSV, students, fields)
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

        students = main.load_students()
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

        quiz_info = next((q for q in main.load_quizzes() if q.get("quiz_id") == quiz_id), None)
        try:
            maximum = int(quiz_info.get("max_item", 999999)) if quiz_info else 999999
        except (TypeError, ValueError):
            maximum = 999999
        score, ok = QInputDialog.getInt(self, "Edit Grade", f"Enter score for {label} (0–{maximum}):", int(current) if current.isdigit() else 0, 0, max(0, maximum), 1)
        if not ok:
            return

        for record in students:
            if record["student_id"] == self.selected_student_id:
                record[quiz_id] = str(score)
                break

        fields = main.get_student_fields()
        if lock_field not in fields:
            fields.append(lock_field)

        for record in students:
            if lock_field not in record:
                record[lock_field] = ""

        main.write_csv(main.STUDENTS_CSV, students, fields)
        self.load_grade_table()
        QMessageBox.information(self, "Grade Updated", "The student's grade has been updated.")

    def delete_student(self):
        if not self.selected_student_id:
            QMessageBox.warning(self, "No Student Selected", "Select a student first.")
            return

        reply = QMessageBox.question(self, "Delete Student", f"Delete Student ID {self.selected_student_id}?\n\nThe ID will be retired and cannot be reused.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        students = main.load_students()
        deleted_student, remaining = None, []
        for student in students:
            if student["student_id"] == self.selected_student_id:
                deleted_student = student
            else:
                remaining.append(student)

        if deleted_student is None:
            return

        main.save_students(remaining)

        retired = main.load_retired_ids()
        retired.append({"student_id": self.selected_student_id, "date_retired": main.get_spaced_now()})
        main.save_retired_ids(retired)

        self.selected_student_id = None
        self.load_grade_table()
        QMessageBox.information(self, "Student Deleted", "Student deleted and ID retired.")

    def reopen_quiz(self):
        if not self.selected_student_id:
            QMessageBox.warning(self, "No Student Selected", "Select a student first.")
            return

        students = main.load_students()
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

        main.save_students(students)
        self.load_grade_table()
        QMessageBox.information(self, "Quiz Reopened", "The quiz is now available again for this student.")

    def lock_grade(self):
        if not self.selected_student_id:
            QMessageBox.warning(self, "No Student Selected", "Select a student first.")
            return

        students = main.load_students()
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

        fields = main.get_student_fields()
        if lock_field not in fields:
            fields.append(lock_field)

        for record in students:
            if lock_field not in record:
                record[lock_field] = ""

        main.write_csv(main.STUDENTS_CSV, students, fields)
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
        self.login_window.reset_password_field()
        if self.launcher_window:
            self.login_window.hide()
            self.launcher_window.show()
        else:
            self.login_window.show()
        event.accept()
