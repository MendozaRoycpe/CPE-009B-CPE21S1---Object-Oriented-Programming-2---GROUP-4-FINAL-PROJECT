<!-- DYNAMIC TYPING ANIMATION BANNER -->
<div align="center">

<a href="https://github.com/MendozaRoycpe">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=24&pause=1000&color=007ACC&center=true&vCenter=true&width=600&lines=WELCOME+TO+MY+REPOSITORY!;Group+4+%E2%80%A2+PyQuiz+OOPB+System;Python+3.14+%E2%80%A2+PyQt6+%E2%80%A2+Object-Oriented+Architecture" alt="Typing Effect" />
</a>

<br><br>

<h1>🎓 PyQuiz — Student Assessment & Evaluation System</h1>

<p align="center">
  <b>Group 4 Laboratory Project • Object-Oriented Programming (OOPB) • Desktop GUI Application</b>
</p>

<!-- INTERACTIVE NAVIGATION BUTTONS -->
<p align="center">
  <a href="#-system-architecture--roles">
    <img src="https://img.shields.io/badge/🛡️_Security_%26_Roles-View-007ACC?style=for-the-badge&logo=python&logoColor=white" alt="Roles">
  </a>
  <a href="#-data-entities--storage-schema">
    <img src="https://img.shields.io/badge/📂_Data_Schema-View-FF8C00?style=for-the-badge&logo=sqlite&logoColor=white" alt="Schema">
  </a>
  <a href="#-project-files">
    <img src="https://img.shields.io/badge/🧩_Project_Files-View-FF69B4?style=for-the-badge&logo=python&logoColor=white" alt="Files">
  </a>
  <a href="#-laptop-setup--step-by-step-guide">
    <img src="https://img.shields.io/badge/💻_Laptop_Setup_Guide-View-28A745?style=for-the-badge&logo=github&logoColor=white" alt="Setup">
  </a>
  <a href="#-implementation-roadmap">
    <img src="https://img.shields.io/badge/🚧_Implementation_Roadmap-View-8A2BE2?style=for-the-badge&logo=qt&logoColor=white" alt="Roadmap">
  </a>
</p>

</div>

---

## 📌 Interactive System Dashboard

<details open>
<summary><b>📘 Project Overview & Core Objectives (Click to toggle)</b></summary>
<br>

> **PyQuiz** is a desktop assessment system designed for **OOPB (Object-Oriented Programming)**. Built with **Python 3.14** and **PyQt6**, it provides a dual-role interface for **Professors** (roster management, quiz creation, grade locking) and **Students** (timed quiz taking, immediate feedback).

### 🎯 Key Engineering Objectives
* 🔒 **Role-Based Security Gate:** Password-authenticated Professor workspace with SHA-256 hashed credential checks (`professor_auth.csv`).
* ⏱️ **Real-Time Quiz Engine:** Active countdown timers with force-finalization on expiration or app closure.
* 🚫 **Concurrency & Anti-Cheating Control:** Single-device session locking via unique device IDs (`sessions.csv`), with conflicting login attempts logged to `session_conflicts.csv` for Professor review.
* ♻️ **Strict Lifecycle Controls:** Permanent student ID retirement system (`retired_ids.csv`) preventing duplicate or reused IDs.

</details>

<details open>
<summary><b>🛠️ Technology Stack & Requirements (Click to toggle)</b></summary>
<br>

<div align="center">

| Component | Technologies & Tools |
| :--- | :--- |
| **Core Runtime** | ![Python](https://img.shields.io/badge/-Python_3.14-3776AB?style=flat-square&logo=python&logoColor=white) |
| **GUI Framework** | ![PyQt6](https://img.shields.io/badge/-PyQt6-41CD52?style=flat-square&logo=qt&logoColor=white) |
| **Persistence Layer** | ![CSV](https://img.shields.io/badge/-Isolated_Flat_CSV_%2B_JSON_Engine-007ACC?style=flat-square) |
| **Packaging / Executable** | ![PyInstaller](https://img.shields.io/badge/-PyInstaller-FF6F00?style=flat-square) |
| **Tooling & VCS** | ![VS Code](https://img.shields.io/badge/-VS_Code-007ACC?style=flat-square&logo=visual-studio-code&logoColor=white) ![Git](https://img.shields.io/badge/-Git-F05032?style=flat-square&logo=git&logoColor=white) ![GitHub](https://img.shields.io/badge/-GitHub-181717?style=flat-square&logo=github&logoColor=white) |

</div>

</details>

---

<a name="-system-architecture--roles"></a>
## 🛡️ System Architecture & Roles

<details open>
<summary><b>🔑 Access Controls & Role Breakdown (Click to toggle)</b></summary>
<br>

| Role | Access Gate | Core Capability |
| :--- | :--- | :--- |
| **Professor** | **SHA-256 Password Required** | Owns roster and every quiz; views/edits grades; publishes quizzes with `max_item` and time limits (blocked under 10 questions); locks grades; adds, imports, and deletes students (ID retirement enforced); builds each quiz's question bank (MCQ/TF). |
| **Student** | **Student ID Only** *(No Password)* | Selects a category, then a published quiz available to them; answers under a countdown timer; attempt auto-finalizes on timeout or on closing the app; receives immediate raw score and answer key post-submission. |

> ⚠️ **Known gaps:** grade/undo history and a dedicated Session Alerts screen are not built yet — see [Implementation Roadmap](#-implementation-roadmap).

</details>

---

<a name="-data-entities--storage-schema"></a>
## 📂 Data Entities & Storage Schema

All application state files are isolated in the **`/data`** folder (created automatically on first run) to keep live grades out of version control — see the `.gitignore` note in [Laptop Setup](#-laptop-setup--step-by-step-guide).

<details open>
<summary><b>🗄️ File Layout & CSV Schema (Click to toggle)</b></summary>
<br>

```text
data/
 ├── students.csv           # Roster: student_id, name, plus one grade column + one locked_<quiz_id>
 │                          #   column per published quiz (grade blank = quiz still available)
 ├── retired_ids.csv        # student_id, date_retired — deleted student IDs, never reissued
 ├── quizzes.csv            # quiz_id, title, category, max_item, time_limit_minutes,
 │                          #   published, date_published
 ├── questions/             # One JSON file per quiz_id holding its MCQ/TF question bank
 │                          #   (e.g., questions/math1.json)
 ├── sessions.csv           # student_id, device_id, started_at — one row per logged-in student
 ├── session_conflicts.csv  # student_id, device_id, attempted_at — logged same-ID/second-device attempts
 └── professor_auth.csv     # SHA-256 hashed professor password
```

</details>

---

<a name="-project-files"></a>
## 🧩 Project Files

<details open>
<summary><b>🐍 Source Layout (Click to toggle)</b></summary>
<br>

| File | Role |
| :--- | :--- |
| `main.py` | Entry point — role-select window (Teacher / Student); imports the two classes below rather than redefining anything. |
| `teacher_system.py` | Professor side: `ProfessorLogin`, `ProfessorDashboard` (grade sheet, add/import/delete students, lock grades), `QuizManagerWindow`, `QuestionDialog` / `QuestionManagerWindow` (question bank), plus every shared CSV/JSON helper function. |
| `student_system.py` | Student side: `StudentLogin`, `StudentDashboard`, `TakeQuizWindow` (countdown timer, auto-finalize on timeout/close), `ResultWindow`. Imports its file/CSV helpers from `teacher_system.py` instead of duplicating them. |

Run any file on its own for testing (`python teacher_system.py` / `python student_system.py`), or run `main.py` for the normal combined entry point.

</details>

---

<a name="-laptop-setup--step-by-step-guide"></a>
## 💻 Laptop Setup & Team Collaboration Guide

<details open>
<summary><b>🤝 Step 1: GitHub Invitation & Authentication Setup (Click to toggle)</b></summary>
<br>

**1. Accept your repository invitation:**

👉 **[Click Here to Accept GitHub Invitation](https://github.com/MendozaRoycpe/GROUP-4---STUDENT-QUIZ-SYSTEM/invitations)**

**2. Authenticate Git on your laptop (one-time setup):**

```bash
git config --global user.name "Your GitHub Username"
git config --global user.email "your_email@example.com"
```

**3. Before you start any work — pull the latest team changes:**

```bash
git pull origin main
```

**4. After writing or updating a feature:**

```bash
# 1. Check which files changed
git status

# 2. Stage all changed files
git add .

# 3. Commit with a short, descriptive message
git commit -m "Added student login screen"

# 4. Push to GitHub
git push origin main
```

> ⚠️ Always `git pull` before you `git push` — a push that overwrites someone else's unpulled work is the most common way this goes wrong.

</details>

<details open>
<summary><b>🔗 Linking a Local Folder to GitHub (Click to toggle)</b></summary>
<br>

If you already have the project files on your laptop and need to connect that folder to the remote repository:

```bash
# 1. Open a terminal inside your local project folder
cd "path/to/your/local/folder"

# 2. Initialize a local Git repository (if not already initialized)
git init

# 3. Set your main branch name to main
git branch -M main

# 4. Link your local folder to the GitHub repository
git remote add origin https://github.com/MendozaRoycpe/GROUP-4---STUDENT-QUIZ-SYSTEM.git

# 5. Verify the remote connection
git remote -v

# 6. Fetch and merge the remote files (e.g., README.md) before pushing
git pull origin main --allow-unrelated-histories

# 7. Stage, commit, and push your local files
git add .
git commit -m "Initial commit from local folder"
git push -u origin main
```

</details>

<details open>
<summary><b>🚫 Keeping Live Data Out of the Repo (Click to toggle)</b></summary>
<br>

The `/data` folder holds live grades, the roster, and question banks (with answer keys) — it should never be committed. Create a `.gitignore` in the project root containing:

```text
data/
__pycache__/
*.pyc
```

If `/data` was already committed before adding this, remove it from tracking without deleting it locally:

```bash
git rm -r --cached data
git commit -m "Stop tracking data folder"
git push origin main
```

</details>

---

<a name="-implementation-roadmap"></a>
## 🚧 Implementation Roadmap

<details open>
<summary><b>✅ Completed (Click to toggle)</b></summary>
<br>

- **Professor:** password login, grade sheet, add/import students, edit grade, delete student with ID retirement, reopen quiz, lock grade, quiz manager (create / publish / delete), question bank editor
- **Student:** ID-only login, one-device-per-ID session tracking with conflict logging, category → quiz list → timed quiz → auto-finalize on timeout or app close, results screen with correct answers shown immediately
- **Unified launcher** (`main.py`) with Teacher / Student role select
- **Bug fix:** `students.csv` no longer silently drops quiz/lock columns when the roster has zero rows

</details>

<details open>
<summary><b>🔜 Still To Do (Click to toggle)</b></summary>
<br>

1. **Undo** — grade edits, student deletion, and quiz reopen currently write straight to disk; the agreed design needs undo available until the program closes or the grade is explicitly locked.
2. **Session Alerts screen** — `session_conflicts.csv` is being logged correctly, but nothing on the Professor side displays it yet.
3. **`.gitignore` + repo cleanup** — exclude `/data` before the next push (see above) if it hasn't been done yet.
4. **Formal multi-machine test pass** — concurrent students and edge cases (publishing under 10 questions, duplicate-ID rejection) have only been spot-checked, not run by the whole group on separate machines.
5. **Final wrap-up** — assign file ownership across the group, and check the finished build against the original activity brief.

</details>

---

<div align="center">
<sub>Group 4 • OOPB Laboratory Project • Maintained via GitHub collaboration</sub>
</div>
