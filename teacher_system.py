import sys, csv, os, hashlib
from datetime import datetime
from PyQt6.QtWidgets import QWidget, QApplication, QPushButton, QLineEdit, QLabel, QMessageBox, QTableWidget, QTableWidgetItem, QFileDialog, QComboBox, QSpinBox, QDialog, QFormLayout, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QHeaderView, QInputDialog, QAbstractItemView
from PyQt6.QtCore import Qt

#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# FUNCTIONS / METHODS LIST:
# - ensure_files()
# - hash_password(password)
# - read_csv(filename)
# - write_csv(filename, rows, fieldnames)
# - get_student_fields()
# - load_students()
# - save_students(students)
# - load_retired_ids()
# - save_retired_ids(rows)
# - load_quizzes()
# - save_quizzes(quizzes)
#
# CLASSES & METHODS:
# - AddStudentDialog: __init__(), get_data()
# - QuizDialog: __init__(), get_data()
# - ProfessorLogin: __init__(), initUI(), login()
# - ProfessorDashboard: __init__(), initUI(), load_grade_table(), select_student(),
#                       add_student(), import_students(), edit_grade(),
#                       delete_student(), reopen_quiz(), lock_grade(),
#                       quiz_manager(), logout()
# - QuizManagerWindow: __init__(), load_table(), create_quiz(), toggle_publish(), delete_quiz()
#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# File settings / configurations
DATA_FOLDER = "data"
STUDENTS_FILE = os.path.join(DATA_FOLDER, "students.csv")
RETIRED_FILE = os.path.join(DATA_FOLDER, "retired_ids.csv") # <-- Note: Dito napupunta yung mga deleted Student IDs para hindi na ma-reuse
QUIZZES_FILE = os.path.join(DATA_FOLDER, "quizzes.csv")
AUTH_FILE = os.path.join(DATA_FOLDER, "professor_auth.csv") #<--NOTE: para sa professor password hash, if gagawa ng bagong professor password,
#palitan lang yung default na "jabaiskript" sa ensure_files() function, tapos buksan nyo yung sa data na folder? then delete yung professor_auth.csv 
# para ma-generate ulit sa bagong password hash
SESSIONS_FILE = os.path.join(DATA_FOLDER, "sessions.csv")

DEFAULT_STUDENT_FIELDS = ["student_id", "name"]
QUIZ_FIELDS = ["quiz_id", "title", "category", "max_item", "time_limit_minutes", "published", "date_published"]

# gawa ng data folder tapos initialize lang ng default csv files kung wala pa
def ensure_files():
    os.makedirs(DATA_FOLDER, exist_ok=True)
    if not os.path.isfile(STUDENTS_FILE):
        with open(STUDENTS_FILE, "w", newline="", encoding="utf-8") as file:
            csv.DictWriter(file, fieldnames=DEFAULT_STUDENT_FIELDS).writeheader()
            
    if not os.path.isfile(RETIRED_FILE):
        with open(RETIRED_FILE, "w", newline="", encoding="utf-8") as file:
            csv.DictWriter(file, fieldnames=["student_id", "date_retired"]).writeheader()
            
    if not os.path.isfile(QUIZZES_FILE):
        with open(QUIZZES_FILE, "w", newline="", encoding="utf-8") as file:
            csv.DictWriter(file, fieldnames=QUIZ_FIELDS).writeheader()
            
    if not os.path.isfile(AUTH_FILE):
        with open(AUTH_FILE, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["password_hash"])
            writer.writeheader()
            writer.writerow({"password_hash": hash_password("jabaiskript")})

# para ma-hash string yung password using sha256 para safe;;; thanks online sources
def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

# para mag-read lang ng csv file tapos ibabalik niya list of dictionaries
def read_csv(filename):
    if not os.path.isfile(filename): return []
    with open(filename, "r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))

# para mag-write/save ng rows sa csv file gamit yung fieldnames
def write_csv(filename, rows, fieldnames):
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

# kukunin lang yung mga headers or column fields ng student records
def get_student_fields():
    students = read_csv(STUDENTS_FILE)
    return list(students[0].keys()) if students else DEFAULT_STUDENT_FIELDS.copy()

# kuhanin lahat ng student records sa csv
def load_students():
    return read_csv(STUDENTS_FILE)

# i-save yung list ng new students pabalik sa csv
def save_students(students):
    fields = get_student_fields()
    if not fields: fields = DEFAULT_STUDENT_FIELDS.copy()
    write_csv(STUDENTS_FILE, students, fields)
    
# kailangan ito para sa mga na-delete na student IDs para hindi ma-reuse
def load_retired_ids():
    return read_csv(RETIRED_FILE)

# save ng list ng mga retired student IDs
def save_retired_ids(rows):
    write_csv(RETIRED_FILE, rows, ["student_id", "date_retired"])

# load ng list ng mga quizzes galing sa csv
def load_quizzes():
    return read_csv(QUIZZES_FILE)

# save ng list ng quiz data pabalik sa csv
def save_quizzes(quizzes):
    write_csv(QUIZZES_FILE, quizzes, QUIZ_FIELDS)

# modal dialog pop-up para sa pag add ng bagong student
class AddStudentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Student")
        self.setFixedSize(400, 180)
        layout = QFormLayout(self)
        self.id_input = QLineEdit()
        self.name_input = QLineEdit()
        layout.addRow("Student ID:", self.id_input)
        layout.addRow("Student Name:", self.name_input)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    # return lang yung ininput na student id tsaka name as tuple
    def get_data(self):
        return (self.id_input.text().strip(), self.name_input.text().strip())

# modal window pop-up para sa pag-setup or gawa ng quiz
class QuizDialog(QDialog):
    # setup lang ng mga input fields tulad ng subject category, timer, and max items
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Quiz")
        self.setFixedSize(450, 260)
        layout = QFormLayout(self)
        self.quiz_id, self.title = QLineEdit(), QLineEdit()
        self.category = QComboBox()
        self.category.addItems(["English","Math","Science","Computer"]) # <-- NOTE: Kung gusto magdagdag ng bagong subjects/category, dito lang i-append sa array list
        self.max_item = QSpinBox()
        self.max_item.setRange(1, 999)#<-- NOTE: Pwede nyo babaan sa 10 kung gusto nyo lang sa testing, pero requirement ng project ay minimum 10 questions per quiz eh, but leme max this shi
        self.time_limit = QSpinBox()
        self.time_limit.setRange(1, 999)#<-- NOTE: time in mins mo focus Roy ah
        layout.addRow("Quiz ID:", self.quiz_id)
        layout.addRow("Quiz Title:", self.title)
        layout.addRow("Category:", self.category)
        layout.addRow("Maximum Items:", self.max_item)
        layout.addRow("Time Limit (minutes):", self.time_limit)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    # ibabalik yung dictionary na naglalaman ng quiz info
    def get_data(self):
        return {"quiz_id": self.quiz_id.text().strip(), "title": self.title.text().strip(), "category": self.category.currentText(), "max_item": str(self.max_item.value()), "time_limit_minutes": str(self.time_limit.value())}

# login window para sa prof authentication
class ProfessorLogin(QWidget):
    # setup ng window size at title para sa login page
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Professor Login")
        self.setGeometry(400, 200, 450, 300)
        self.initUI()

    # gawa ng labels, text box password, at login button sa window
    def initUI(self):
        QLabel("QUIZ SYSTEM - PROFESSOR", self).move(100, 35)
        QLabel("Password:", self).move(70, 100)
        self.password_input = QLineEdit(self)
        self.password_input.setGeometry(150, 95, 220, 30)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        login_button = QPushButton("Login", self)
        login_button.setGeometry(150, 150, 220, 35)
        login_button.clicked.connect(self.login)
        QLabel("Demo password: jabaiskript", self).move(115, 215) # <-- NOTE: Kapag pinalitan niyo ang password sa top, palitan niyo rin itong text display para hindi nakakalito
        self.show()

    # checking if the password is correct, if yes, open the dashboard window#comapring to dun sa naka hash kaya if mag papalit password sundan yung note sa taas
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
            self.dashboard = ProfessorDashboard(self)
            self.dashboard.show()
        else:
            QMessageBox.warning(self, "Access Denied", "Incorrect professor password.")

# main window dashboard para sa pag navigate ng students, grades, at quizzes
class ProfessorDashboard(QWidget):
    # constructor para i-initialize dashboard screen
    def __init__(self, login_window):
        super().__init__()
        self.login_window = login_window
        self.setWindowTitle("Professor Dashboard")
        self.setGeometry(150, 100, 1100, 700)
        self.selected_student_id = None
        self.initUI()
        self.load_grade_table()

    # ilalagay lahat ng buttons, student table view, tsaka action controls sa dashboard
    def initUI(self):
        QLabel("PROFESSOR DASHBOARD", self).move(25, 20)
        self.student_table = QTableWidget(self)
        self.student_table.setGeometry(25, 70, 1050, 300)
        self.student_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.student_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.student_table.cellClicked.connect(self.select_student)

        # Dashboard Action Buttons
        QPushButton("Add Student", self, clicked=self.add_student).move(25, 400)
        QPushButton("Import CSV", self, clicked=self.import_students).move(145, 400)
        QPushButton("Edit Grade", self, clicked=self.edit_grade).move(265, 400)
        QPushButton("Delete Student", self, clicked=self.delete_student).move(385, 400)
        QPushButton("Reopen Quiz", self, clicked=self.reopen_quiz).move(525, 400)
        QPushButton("Lock Grade", self, clicked=self.lock_grade).move(645, 400)
        QPushButton("Refresh", self, clicked=self.load_grade_table).move(765, 400)
        QPushButton("Quiz Manager", self, clicked=self.quiz_manager).move(885, 400)
        QPushButton("Logout", self, clicked=self.logout).move(25, 470)

        self.status_label = QLabel("Select a student row to perform student-specific actions.", self)
        self.status_label.move(25, 520)

    # ila-load dito sa table yung lahat ng student records at grades
    def load_grade_table(self):
        students = load_students()
        self.student_table.clear()
        if not students:
            self.student_table.setRowCount(0)
            self.student_table.setColumnCount(2)
            self.student_table.setHorizontalHeaderLabels(["Student ID", "Name"])
            return

        fields = list(students[0].keys())
        self.student_table.setColumnCount(len(fields))
        self.student_table.setRowCount(len(students))
        self.student_table.setHorizontalHeaderLabels(fields)

        for row_index, student in enumerate(students):
            for column_index, field in enumerate(fields):
                self.student_table.setItem(row_index, column_index, QTableWidgetItem(student.get(field, "")))

        self.student_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    # para ma-select kung sinong student ID yung iki-click sa table row
    def select_student(self, row, column):
        item = self.student_table.item(row, 0)
        if item:
            self.selected_student_id = item.text()
            self.status_label.setText(f"Selected Student ID: {self.selected_student_id}")

    # lalabas yung dialog box para makapag add ng bagong student manually
    def add_student(self):
        dialog = AddStudentDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted: return
        student_id, name = dialog.get_data()

        if not student_id or not name:
            QMessageBox.warning(self, "Missing Information", "Student ID and Name are required.")
            return

        students, retired = load_students(), load_retired_ids()
        if student_id in {student["student_id"] for student in students}:
            QMessageBox.warning(self, "Duplicate ID", "This Student ID already exists.")
            return
        if student_id in {student["student_id"] for student in retired}: # <-- NOTE: If ayaw pumayag pumasok ng ID, ibig sabihin nasa retired_ids.csv na siya. Burahin niyo doon kung gusto niyo ire-use.
            QMessageBox.warning(self, "Retired ID", "This Student ID was previously deleted and cannot be reused.")
            return

        new_student = {"student_id": student_id, "name": name}
        quizzes = load_quizzes()
        for quiz in quizzes:
            if quiz["quiz_id"] not in new_student: new_student[quiz["quiz_id"]] = ""

        students.append(new_student)
        existing_fields = get_student_fields()

        for quiz in quizzes:
            if quiz["quiz_id"] not in existing_fields: existing_fields.append(quiz["quiz_id"])

        for student in students:
            for field in existing_fields:
                if field not in student: student[field] = ""

        write_csv(STUDENTS_FILE, students, existing_fields)
        self.load_grade_table()
        QMessageBox.information(self, "Student Added", f"{name} has been added successfully.")

    # para mag import ng panibagong listahan ng students gamit ang external csv file
    def import_students(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Select Student CSV", "", "CSV Files (*.csv)") # <-- NOTE: Siguraduhin na ang CSV file ay may header na "student_id" at "name" kung hindi mag-e-error.
        if not filename: return

        try:
            with open(filename, "r", newline="", encoding="utf-8-sig") as file: imported = list(csv.DictReader(file))
            if not imported:
                QMessageBox.warning(self, "Empty File", "The selected CSV file has no student records.")
                return

            if not {"student_id", "name"}.issubset(imported[0].keys()):
                QMessageBox.warning(self, "Invalid CSV", "The CSV must contain student_id and name columns.")
                return

            students, retired = load_students(), load_retired_ids()
            active_ids = {student["student_id"] for student in students}
            retired_ids = {student["student_id"] for student in retired}
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
                    if quiz["quiz_id"] not in fields: fields.append(quiz["quiz_id"])

                students.append(record)
                active_ids.add(student_id)
                added += 1

            for student in students:
                for field in fields:
                    if field not in student: student[field] = ""

            write_csv(STUDENTS_FILE, students, fields)
            self.load_grade_table()
            message = f"{added} student(s) imported."
            if rejected: message += "\n\nRejected IDs:\n" + "\n".join(rejected)
            QMessageBox.information(self, "Import Complete", message)

        except Exception as error:
            QMessageBox.critical(self, "Import Error", f"Could not import the CSV.\n\n{error}")

    # mag bubukas ng prompt para baguhin or palitan score ng piniling student sa specific quiz
    def edit_grade(self):
        if not self.selected_student_id:
            QMessageBox.warning(self, "No Student Selected", "Select a student first.")
            return

        students = load_students()
        student = next((item for item in students if item["student_id"] == self.selected_student_id), None)
        if student is None: return

        quiz_columns = [field for field in student.keys() if field not in ["student_id", "name"]]
        if not quiz_columns:
            QMessageBox.information(self, "No Quizzes", "There are no quiz grade columns yet.")
            return

        quiz_id, ok = QInputDialog.getItem(self, "Select Quiz", "Quiz:", quiz_columns, 0, False)
        if not ok: return

        current = student.get(quiz_id, "")
        lock_field = f"locked_{quiz_id}"
        if student.get(lock_field, "") == "yes": # <-- NOTE: Pag naka-lock ang grade, nakasulat "yes" sa column na `locked_<quiz_id>` sa students.csv
            QMessageBox.warning(self, "Grade Locked", "This grade has been permanently locked.")
            return

        score, ok = QInputDialog.getInt(self, "Edit Grade", f"Enter score for {quiz_id}:", int(current) if current.isdigit() else 0, 0, 999999, 1)
        if not ok: return

        for record in students:
            if record["student_id"] == self.selected_student_id:
                record[quiz_id] = str(score)
                break

        fields = get_student_fields()
        if lock_field not in fields: fields.append(lock_field)

        for record in students:
            if lock_field not in record: record[lock_field] = ""

        write_csv(STUDENTS_FILE, students, fields)
        self.load_grade_table()
        QMessageBox.information(self, "Grade Updated", "The student's grade has been updated.")

    # ire-remove yung student sa active list at ililipat yung ID sa retired_ids.csv
    def delete_student(self):
        if not self.selected_student_id:
            QMessageBox.warning(self, "No Student Selected", "Select a student first.")
            return

        reply = QMessageBox.question(self, "Delete Student", f"Delete Student ID {self.selected_student_id}?\n\nThe ID will be retired and cannot be reused.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes: return

        students = load_students()
        deleted_student, remaining = None, []
        for student in students:
            if student["student_id"] == self.selected_student_id: deleted_student = student
            else: remaining.append(student)

        if deleted_student is None: return

        self.last_deleted_student = deleted_student
        save_students(remaining)

        retired = load_retired_ids()
        retired.append({"student_id": self.selected_student_id, "date_retired": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}) # <-- NOTE: Nilalagyan ng timestamp kapag nade-delete
        save_retired_ids(retired)

        self.selected_student_id = None
        self.load_grade_table()
        QMessageBox.information(self, "Student Deleted", "Student deleted and ID retired.")

    # buburahin yung quiz attempt/score para ma-retake uli ng napiling student
    def reopen_quiz(self):
        if not self.selected_student_id:
            QMessageBox.warning(self, "No Student Selected", "Select a student first.")
            return

        students = load_students()
        student = next((item for item in students if item["student_id"] == self.selected_student_id), None)
        if not student: return

        quiz_columns = [field for field in student.keys() if field not in ["student_id", "name"] and not field.startswith("locked_")]
        if not quiz_columns:
            QMessageBox.information(self, "No Quizzes", "There are no quiz columns.")
            return

        quiz_id, ok = QInputDialog.getItem(self, "Reopen Quiz", "Select quiz:", quiz_columns, 0, False)
        if not ok: return

        if student.get(f"locked_{quiz_id}", "") == "yes": # <-- NOTE: Kapag naka-lock na, ayaw din nitong mag-reopen. Kailangan burahin nang manual yung "yes" sa CSV para ma-unlock.
            QMessageBox.warning(self, "Grade Locked", "This grade is permanently locked and cannot be reopened.")
            return

        for record in students:
            if record["student_id"] == self.selected_student_id:
                record[quiz_id] = "" # <-- NOTE: Ginagawang blank lang yung score sa students.csv
                break

        save_students(students)
        self.load_grade_table()
        QMessageBox.information(self, "Quiz Reopened", "The quiz is now available again for this student.")

    # i-lock na permanently yung grade ng student para hindi na mabago pa
    def lock_grade(self):
        if not self.selected_student_id:
            QMessageBox.warning(self, "No Student Selected", "Select a student first.")
            return

        students = load_students()
        student = next((item for item in students if item["student_id"] == self.selected_student_id), None)
        if not student: return

        quiz_columns = [field for field in student.keys() if field not in ["student_id", "name"] and not field.startswith("locked_")]
        if not quiz_columns: return

        quiz_id, ok = QInputDialog.getItem(self, "Lock Grade", "Select quiz:", quiz_columns, 0, False)
        if not ok: return

        if student.get(quiz_id, "") == "":
            QMessageBox.warning(self, "No Grade", "This quiz has no grade yet.")
            return

        lock_field = f"locked_{quiz_id}"
        for record in students:
            if record["student_id"] == self.selected_student_id: record[lock_field] = "yes" # <-- NOTE: Dinadagdagan ng `locked_<quiz_id>` column tapos sineset sa "yes"

        fields = get_student_fields()
        if lock_field not in fields: fields.append(lock_field)

        for record in students:
            if lock_field not in record: record[lock_field] = ""

        write_csv(STUDENTS_FILE, students, fields)
        self.load_grade_table()
        QMessageBox.information(self, "Grade Locked", "The grade is now permanently locked.")

    # pag-click nito, bubukas yung hiwalay na quiz manager window dialog
    def quiz_manager(self):
        QuizManagerWindow(self).exec()
        self.load_grade_table()

    # ie-exit yung dashboard at ibabalik uli sa login screen interface
    def logout(self):
        reply = QMessageBox.question(self, "Logout", "Return to the professor login screen?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.close()
            self.login_window.password_input.clear() # <-- Clears password field on logout
            self.login_window.show()

# dialog window para sa pag create, publish, tsaka delete ng mga quiz
class QuizManagerWindow(QDialog):
    # setup ng layout buttons tsaka quiz details table view
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Professor - Quiz Manager")
        self.setMinimumSize(850, 500)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("QUIZ MANAGER"))

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Quiz ID", "Title", "Category", "Max Items", "Time Limit", "Published", "Date Published"])
        layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        create_button, publish_button = QPushButton("Create Quiz"), QPushButton("Publish / Unpublish")
        delete_button, refresh_button = QPushButton("Delete Quiz"), QPushButton("Refresh")

        create_button.clicked.connect(self.create_quiz)
        publish_button.clicked.connect(self.toggle_publish)
        delete_button.clicked.connect(self.delete_quiz)
        refresh_button.clicked.connect(self.load_table)

        for btn in (create_button, publish_button, delete_button, refresh_button):
            button_layout.addWidget(btn)

        layout.addLayout(button_layout)
        self.load_table()

    # ipapakita lahat ng list ng quizzes na naka-store sa quizzes.csv file
    def load_table(self):
        quizzes = load_quizzes()
        self.table.setRowCount(len(quizzes))
        for row, quiz in enumerate(quizzes):
            values = [quiz.get("quiz_id", ""), quiz.get("title", ""), quiz.get("category", ""), quiz.get("max_item", ""), quiz.get("time_limit_minutes", ""), quiz.get("published", ""), quiz.get("date_published", "")]
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    # para gumawa ng panibagong quiz entry tapos idadagdag sa list at csv
    def create_quiz(self):
        dialog = QuizDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted: return
        data = dialog.get_data()

        if not data["quiz_id"] or not data["title"]:
            QMessageBox.warning(self, "Missing Information", "Quiz ID and title are required.")
            return

        if int(data["max_item"]) < 10: # <-- NOTE: Naka-set sa minimum 10 items per requirement. Pwede babaan dito kung kailangan lang sa testing.
            QMessageBox.warning(self, "Invalid Quiz", "The project requires at least 10 questions/items.")
            return

        quizzes = load_quizzes()
        if any(quiz["quiz_id"] == data["quiz_id"] for quiz in quizzes):
            QMessageBox.warning(self, "Duplicate Quiz ID", "That Quiz ID already exists.")
            return

        data["published"], data["date_published"] = "no", ""
        quizzes.append(data)
        save_quizzes(quizzes)

        # Automatic na nilalagyan ng bagong column header sa students.csv base sa nilikhang Quiz ID
        students = load_students()
        if students:
            fields = get_student_fields()
            if data["quiz_id"] not in fields: fields.append(data["quiz_id"])
            for student in students:
                if data["quiz_id"] not in student: student[data["quiz_id"]] = ""
            write_csv(STUDENTS_FILE, students, fields)

        self.load_table()
        QMessageBox.information(self, "Quiz Created", "Quiz created successfully.\nQuestion-bank entry can be connected in the next stage.")

    # para mag-palit/toggle sa publish or unpublish state ng napiling quiz
    def toggle_publish(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Quiz Selected", "Select a quiz first.")
            return

        quizzes = load_quizzes()
        if row >= len(quizzes): return

        quiz = quizzes[row]
        if quiz["published"] == "yes":
            quiz["published"], quiz["date_published"] = "no", ""
        else:
            quiz["published"] = "yes"
            quiz["date_published"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        save_quizzes(quizzes)
        self.load_table()

    # tanggalin yung quiz entry sa metadata csv file
    def delete_quiz(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Quiz Selected", "Select a quiz first.")
            return

        quizzes = load_quizzes()
        if row >= len(quizzes): return

        quiz = quizzes[row]
        reply = QMessageBox.question(self, "Delete Quiz", f"Delete quiz '{quiz['title']}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes: return

        quizzes.pop(row)
        save_quizzes(quizzes)
        self.load_table()
        QMessageBox.information(self, "Quiz Deleted", "Quiz metadata has been deleted.")




# EXECUTE ORDER66
ensure_files()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = ProfessorLogin()
    login.show()
    sys.exit(app.exec())
    
    
# NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE
# TO DO LIST:
#buksan nyo yung read.me file ng github repo para sa instructions kung paano gamitin tong project, tapos ano pa need gawin lol
# NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE