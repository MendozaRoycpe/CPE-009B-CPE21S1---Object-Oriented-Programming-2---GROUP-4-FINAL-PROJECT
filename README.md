<!-- PyQuiz README | Group 4 OOPB Project -->

<div align="center">

<a href="https://github.com/MendozaRoycpe">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=24&pause=1000&color=007ACC&center=true&vCenter=true&width=650&lines=WELCOME+TO+OUR+REPOSITORY;Group+4+%E2%80%A2+PyQuiz+Assessment+System;Python+%E2%80%A2+PyQt6+%E2%80%A2+OOP" alt="Typing effect" />
</a>

<br><br>

# PyQuiz — Student Assessment & Evaluation System

**Group 4 Laboratory Project · Object-Oriented Programming (OOPB) · Desktop GUI**

A Python desktop application for managing students, creating quizzes, conducting timed assessments, and recording quiz scores.

<br>

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-41CD52?style=for-the-badge&logo=qt&logoColor=white)
![Storage](https://img.shields.io/badge/Storage-CSV%20%2B%20JSON-007ACC?style=for-the-badge)
![Project](https://img.shields.io/badge/Project-Group%204-8A2BE2?style=for-the-badge)

</div>

---

## Navigation

- [Project Overview](#-project-overview)
- [Features and Roles](#-features-and-roles)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Data Storage](#-data-storage)
- [Installation and Setup](#-installation-and-setup)
- [Running the Application](#-running-the-application)
- [GitHub Team Workflow](#-github-team-workflow)
- [Important Notes](#-important-notes)

---

## 📌 Project Overview

PyQuiz is a desktop quiz system built for the **Object-Oriented Programming (OOPB)** laboratory project. It uses **Python** and **PyQt6** to provide a graphical interface for two user roles:

- **Professor:** manages student records, quiz settings, question banks, and grades.
- **Student:** signs in using a student ID and takes quizzes made available by the professor.

The application stores roster and quiz metadata in CSV files and stores each quiz's question bank in a JSON file. These files are created inside the local `data/` directory when the application initializes.

## 🛡️ Features and Roles

| Role | Main capabilities |
| :--- | :--- |
| **Professor** | Password-protected access; view and manage student records; import or add students; edit grades; manage quizzes and question banks; configure quiz item counts and time limits; publish or remove quizzes. |
| **Student** | Sign in using a student ID; view available published quizzes; answer questions in the quiz interface; take a timed attempt; view the resulting score and feedback provided by the application. |
| **Session tracking** | Records student sessions by device and logs conflicting session attempts for review. |

Question banks support **Multiple Choice (MCQ)** and **True or False (TF)** question types in the current project design.

> **Implementation note:** Available features depend on the versions of `main.py`, `professor_system.py`, and `student_system.py` in your local project. Test the complete workflow after replacing or merging files.

## 🧰 Technology Stack

| Component | Technology |
| :--- | :--- |
| Programming language | Python |
| Desktop interface | PyQt6 |
| Student roster and quiz metadata | CSV |
| Code editor | Visual Studio Code (recommended) |
| Version control | Git and GitHub |
| Optional executable packaging | PyInstaller |

## 🧩 Project Structure

The core project layout should look similar to this:

```text
project-folder/
├── main.py                  # Application entry point and shared data utilities
├── professor_system.py      # Professor login and professor-side interface
├── student_system.py       # Student login and student-side quiz interface
├── TIPlogo.ico              # Optional application icon
├── README.md                # Project documentation
└── data/                    # Created automatically when the app initializes
    ├── students.csv
    ├── retired_ids.csv
    ├── quizzes.csv
    ├── professor_auth.csv
    ├── sessions.csv
    ├── session_conflicts.csv
    ├── questions/
    │   └── <quiz_id>.json
    └── assets/
        ├── spin_up.png
        └── spin_down.png
```

Some files and folders under `data/` are generated automatically. Do not create the question JSON files manually unless you are following the application's expected question format.

## 📂 Data Storage

PyQuiz uses local files rather than a database server.

| File | Purpose |
| :--- | :--- |
| `students.csv` | Student IDs, names, and dynamic quiz-grade columns. Some versions also use `locked_<quiz_id>` columns to track locked attempts. |
| `retired_ids.csv` | IDs retired after student removal, where that feature is enabled. |
| `quizzes.csv` | Quiz ID, title, category, maximum item count, time limit, publication status, and publication date. |
| `professor_auth.csv` | Stores the professor password hash. |
| `sessions.csv` | Tracks student sessions and device information. |
| `session_conflicts.csv` | Records conflicting session attempts. |
| `questions/<quiz_id>.json` | Stores the question bank for a quiz. |

### Data backup and privacy

- Back up the `data/` folder before changing code or replacing project files.
- Do not commit real student names, IDs, grades, password files, or question banks containing answer keys to a public repository.
- Add `data/` to `.gitignore` if the repository should contain source code only.
- CSV files are plain text. Anyone who can access them may be able to read their contents.
- The project uses a SHA-256 hash for the professor password. This is a course-project implementation, **not a production-grade authentication system**; a salted password-hashing scheme would be more appropriate for a real deployment.

## 💻 Installation and Setup

### 1. Install Python

Install a Python version supported by your installed PyQt6 release. Confirm Python and pip are available:

```bash
python --version
python -m pip --version
```

### 2. Open the project folder

Open the folder containing `main.py`, `professor_system.py`, and `student_system.py` in Visual Studio Code or a terminal.

### 3. Install PyQt6

```bash
python -m pip install PyQt6
```

If your group uses a virtual environment, activate it before installing the dependency.

### 4. Confirm the project files

Make sure the three Python modules are in the same folder. The `TIPlogo.ico` icon is optional; the application can use its default icon if the file is absent.

## ▶️ Running the Application

From the project folder, run:

```bash
python main.py
```

The launcher should open with options to enter the Professor Portal or Student Portal.

On the first run, the application initializes the `data/` directory and required CSV files. Depending on the initialization code, a new installation may also receive starter quiz data and a demo student.

**Before using real records:** run the app with test data first and verify that student login, quiz publication, quiz submission, grade saving, and professor grade management all work as expected.

## 🤝 GitHub Team Workflow

### Clone the repository

If you have not downloaded the repository yet:

```bash
git clone https://github.com/MendozaRoycpe/GROUP-4---STUDENT-QUIZ-SYSTEM.git
cd GROUP-4---STUDENT-QUIZ-SYSTEM
```

If you already have a local copy, open a terminal in that project folder.

### Configure Git (one time per computer)

Use your own GitHub identity:

```bash
git config --global user.name "Your GitHub Username"
git config --global user.email "your_email@example.com"
```

### Before editing

```bash
git pull origin main
git status
```

### Commit and push your changes

```bash
git add README.md main.py professor_system.py student_system.py
git commit -m "Update quiz system documentation and code"
git push origin main
```

If you changed other files, stage those files as appropriate. Pull and resolve any merge conflicts before pushing; do not overwrite another team member's work.

### Recommended `.gitignore`

Create a `.gitignore` file in the repository root:

```gitignore
# Local application records and question banks
data/

# Python-generated files
__pycache__/
*.py[cod]

# Local virtual environments
.venv/
venv/

# IDE settings
.vscode/
```

If `data/` has already been committed, adding it to `.gitignore` alone does not remove it from Git tracking. Coordinate with the team before removing tracked data from the repository.

## 🧪 Testing Checklist

Before presenting the project, test these flows with sample data:

- [ ] The application starts and displays the launcher.
- [ ] Professor login accepts the configured credentials and rejects an incorrect password.
- [ ] The professor can add a test student and manage a quiz.
- [ ] A quiz cannot be published unless its question requirements are satisfied.
- [ ] The student can sign in and see quizzes available to them.
- [ ] A timed quiz can be submitted and the score is saved correctly.
- [ ] A completed quiz cannot be retaken when attempt locking is enabled.
- [ ] Editing or deleting a quiz does not unintentionally remove unrelated grades.
- [ ] Session conflicts are recorded and the session state is handled correctly.
- [ ] Existing project data is preserved after restarting the application.

## 🚧 Known Limitations

- Data is stored in local CSV and JSON files, so simultaneous writes and multi-computer use may cause consistency issues.
- Session tracking is a basic project-level safeguard, not a secure anti-cheating system.
- SHA-256 hashing without a dedicated password-hashing scheme is not sufficient for production authentication.
- The final set of completed features should be confirmed against the actual code and tested locally before presenting or deploying the project.

---

<div align="center">

**Group 4 · OOPB Laboratory Project**

<sub>PyQuiz — Student Assessment & Evaluation System</sub>

</div>
