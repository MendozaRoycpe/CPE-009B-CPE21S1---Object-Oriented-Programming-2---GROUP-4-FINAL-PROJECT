#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# FUNCTIONS / METHODS LIST:
# - get_device_id()
# - load_sessions()
# - save_sessions(rows)
# - start_session(student_id)
# - end_session(student_id)
# - log_conflict(student_id, issue_type)
#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

import socket
from datetime import datetime
from PROFESSOR_FUNCTS import (
    ensure_files, read_csv, write_csv, load_students,
    SESSIONS_FILE, CONFLICTS_FILE, SESSION_FIELDS, CONFLICT_FIELDS,
)

ensure_files()

# gumagamit ng hostname bilang device_id para sa session control
def get_device_id():
    return socket.gethostname()

# kukunin lahat ng currently-active na sessions
def load_sessions():
    return read_csv(SESSIONS_FILE)

def save_sessions(rows):
    write_csv(SESSIONS_FILE, rows, SESSION_FIELDS)

# susubukan i-start ang session; conflict kung naka-login na sa ibang device
def start_session(student_id):
    sessions = load_sessions()
    device_id = get_device_id()

    for session in sessions:
        if session["student_id"] == student_id:
            if session["device_id"] == device_id:
                return "ok"
            log_conflict(student_id, "Device Conflict / Multiple Logins")
            return "conflict"

    sessions.append({"student_id": student_id, "device_id": device_id,
                      "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    save_sessions(sessions)
    return "ok"

# tatanggalin yung session row ng student_id na ito
def end_session(student_id):
    sessions = [s for s in load_sessions() if s["student_id"] != student_id]
    save_sessions(sessions)

# ililista sa session_conflicts.csv ang mga issue o anti-cheat violation
def log_conflict(student_id, issue_type="Device Conflict"):
    conflicts = read_csv(CONFLICTS_FILE)
    conflicts.append({
        "student_id": student_id, 
        "device_id": get_device_id(),
        "attempted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "issue_type": issue_type
    })
    write_csv(CONFLICTS_FILE, conflicts, CONFLICT_FIELDS)