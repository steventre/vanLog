from datetime import datetime, timedelta
import sqlite3
import pandas as pd
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Vehicle Use Log", page_icon="🚐", layout="centered"
)

# Custom CSS to tightly pack button columns together
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }
    header {
        visibility: hidden !important;
        height: 0px !important;
    }
    [data-testid="stExpander"] {
        background-color: #f9f9f9 !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    [data-testid="stExpander"] summary {
        background-color: #f9f9f9 !important;
        border-radius: 0.5rem !important;
    }
    
    /* Tightly pack button columns together without wide spacing */
    [data-testid="stHorizontalBlock"] {
        gap: 8px !important;
    }
    
    @media print {
        .print-hide, [data-testid="stButton"], header, footer {
            display: none !important;
        }
        body, .print-receipt {
            display: block !important;
            visibility: visible !important;
            color: #000 !important;
            background: #fff !important;
            font-size: 13px !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        h1 {
            font-size: 16px !important;
            margin-top: 0 !important;
            margin-bottom: 2px !important;
            padding-top: 0 !important;
        }
        h3, h4 {
            font-size: 13px !important;
            margin-top: 4px !important;
            margin-bottom: 4px !important;
        }
        hr {
            margin: 4px 0 !important;
        }
        .print-students-box {
            font-size: 13px !important;
            font-weight: bold !important;
            color: #000 !important;
            border: 1px solid #000 !important;
            padding: 5px !important;
            margin-top: 4px !important;
            margin-bottom: 4px !important;
        }
        .print-grid {
            display: block !important;
            margin-top: 4px !important;
            margin-bottom: 4px !important;
            border-top: 1px solid #ccc !important;
            border-bottom: 1px solid #ccc !important;
            padding: 4px 0 !important;
        }
    }
    .scrollable-log-container {
        max-height: 350px;
        overflow-y: auto;
        padding-right: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- DATABASE SETUP (Persistence across refreshes) ---
def init_db():
    conn = sqlite3.connect("vehicle_logs.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            driver TEXT,
            vehicle TEXT,
            destination TEXT,
            start_mileage INTEGER,
            end_mileage INTEGER,
            total_miles INTEGER,
            start_time TEXT,
            end_time TEXT,
            students TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def load_logs_from_db():
    conn = sqlite3.connect("vehicle_logs.db", check_same_thread=False)
    df = pd.read_sql_query("SELECT * FROM logs ORDER BY id DESC", conn)
    conn.close()
    
    logs = []
    for _, row in df.iterrows():
        logs.append({
            "id": row["id"],
            "Date": row["date"],
            "Driver": row["driver"],
            "Vehicle": row["vehicle"],
            "Destination / Purpose": row["destination"],
            "Start Mileage": row["start_mileage"],
            "End Mileage": row["end_mileage"],
            "Total Miles": row["total_miles"],
            "Start Time": row["start_time"],
            "End Time": row["end_time"],
            "Students": row["students"]
        })
    return logs

def save_log_to_db(trip):
    conn = sqlite3.connect("vehicle_logs.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO logs (date, driver, vehicle, destination, start_mileage, end_mileage, total_miles, start_time, end_time, students)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        trip["Date"], trip["Driver"], trip["Vehicle"], trip["Destination / Purpose"],
        trip["Start Mileage"], trip["End Mileage"], trip["Total Miles"],
        trip["Start Time"], trip["End Time"], trip["Students"]
    ))
    conn.commit()
    conn.close()

def update_log_in_db(trip_id, trip):
    conn = sqlite3.connect("vehicle_logs.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE logs SET date=?, driver=?, vehicle=?, destination=?, start_mileage=?, end_mileage=?, total_miles=?, start_time=?, end_time=?, students=?
        WHERE id=?
    """, (
        trip["Date"], trip["Driver"], trip["Vehicle"], trip["Destination / Purpose"],
        trip["Start Mileage"], trip["End Mileage"], trip["Total Miles"],
        trip["Start Time"], trip["End Time"], trip["Students"], trip_id
    ))
    conn.commit()
    conn.close()

def delete_log_from_db(trip_id):
    conn = sqlite3.connect("vehicle_logs.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM logs WHERE id = ?", (trip_id,))
    conn.commit()
    conn.close()

# Initialize session state from database
if "log_history" not in st.session_state:
    st.session_state.log_history = load_logs_from_db()
if "form_counter" not in st.session_state:
    st.session_state.form_counter = 0
if "print_target_idx" not in st.session_state:
    st.session_state.print_target_idx = None

# Helper function to get current UTC-5 time in 12-hour string format + AM/PM
def get_current_utc5_time():
    utc_minus_5 = datetime.utcnow() - timedelta(hours=5)
    hour_24 = utc_minus_5.hour
    minute = utc_minus_5.minute
    
    is_pm = hour_24 >= 12
    hour_12 = hour_24 % 12
    if hour_12 == 0:
        hour_12 = 12
        
    time_str = f"{hour_12}:{minute:02d}"
    ampm = "PM" if is_pm else "AM"
    return time_str, ampm

cur_t_str, cur_ap = get_current_utc5_time()

# Initialize default session state values for main form times if not present
if "main_start_time_val" not in st.session_state:
    st.session_state.main_start_time_val = cur_t_str
if "main_start_ap_val" not in st.session_state:
    st.session_state.main_start_ap_val = cur_ap
if "main_end_time_val" not in st.session_state:
    st.session_state.main_end_time_val = ""
if "main_end_ap_val" not in st.session_state:
    st.session_state.main_end_ap_val = "--"

# Helper function to parse existing time string back into time value and AM/PM for editing
def parse_time_string(time_str):
    if not time_str:
        return "", "--"
    try:
        parts = time_str.split()
        t_val = parts[0]
        ap = parts[1] if len(parts) > 1 else "AM"
        return t_val, ap
    except (ValueError, IndexError):
        return "", "--"

# Grouped student roster definition
grouped_students = [
    "--- GROUP A ---",
    "Carmelo Behrendt",
    "Dorian Patterson",
    "Javion Townsend",
    "Jevon Smiley",
    "Nathaniel Nelson",
    "--- GROUP B ---",
    "Caleb Allen",
    "Charles Mcintyre",
    "Joel Afamefuna",
    "Nicholas Gardner",
    "Tyler Evans",
    "Zachary McDaniels"
]
clean_students_list = [s for s in grouped_students if not s.startswith("---")]

# --- INDIVIDUAL PRINT VIEW SCREEN ---
if st.session_state.print_target_idx is not None and st.session_state.print_target_idx < len(st.session
