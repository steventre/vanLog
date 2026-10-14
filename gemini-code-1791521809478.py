from datetime import datetime, timedelta
import sqlite3
import pandas as pd
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="High School Vehicle Usage Log", page_icon="🚐", layout="centered"
)

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
    # Order by id DESC so newest entries appear at the top
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
    st.session_state.main_end_time_val =
