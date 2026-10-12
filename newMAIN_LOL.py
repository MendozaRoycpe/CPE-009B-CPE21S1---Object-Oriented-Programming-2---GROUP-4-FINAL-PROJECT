#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# FUNCTIONS / METHODS LIST:
# - MainLauncher: __init__(), initUI(), _reuse_or_create(), open_professor(),
#                 open_student(), closeEvent()
#
# Alternate HD entry point. Same role as main.py's RoleSelect window, but
# it launches PROFESSOR_GUI.ProfessorLogin / STUDENT_GUI.StudentLogin.
# Logout from either dashboard is supposed to return HERE.
# Run this file OR main.py — huwag pareho nang sabay.
#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

import sys
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt

from PROFESSOR_GUI import ProfessorLogin
from STUDENT_GUI import StudentLogin

class MainLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quiz System — Main HD Launcher")
        self.resize(480, 280)
        self._closing = False
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 35, 40, 35)
        layout.setSpacing(15)

        title = QLabel("QUIZ SYSTEM PORTAL")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel("Please select your role to continue:")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        prof_button = QPushButton("Professor Portal", clicked=self.open_professor)
        prof_button.setStyleSheet("font-size: 14px; padding: 12px;")
        layout.addWidget(prof_button)

        student_button = QPushButton("Student Portal", clicked=self.open_student)
        student_button.setStyleSheet("font-size: 14px; padding: 12px;")
        layout.addWidget(student_button)

        layout.addStretch()
        self.show()

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
        self.hide()
        self._reuse_or_create("prof_login", lambda: ProfessorLogin(launcher_window=self))

    def open_student(self):
        self.hide()
        self._reuse_or_create("student_login", lambda: StudentLogin(launcher_window=self))

    # kapag isinara ang portal mismo, isara na rin ang buong app
    def closeEvent(self, event):
        self._closing = True
        app = QApplication.instance()
        if app is not None:
            app.quit()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    launcher = MainLauncher()
    sys.exit(app.exec())