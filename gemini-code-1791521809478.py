from datetime import datetime, timedelta
import sqlite3
import pandas as pd
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="High School Vehicle Usage Log", page_icon="🚐", layout="centered"
)

# Custom CSS for print hiding, student text styling, and compact scrollable log history container
st.markdown("""
    <style>
    @media print {
        .print-hide, [data-testid="stButton"] {
            display: none !important;
        }
        .print-students {
            font-size: 16px !important;
            font-weight: bold !important;
            color: #000 !important;
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

# Student list definition
students_list = [
    "Carmelo Behrendt",
    "Nick Gardner",
    "Nate Nelson",
    "Javion Townsend",
    "Jevon Smiley",
    "Droian Patterson",
    "Charles Mcentyre",
    "Tyler Evans",
    "Joel Afumafane",
    "Caleb Allen",
    "Zach McDaniels",
]
sorted_students = sorted(students_list)

# --- INDIVIDUAL PRINT VIEW SCREEN ---
if st.session_state.print_target_idx is not None and st.session_state.print_target_idx < len(st.session_state.log_history):
    idx = st.session_state.print_target_idx
    trip = st.session_state.log_history[idx]
    
    st.title("🚐 Vehicle Usage Log - Trip Receipt")
    st.markdown(f"**Trip #{trip['id']} Report** (Generated: {datetime.today().strftime('%Y-%m-%d')})")
    st.markdown("---")

    st.markdown(f"### 📅 Date: {trip['Date']}")
    st.markdown(f"**Driver:** {trip['Driver']}")
    st.markdown(f"**Vehicle:** {trip['Vehicle']}")
    st.markdown(f"**Destination / Purpose:** {trip['Destination / Purpose']}")
    
    st.markdown("---")
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        st.metric("Starting Mileage", trip['Start Mileage'])
    with col_p2:
        st.metric("Ending Mileage", trip['End Mileage'])
    with col_p3:
        st.metric("Total Miles", trip['Total Miles'])

    col_p4, col_p5 = st.columns(2)
    with col_p4:
        st.markdown(f"**Start Time:** {trip['Start Time']}")
    with col_p5:
        st.markdown(f"**End Time:** {trip['End Time'] if trip['End Time'] else 'N/A'}")

    st.markdown("---")
    st.markdown("#### 👥 Student Passengers")
    st.markdown(f'<p class="print-students"><strong>{trip["Students"]}</strong></p>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("⬅️ Back to Home / Entry Form"):
        st.session_state.print_target_idx = None
        st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="print-hide">💡 <em>Tip: Use <code>Cmd+P</code> or <code>Ctrl+P</code> to print this individual trip page cleanly.</em></p>', unsafe_allow_html=True)

else:
    # --- NORMAL APP & FORM MODE ---
    st.title("🚐 High School Vehicle Usage Log")
    st.markdown("Record vehicle trips, destinations, passengers, and mileage for school transport.")

    with st.form(f"vehicle_log_form_{st.session_state.form_counter}"):
        st.subheader("Trip Details")

        col1, col2 = st.columns(2)
        with col1:
            driver_name = st.text_input("Driver Name", value="Steven Hartl")
        with col2:
            trip_date = st.date_input("Date", value=datetime.today())

        vehicle = st.selectbox(
            "Select Vehicle",
            ["Silver Van", "White Van", "Honda Pilot"]
        )

        destination = st.text_input("Destination / Purpose", value="Nehemiah 2.0")

        st.markdown("---")
        st.subheader("Mileage & Time Tracking")

        col3, col4 = st.columns(2)
        with col3:
            st.markdown("**Start Time (UTC-5)**")
            sc1, sc2 = st.columns([2, 1])
            with sc1:
                start_t_val = st.text_input("Start Time (HH:MM)", value=st.session_state.main_start_time_val, key=f"main_start_t_{st.session_state.form_counter}")
            with sc2:
                start_ap_val = st.selectbox("Start AM/PM", ["AM", "PM"], index=0 if st.session_state.main_start_ap_val == "AM" else 1, key=f"main_start_ap_{st.session_state.form_counter}")

            start_mileage = st.number_input(
                "Starting Mileage (Required)", min_value=0, value=None, step=1, format="%d", key=f"main_sm_{st.session_state.form_counter}"
            )

        with col4:
            st.markdown("**End Time (UTC-5)**")
            ec1, ec2 = st.columns([2, 1])
            with ec1:
                end_t_val = st.text_input("End Time (HH:MM)", value=st.session_state.main
