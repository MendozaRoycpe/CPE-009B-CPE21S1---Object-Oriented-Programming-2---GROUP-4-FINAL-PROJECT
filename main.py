import sys
from PyQt6.QtWidgets import QWidget, QApplication, QPushButton, QLabel

#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# FUNCTIONS / METHODS LIST:
# - RoleSelect: __init__(), initUI(), open_teacher(), open_student()
#
# Single entry point for the whole Group 4 quiz system. Imports both
# ProfessorLogin (from teacher_system.py) and StudentLogin (from
# student_system.py) instead of redefining anything — same "class of
# teacher and students... imported/used on another file" setup as
# main.py -> registration.py in the earlier course exercise, just with
# two importable classes and a role picker instead of one.
#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

from teacher_system import ProfessorLogin
from Student_system import StudentLogin


# unang window na lalabas — dito pipiliin kung Teacher o Student ang gagamit
class RoleSelect(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quiz System — Group 4")
        self.setGeometry(400, 250, 350, 200)
        self.initUI()

    # ilalagay yung title at dalawang buttons para sa role selection
    def initUI(self):
        QLabel("QUIZ SYSTEM", self).move(130, 30)
        QLabel("Who are you?", self).move(120, 60)

        teacher_button = QPushButton("Teacher", self, clicked=self.open_teacher)
        teacher_button.setGeometry(75, 100, 200, 35)

        student_button = QPushButton("Student", self, clicked=self.open_student)
        student_button.setGeometry(75, 145, 200, 35)

        self.show()

    # itatago ang role-select window tapos buksan ang Professor login
    def open_teacher(self):
        self.hide()
        self.teacher_login = ProfessorLogin()
        self.teacher_login.show()

    # itatago ang role-select window tapos buksan ang Student login
    def open_student(self):
        self.hide()
        self.student_login = StudentLogin()
        self.student_login.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = RoleSelect()
    sys.exit(app.exec())