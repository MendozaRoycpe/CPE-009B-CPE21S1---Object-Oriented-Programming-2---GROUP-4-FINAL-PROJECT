from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, 
    QDialog, QComboBox, QTextEdit, QFrame, QHeaderView
)

import config
from utils import read_csv, write_csv, load_questions, save_questions, apply_fade_in
from styles import QUIZZIZ_STYLE

class QuestionEditorDialog(QDialog):
    def __init__(self, question_data=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet(QUIZZIZ_STYLE)
        self.setWindowTitle("Edit Question" if question_data else "Add New Question")
        self.setMinimumSize(500, 500)
        self.question_data = question_data or {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Question Type Selector
        layout.addWidget(QLabel("<b>Question Type:</b>"))
        self.cmb_type = QComboBox()
        self.cmb_type.addItems(["Multiple Choice (4 Options)", "True / False"])
        
        # Detect type if editing
        opts = self.question_data.get("options", ["", "", "", ""])
        if len(opts) == 2 or (len(opts) == 4 and opts[0] == "True" and opts[1] == "False" and not opts[2] and not opts[3]):
            self.cmb_type.setCurrentIndex(1)
            
        self.cmb_type.currentIndexChanged.connect(self.on_type_changed)
        layout.addWidget(self.cmb_type)

        # Question Text
        layout.addWidget(QLabel("<b>Question Text:</b>"))
        self.txt_q = QTextEdit()
        self.txt_q.setPlaceholderText("Enter question prompt here...")
        self.txt_q.setPlainText(self.question_data.get("question", ""))
        layout.addWidget(self.txt_q)

        # Answer Choices
        layout.addWidget(QLabel("<b>Answer Choices:</b>"))
        self.option_inputs = []
        existing_options = self.question_data.get("options", ["", "", "", ""])

        for i in range(4):
            inp = QLineEdit()
            inp.setPlaceholderText(f"Option {i+1}")
            if i < len(existing_options):
                inp.setText(existing_options[i])
            self.option_inputs.append(inp)
            layout.addWidget(inp)

        # Correct Answer Dropdown
        layout.addWidget(QLabel("<b>Correct Answer:</b>"))
        self.cmb_correct = QComboBox()
        layout.addWidget(self.cmb_correct)

        # Buttons
        btn_box = QHBoxLayout()
        btn_save = QPushButton("Save Question")
        btn_save.clicked.connect(self.save)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("BtnSecondary")
        btn_cancel.clicked.connect(self.reject)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

        self.on_type_changed()

    def on_type_changed(self):
        is_tf = self.cmb_type.currentIndex() == 1
        
        if is_tf:
            self.option_inputs[0].setText("True")
            self.option_inputs[1].setText("False")
            self.option_inputs[0].setEnabled(False)
            self.option_inputs[1].setEnabled(False)
            self.option_inputs[2].hide()
            self.option_inputs[3].hide()

            self.cmb_correct.clear()
            self.cmb_correct.addItems(["Option 1: True", "Option 2: False"])
        else:
            self.option_inputs[0].setEnabled(True)
            self.option_inputs[1].setEnabled(True)
            self.option_inputs[2].show()
            self.option_inputs[3].show()

            if self.option_inputs[0].text() == "True":
                self.option_inputs[0].clear()
            if self.option_inputs[1].text() == "False":
                self.option_inputs[1].clear()

            self.cmb_correct.clear()
            self.cmb_correct.addItems(["Option 1", "Option 2", "Option 3", "Option 4"])

        curr_idx = self.question_data.get("correct_option_index", 0)
        if curr_idx < self.cmb_correct.count():
            self.cmb_correct.setCurrentIndex(curr_idx)

    def save(self):
        q_text = self.txt_q.toPlainText().strip()
        is_tf = self.cmb_type.currentIndex() == 1

        if is_tf:
            options = ["True", "False"]
        else:
            options = [inp.text().strip() for inp in self.option_inputs]

        if not q_text or any(not opt for opt in options):
            QMessageBox.warning(self, "Validation Error", "Please fill in the question and options.")
            return

        self.question_data = {
            "question": q_text,
            "options": options,
            "correct_option_index": self.cmb_correct.currentIndex()
        }
        self.accept()


class QuizQuestionsManager(QDialog):
    def __init__(self, quiz_id, quiz_title, parent=None):
        super().__init__(parent)
        self.setStyleSheet(QUIZZIZ_STYLE)
        self.quiz_id = quiz_id
        self.quiz_title = quiz_title
        self.setWindowTitle(f"Manage Questions - {self.quiz_title}")
        self.resize(650, 480)
        
        self.questions = load_questions(self.quiz_id)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        lbl = QLabel(f"<h2>Questions for: {self.quiz_title}</h2>")
        layout.addWidget(lbl)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["#", "Question", "Correct Choice"])
        header = self.table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        btn_add = QPushButton("+ Add Question")
        btn_add.clicked.connect(self.add_question)

        btn_edit = QPushButton("Edit Question")
        btn_edit.setObjectName("BtnSecondary")
        btn_edit.clicked.connect(self.edit_question)

        btn_delete = QPushButton("Delete Question")
        btn_delete.setObjectName("BtnDanger")
        btn_delete.clicked.connect(self.delete_question)

        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_delete)
        layout.addLayout(btn_layout)

        self.refresh_table()

    def refresh_table(self):
        self.table.setRowCount(0)
        for i, q in enumerate(self.questions):
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(i + 1)))
            self.table.setItem(row, 1, QTableWidgetItem(q.get("question", "")))
            
            c_idx = q.get("correct_option_index", 0)
            opts = q.get("options", [])
            c_text = opts[c_idx] if c_idx < len(opts) else "N/A"
            self.table.setItem(row, 2, QTableWidgetItem(f"Option {c_idx+1}: {c_text}"))

    def add_question(self):
        dlg = QuestionEditorDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.questions.append(dlg.question_data)
            save_questions(self.quiz_id, self.questions)
            self.update_quiz_question_count()
            self.refresh_table()

    def edit_question(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Selection Required", "Please select a question to edit.")
            return

        dlg = QuestionEditorDialog(question_data=self.questions[row], parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.questions[row] = dlg.question_data
            save_questions(self.quiz_id, self.questions)
            self.refresh_table()

    def delete_question(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Selection Required", "Please select a question to delete.")
            return

        reply = QMessageBox.question(self, "Confirm Delete", "Delete this question?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.questions.pop(row)
            save_questions(self.quiz_id, self.questions)
            self.update_quiz_question_count()
            self.refresh_table()

    def update_quiz_question_count(self):
        quizzes = read_csv(config.QUIZZES_FILE)
        for q in quizzes:
            if q.get("quiz_id") == self.quiz_id:
                q["total_questions"] = str(len(self.questions))
                break
        write_csv(config.QUIZZES_FILE, quizzes, config.QUIZ_FIELDS)


class ProfessorDashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(QUIZZIZ_STYLE)
        self.setWindowTitle("Quizizz Teacher Studio")
        self.resize(800, 500)
        self.init_ui()
        self.load_quizzes()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        header_lbl = QLabel("<h1>⚡ Teacher Control Dashboard</h1>")
        layout.addWidget(header_lbl)

        card = QFrame()
        card.setObjectName("CardPanel")
        card_layout = QHBoxLayout(card)

        self.txt_title = QLineEdit()
        self.txt_title.setPlaceholderText("Quiz Title")

        self.txt_duration = QLineEdit()
        self.txt_duration.setPlaceholderText("Duration (Mins)")
        self.txt_duration.setFixedWidth(130)

        btn_add = QPushButton("+ Create Quiz")
        btn_add.clicked.connect(self.add_quiz)

        card_layout.addWidget(self.txt_title)
        card_layout.addWidget(self.txt_duration)
        card_layout.addWidget(btn_add)
        layout.addWidget(card)

        self.table_quizzes = QTableWidget(0, 4)
        self.table_quizzes.setHorizontalHeaderLabels(["Quiz ID", "Title", "Duration", "Questions"])
        header = self.table_quizzes.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table_quizzes)

        actions_layout = QHBoxLayout()
        
        btn_edit_q = QPushButton("✏️ Edit Questions & Content")
        btn_edit_q.clicked.connect(self.manage_questions)

        btn_delete_quiz = QPushButton("🗑 Delete Quiz")
        btn_delete_quiz.setObjectName("BtnDanger")
        btn_delete_quiz.clicked.connect(self.delete_quiz)

        actions_layout.addWidget(btn_edit_q)
        actions_layout.addStretch()
        actions_layout.addWidget(btn_delete_quiz)
        layout.addLayout(actions_layout)

        apply_fade_in(self)

    def load_quizzes(self):
        self.table_quizzes.setRowCount(0)
        quizzes = read_csv(config.QUIZZES_FILE)
        
        for q in quizzes:
            row = self.table_quizzes.rowCount()
            self.table_quizzes.insertRow(row)
            self.table_quizzes.setItem(row, 0, QTableWidgetItem(q.get("quiz_id", "")))
            self.table_quizzes.setItem(row, 1, QTableWidgetItem(q.get("title", "")))
            self.table_quizzes.setItem(row, 2, QTableWidgetItem(f"{q.get('duration_minutes', '10')} mins"))
            self.table_quizzes.setItem(row, 3, QTableWidgetItem(f"{q.get('total_questions', '0')} Qs"))

    def add_quiz(self):
        title = self.txt_title.text().strip()
        duration = self.txt_duration.text().strip()

        if not title or not duration:
            QMessageBox.warning(self, "Input Error", "Please provide a Quiz Title and Duration.")
            return

        quizzes = read_csv(config.QUIZZES_FILE)
        quiz_id = f"QUIZ_{len(quizzes) + 1:03d}"

        new_quiz = {
            "quiz_id": quiz_id,
            "title": title,
            "subject": "General",
            "total_questions": "0",
            "duration_minutes": duration
        }

        quizzes.append(new_quiz)
        write_csv(config.QUIZZES_FILE, quizzes, config.QUIZ_FIELDS)

        self.txt_title.clear()
        self.txt_duration.clear()
        self.load_quizzes()

    def manage_questions(self):
        row = self.table_quizzes.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Selection Required", "Please select a quiz to manage.")
            return

        id_item = self.table_quizzes.item(row, 0)
        title_item = self.table_quizzes.item(row, 1)

        quiz_id = id_item.text() if id_item else ""
        quiz_title = title_item.text() if title_item else ""

        dlg = QuizQuestionsManager(quiz_id, quiz_title, parent=self)
        dlg.exec()
        self.load_quizzes()

    def delete_quiz(self):
        row = self.table_quizzes.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Selection Required", "Please select a quiz to delete.")
            return

        id_item = self.table_quizzes.item(row, 0)
        quiz_id = id_item.text() if id_item else ""

        reply = QMessageBox.question(self, "Delete Quiz", f"Delete quiz {quiz_id}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            quizzes = read_csv(config.QUIZZES_FILE)
            quizzes = [q for q in quizzes if q.get("quiz_id") != quiz_id]
            write_csv(config.QUIZZES_FILE, quizzes, config.QUIZ_FIELDS)
            self.load_quizzes()
