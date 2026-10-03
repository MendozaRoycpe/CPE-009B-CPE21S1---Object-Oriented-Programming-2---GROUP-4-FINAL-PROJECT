from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QListWidgetItem, QPushButton, QMessageBox, QFrame
)

import config
from utils import read_csv, apply_fade_in
from styles import QUIZZIZ_STYLE
from quiz_window import QuizWindow

class StudentDashboard(QWidget):
    def __init__(self, student_id: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(QUIZZIZ_STYLE)
        self.student_id = student_id
        self.quiz_window_ref = None

        self.setWindowTitle(f"Student Portal - {self.student_id}")
        self.resize(600, 420)
        self.init_ui()
        self.load_quizzes()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel(f"<h1>🎮 Welcome, {self.student_id}!</h1>")
        layout.addWidget(header)

        card = QFrame()
        card.setObjectName("CardPanel")
        card_layout = QVBoxLayout(card)

        card_layout.addWidget(QLabel("<b>Available Quizzes:</b>"))
        self.list_quizzes = QListWidget()
        card_layout.addWidget(self.list_quizzes)

        layout.addWidget(card)

        btn_layout = QHBoxLayout()
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setObjectName("BtnSecondary")
        self.btn_refresh.clicked.connect(self.load_quizzes)

        self.btn_start = QPushButton("🚀 Join Quiz")
        self.btn_start.clicked.connect(self.start_quiz)

        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_start)
        
        layout.addLayout(btn_layout)
        apply_fade_in(self)

    def load_quizzes(self):
        self.list_quizzes.clear()
        quizzes = read_csv(config.QUIZZES_FILE)
        
        for q in quizzes:
            title = q.get("title", "Untitled")
            quiz_id = q.get("quiz_id", "")
            duration = q.get("duration_minutes", "10")
            count = q.get("total_questions", "0")
            
            item = QListWidgetItem(f"⚡ {title}  •  {count} Questions  •  ⏱️ {duration} mins")
            item.setData(100, quiz_id)
            self.list_quizzes.addItem(item)

    def start_quiz(self):
        selected = self.list_quizzes.currentItem()
        if not selected:
            QMessageBox.warning(self, "Selection Required", "Please choose a quiz from the list.")
            return

        quiz_id = selected.data(100)
        self.quiz_window_ref = QuizWindow(student_id=self.student_id, quiz_id=quiz_id)
        self.quiz_window_ref.show()
