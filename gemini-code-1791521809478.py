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
    df = pd.read_sql_query("SELECT * FROM logs", conn)
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

# Helper function to render time input safely inside forms
def render_time_input(label, default_time, default_ampm, key_prefix, allow_blank=False):
    st.markdown(f"**{label} (UTC-5)**")
    c1, c2 = st.columns([2, 1])
    
    with c1:
        t_val = st.text_input("Time (HH:MM)", value=default_time, placeholder="HH:MM", key=f"{key_prefix}_time")
    with c2:
        ap_options = ["--", "AM", "PM"] if allow_blank else ["AM", "PM"]
        if not default_ampm or default_ampm not in ap_options:
            default_ap_idx = 0 if allow_blank else 0
        else:
            default_ap_idx = ap_options.index(default_ampm)
        ap = st.selectbox("AM/PM", ap_options, index=default_ap_idx, key=f"{key_prefix}_ap")
        
    if not t_val.strip() or ap == "--":
        return ""
    return f"{t_val.strip()} {ap}"

# Helper function to parse existing time string back into time value and AM/PM for editing
def parse_time_string(time_str):
    if not time_str:
        return "", ""
    try:
        parts = time_str.split()
        t_val = parts[0]
        ap = parts[1] if len(parts) > 1 else "AM"
        return t_val, ap
    except (ValueError, IndexError):
        return "", ""

# --- INDIVIDUAL PRINT VIEW SCREEN (No Back button per request) ---
if st.session_state.print_target_idx is not None and st.session_state.print_target_idx < len(st.session_state.log_history):
    idx = st.session_state.print_target_idx
    trip = st.session_state.log_history[idx]
    
    st.title("🚐 Vehicle Usage Log - Trip Receipt")
    st.markdown(f"**Trip #{idx + 1} Report** (Generated: {datetime.today().strftime('%Y-%m-%d')})")
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
    st.info(trip['Students'])
    
    st.info("Tip: Use `Cmd+P` or `Ctrl+P` to print this individual trip page cleanly.")

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
            start_mileage = st.number_input(
                "Starting Mileage (Required)", min_value=0, value=None, step=1, format="%d"
            )
            start_time_str = render_time_input("Start Time", cur_t_str, cur_ap, "main_start", allow_blank=False)

        with col4:
            end_mileage = st.number_input(
                "Ending Mileage (Optional)", min_value=0, value=None, step=1, format="%d"
            )
            end_time_str = render_time_input("End Time", "", "--", "main_end", allow_blank=True)

        submitted = st.form_submit_button("Save Trip Entry")

        if submitted:
            if not driver_name.strip():
                st.error("Driver Name is required.")
            elif start_mileage is None:
                st.error("Starting Mileage is required.")
            elif not start_time_str:
                st.error("Start Time is required.")
            else:
                s_mileage = start_mileage
                e_mileage = end_mileage if end_mileage is not None else s_mileage
                total_miles = e_mileage - s_mileage if e_mileage >= s_mileage else 0

                trip_entry = {
                    "Date": trip_date.strftime("%Y-%m-%d"),
                    "Driver": driver_name,
                    "Vehicle": vehicle,
                    "Destination / Purpose": destination,
                    "Start Mileage": s_mileage,
                    "End Mileage": end_mileage if end_mileage is not None else 0,
                    "Total Miles": total_miles,
                    "Start Time": start_time_str,
                    "End Time": end_time_str,
                    "Students": "None logged",
                }

                save_log_to_db(trip_entry)
                st.session_state.log_history = load_logs_from_db()
                st.session_state.form_counter += 1
                st.success("Trip successfully logged and saved to database!")
                st.rerun()

    # --- PRINTABLE & EDITABLE LOG SECTION ---
    if len(st.session_state.log_history) > 0:
        st.markdown("---")
        st.subheader("📋 Log History & Individual Trip Printouts")
        st.info("Expand any trip below to edit details or click its dedicated print button to view and print that specific log on its own page.")

        for idx, trip in enumerate(st.session_state.log_history):
            with st.expander(f"Trip #{idx + 1}: {trip['Date']} - {trip['Vehicle']} (Driver: {trip['Driver']})"):
                
                if st.button(f"🖨️ Print / View Trip #{idx + 1} Sheet", key=f"print_btn_{idx}"):
                    st.session_state.print_target_idx = idx
                    st.rerun()

                st.markdown("---")
                with st.form(f"edit_form_{idx}"):
                    try:
                        default_d = datetime.strptime(trip["Date"], "%Y-%m-%d").date()
                    except ValueError:
                        default_d = datetime.today().date()
                    
                    e_date = st.date_input("Date", value=default_d, key=f"ed_date_{idx}")
                    e_dest = st.text_input("Destination / Purpose", value=trip["Destination / Purpose"], key=f"ed_dest_{idx}")
                    
                    existing_sm = int(trip["Start Mileage"]) if trip["Start Mileage"] != 0 else None
                    existing_em = int(trip["End Mileage"]) if trip["End Mileage"] != 0 else None
                    
                    e_start_m = st.number_input("Start Mileage", min_value=0, value=existing_sm, step=1, format="%d", key=f"ed_sm_{idx}")
                    e_end_m = st.number_input("End Mileage", min_value=0, value=existing_em, step=1, format="%d", key=f"ed_em_{idx}")
                    
                    est_t, est_ap = parse_time_string(trip["Start Time"])
                    if not est_t:
                        est_t, est_ap = cur_t_str, cur_ap
                    e_start_time_str = render_time_input("Start Time", est_t, est_ap, f"ed_start_{idx}", allow_blank=False)

                    eet_t, eet_ap = parse_time_string(trip["End Time"])
                    e_end_time_str = render_time_input("End Time", eet_t, eet_ap, f"ed_end_{idx}", allow_blank=True)
                    
                    e_saved = st.form_submit_button("Update Trip Entry")
                    if e_saved:
                        calc_sm = e_start_m if e_start_m is not None else 0
                        calc_em = e_end_m if e_end_m is not None else 0
                        calc_total = calc_em - calc_sm if calc_em >= calc_sm else 0

                        updated_trip = {
                            "Date": e_date.strftime("%Y-%m-%d"),
                            "Driver": trip["Driver"],
                            "Vehicle": trip["Vehicle"],
                            "Destination / Purpose": e_dest,
                            "Start Mileage": calc_sm,
                            "End Mileage": calc_em,
                            "Total Miles": calc_total,
                            "Start Time": e_start_time_str,
                            "End Time": e_end_time_str,
                            "Students": trip["Students"]
                        }

                        update_log_in_db(trip["id"], updated_trip)
                        st.session_state.log_history = load_logs_from_db()
                        st.success("Trip updated successfully!")
                        st.rerun()

        df_logs = pd.DataFrame(st.session_state.log_history)
        csv = df_logs.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Entire Log History as CSV",
            data=csv,
            file_name=f"vehicle_usage_log_{datetime.today().strftime('%Y-%m-%d')}.csv",
            mime="text/csv",
        )
