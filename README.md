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
* 🚫 **Concurrency & Anti-Cheating Control:** Single-device session locking via unique device IDs (`sessions.csv`) and conflict reporting.
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
| **Persistence Layer** | ![CSV](https://img.shields.io/badge/-Isolated_Flat_CSV_Engine-007ACC?style=flat-square) |
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
| **Professor** | **SHA-256 Password Required** | Owns roster and every quiz; views/edits grades; publishes quizzes with `max_item` and time limits; locks/undoes grades; adds/deletes students; reviews session conflict alerts. |
| **Student** | **Student ID Only** *(No Password)* | Selects category and published quiz; answers under a countdown timer; receives immediate raw score and answer key post-submission. |

</details>

---

<a name="-data-entities--storage-schema"></a>
## 📂 Data Entities & Storage Schema

All application state files are isolated in the **`/data`** folder to keep live grades out of version control.

<details open>
<summary><b>🗄️ File Layout & CSV Schema (Click to toggle)</b></summary>
<br>

```text
data/
 ├── students.csv         # Active student roster & grades per published quiz
 ├── retired_ids.csv      # Log of deleted student IDs (prevents ID reuse)
 ├── quizzes.csv          # Global quiz registry & metadata
 ├── question_banks/      # Per-quiz MCQ/TF question files (e.g., QZ_101.csv)
 ├── sessions.csv         # Active student devices & timestamps
 └── professor_auth.csv   # SHA-256 hashed professor authentication credentials
