#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# CLASSES & METHODS:
# - AddStudentDialog: __init__(), get_data()
# - QuizDialog: __init__(), update_quiz_id_preview(), get_data()
# - QuestionDialog: __init__(), toggle_choice_fields(), get_data()
# - ProfessorLogin: __init__(), initUI(), login(), back_to_portal(), closeEvent()
# - ProfessorDashboard: __init__(), initUI(), load_grade_table(), populate_table_with_data(),
#                       filter_students_by_name(), export_grade_report(), select_student(),
#                       _quiz_picker(), add_student(), import_students(), edit_grade(),
#                       delete_student(), reopen_quiz(), lock_grade(), quiz_manager(),
#                       logout(), closeEvent()
# - QuizManagerWindow: __init__(), load_table(), create_quiz(), manage_questions(),
#                       toggle_publish(), delete_quiz()
# - QuestionManagerWindow: __init__(), load_list(), add_question(), edit_question(), delete_question()
#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

import sys
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QApplication, QPushButton, QLineEdit, QLabel, QMessageBox,
    QTableWidget, QTableWidgetItem, QFileDialog, QComboBox, QSpinBox,
    QDialog, QFormLayout, QDialogButtonBox, QVBoxLayout, QHBoxLayout,
    QHeaderView, QInputDialog, QAbstractItemView,
)
from PyQt6.QtCore import Qt
import csv

from PROFESSOR_FUNCTS import (
    ensure_files, hash_password, read_csv, write_csv, get_student_fields,
    load_students, save_students, load_retired_ids, save_retired_ids,
    load_quizzes, save_quizzes, load_questions, save_questions,
    generate_quiz_id, compute_total_and_remark,
    STUDENTS_FILE, AUTH_FILE, CATEGORIES,
)

ensure_files()

class AddStudentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
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
        self.setWindowTitle("Create Quiz")
        self.setMinimumWidth(450)
        layout = QFormLayout(self)

        self.title_input = QLineEdit()
        self.category = QComboBox()
        self.category.addItems(CATEGORIES)

        self.quiz_id_preview = QLabel()
        self.quiz_id_preview.setStyleSheet("font-weight: bold; color: #1a5fb4;")
        self.category.currentTextChanged.connect(self.update_quiz_id_preview)

        self.max_item = QSpinBox()
        self.max_item.setRange(1, 999)
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
            box.setPlaceholderText(f"Choice {i + 1}")
            layout.addRow(f"Choice {i + 1}:", box)
            self.choice_rows.append(layout.rowCount() - 1)

        self.correct_box = QSpinBox()
        self.correct_box.setRange(1, 4)
        layout.addRow("Correct Choice # (1=True for T/F):", self.correct_box)

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
            self.correct_box.setValue(existing.get("correct_index", 0) + 1)

        self.toggle_choice_fields(self.type_box.currentText())

    def toggle_choice_fields(self, qtype):
        is_mcq = (qtype == "Multiple Choice Question")
        form = self.layout()
        for row in self.choice_rows:
            form.setRowVisible(row, is_mcq)
        self.correct_box.setRange(1, 4 if is_mcq else 2)
        self.adjustSize()

    def get_data(self):
        qtype_ui = self.type_box.currentText()
        qtype = "MCQ" if qtype_ui == "Multiple Choice Question" else "TF"
        text = self.text_input.text().strip()
        if qtype == "MCQ":
            choices = [box.text().strip() for box in self.choice_inputs if box.text().strip()]
        else:
            choices = ["True", "False"]
        correct_index = self.correct_box.value() - 1
        return {"qtype": qtype, "text": text, "choices": choices, "correct_index": correct_index}

class ProfessorLogin(QWidget):
    def __init__(self, launcher_window=None):
        super().__init__()
        self.launcher_window = launcher_window
        self.setWindowTitle("Professor Login — HD Portal")
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

        login_button = QPushButton("Login", clicked=self.login)
        layout.addWidget(login_button)

        back_button = QPushButton("Back to Portal", clicked=self.back_to_portal)
        layout.addWidget(back_button)

        hint = QLabel("Demo password: jabaiskript")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: gray;")
        layout.addWidget(hint)

        layout.addStretch()
        self.show()

    def login(self):
        password = self.password_input.text()
        if password == "":
            QMessageBox.warning(self, "Missing Password", "Please enter the professor password.")
            return
        saved = read_csv(AUTH_FILE)
        if not saved:
            QMessageBox.critical(self, "Authentication Error", "Professor authentication data was not found.")
            return
        if hash_password(password) == saved[0]["password_hash"]:
            self.hide()
            self.dashboard = ProfessorDashboard(self, self.launcher_window)
            self.dashboard.show()
        else:
            QMessageBox.warning(self, "Access Denied", "Incorrect professor password.")

    # ibabalik sa Teacher/Student picker kung galing sa newMAIN_LOL.py / main launcher
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
        self.login_window = login_window
        self.launcher_window = launcher_window
        self.setWindowTitle("Professor Dashboard — HD Standard Layout")
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

        # Student Name Search Bar Integration
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
        row1.addWidget(QPushButton("Add Student", clicked=self.add_student))
        row1.addWidget(QPushButton("Import CSV", clicked=self.import_students))
        row1.addWidget(QPushButton("Delete Student", clicked=self.delete_student))
        row1.addWidget(QPushButton("Export Grade Report", clicked=self.export_grade_report))
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
                    display = f"{value} \U0001F512"
                self.student_table.setItem(row_index, 2 + col_offset, QTableWidgetItem(display))

            total_score, total_possible, remark = compute_total_and_remark(student, quizzes)
            total_col = 2 + len(quiz_columns)
            score_text = f"{total_score} / {total_possible}" if total_possible else "-"
            self.student_table.setItem(row_index, total_col, QTableWidgetItem(score_text))
            self.student_table.setItem(row_index, total_col + 1, QTableWidgetItem(remark))

        self.student_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def filter_students_by_name(self, query):
        """Allows professor to search students by name instead of ID."""
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
        retired.append({"student_id": self.selected_student_id, "date_retired": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
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
            self.close()  # closeEvent() ang magbabalik sa portal/login

    def closeEvent(self, event):
        self.login_window.password_input.clear()
        if self.launcher_window:
            self.login_window.hide()
            self.launcher_window.show()
        else:
            self.login_window.show()
        event.accept()

class QuizManagerWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
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
        create_button = QPushButton("Create Quiz", clicked=self.create_quiz)
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
            QMessageBox.warning(self, "Invalid Quiz", "The project requires at least 10 questions/items.")
            return

        quizzes = load_quizzes()
        if any(quiz["quiz_id"] == data["quiz_id"] for quiz in quizzes):
            QMessageBox.warning(self, "Duplicate Quiz ID", "That Quiz ID already exists. Try again.")
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
            quiz["date_published"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
        QMessageBox.information(self, "Quiz Deleted", "Quiz metadata has been deleted.")

class QuestionManagerWindow(QDialog):
    def __init__(self, quiz_id, quiz_title, parent=None):
        super().__init__(parent)
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
        add_button = QPushButton("Add Question", clicked=self.add_question)
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

    def add_question(self):
        dialog = QuestionDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()

        if not data["text"] or len(data["choices"]) < 2:
            QMessageBox.warning(self, "Missing Information", "Enter the question text and options.")
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

        if not data["text"] or len(data["choices"]) < 2:
            QMessageBox.warning(self, "Missing Information", "Enter the question text and options.")
            return

        questions[row] = data
        save_questions(self.quiz_id, questions)
        self.load_list()
        QMessageBox.information(self, "Question Updated", "The question has been updated.")

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