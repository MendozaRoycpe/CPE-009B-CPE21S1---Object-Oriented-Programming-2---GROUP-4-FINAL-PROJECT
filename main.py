import sys
from PyQt6.QtWidgets import QWidget, QApplication, QPushButton, QLabel

#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# FUNCTIONS / METHODS LIST:
# - RoleSelect: __init__(), initUI(), _reuse_or_create(), open_teacher(),
#               open_student(), closeEvent()
#
# Single entry point for the whole Group 4 quiz system. Imports both
# ProfessorLogin (from teacher_system.py) and StudentLogin (from
# Student_system.py) instead of redefining anything — same "class of
# teacher and students... imported/used on another file" setup as
# main.py -> registration.py in the earlier course exercise, just with
# two importable classes and a role picker instead of one.
#
# Logout / window-close from either portal returns HERE (the role
# selection window), not only to the professor/student login screen.
#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

from teacher_system import ProfessorLogin
from Student_system import StudentLogin


# unang window na lalabas — dito pipiliin kung Teacher o Student ang gagamit
class RoleSelect(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quiz System — Group 4")
        self.setGeometry(400, 250, 350, 200)
        self._closing = False  # para hindi mag-loop ang closeEvent ng login windows
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

    # kung buhay pa ang dating login window, i-reuse; kung na-X na, gumawa ng bago
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

    # itatago ang role-select window tapos buksan ang Professor login
    def open_teacher(self):
        self.hide()
        self._reuse_or_create("teacher_login", lambda: ProfessorLogin(portal_window=self))

    # itatago ang role-select window tapos buksan ang Student login
    def open_student(self):
        self.hide()
        self._reuse_or_create("student_login", lambda: StudentLogin(portal_window=self))

    # kapag isinara ang portal mismo, isara na rin ang buong app
    def closeEvent(self, event):
        self._closing = True
        app = QApplication.instance()
        if app is not None:
            app.quit()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = RoleSelect()
    sys.exit(app.exec())