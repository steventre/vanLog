from datetime import datetime, timedelta
import re
import sqlite3
import pandas as pd
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Vehicle Use Log", page_icon="🚐", layout="centered"
)

# Custom CSS with balanced heading sizes (1.5rem), tight button alignment, and clean spacing
st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    /* Balanced heading size for H1 and H3 headings so they match and look prominent */
    h1, h3 {
        font-size: 1.5rem !important;
        font-weight: 600 !important;
    }

    /* Standardize expander headers to have a consistent light gray background */
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

    /* Align the 'Now' submit button columns flush with the text input */
    [data-testid="stHorizontalBlock"] {
        align-items: flex-end !important;
        gap: 8px !important;
    }

    /* Clean horizontal row container for inline text action links */
    .action-links-row {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 16px !important;
        align-items: center !important;
        margin-top: 10px !important;
        margin-bottom: 10px !important;
        padding-left: 4px !important;
        font-size: 0.95rem !important;
    }
    .action-links-row a {
        text-decoration: none !important;
        font-weight: 500 !important;
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
        max-height: 400px;
        overflow-y: auto;
        padding-right: 5px;
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

# Handle URL query params for lightweight link actions (Print / Delete)
query_params = st.query_params
if "action" in query_params and "trip_id" in query_params:
    action = query_params["action"]
    try:
        t_id = int(query_params["trip_id"])
        if action == "print":
            for i, trip in enumerate(st.session_state.log_history):
                if trip["id"] == t_id:
                    st.session_state.print_target_idx = i
                    st.query_params.clear()
                    st.rerun()
        elif action == "delete":
            delete_log_from_db(t_id)
            st.session_state.log_history = load_logs_from_db()
            st.query_params.clear()
            st.rerun()
    except ValueError:
        pass

# Helper function to validate HH:MM time format
def validate_time_format(time_str):
    if not time_str:
        return True
    pattern = r"^([01]?[0-9]|2[0-3]):([0-5][0-9])$"
    return bool(re.match(pattern, time_str.strip()))

# Helper function to get current UTC-5 time in 24-hour format (HH:MM)
def get_current_utc5_time_24h():
    utc_minus_5 = datetime.utcnow() - timedelta(hours=5)
    return utc_minus_5.strftime("%H:%M")

cur_t_str = get_current_utc5_time_24h()

# Initialize default session state values for main form times if not present
if "main_start_time_val" not in st.session_state:
    st.session_state.main_start_time_val = cur_t_str
if "main_end_time_val" not in st.session_state:
    st.session_state.main_end_time_val = ""

# Helper function to convert 12-hour/legacy time string to 24-hour HH:MM
def convert_to_24h(time_str):
    if not time_str:
        return ""
    try:
        if ":" in time_str and "AM" not in time_str and "PM" not in time_str:
            return time_str.strip()
        dt = datetime.strptime(time_str.strip(), "%I:%M %p")
        return dt.strftime("%H:%M")
    except ValueError:
        return ""

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
vehicle_options = ["Silver Van", "White Van", "Honda Pilot"]

# --- INDIVIDUAL PRINT VIEW SCREEN ---
if st.session_state.print_target_idx is not None and st.session_state.print_target_idx < len(st.session_state.log_history):
    idx = st.session_state.print_target_idx
    trip = st.session_state.log_history[idx]
    
    st.markdown('<div class="print-receipt">', unsafe_allow_html=True)
    
    st.markdown("<h1>🚐 Vehicle Use Log - Trip Receipt</h1>", unsafe_allow_html=True)
    st.markdown(f"**Trip #{trip['id']} Report** (Generated: {datetime.today().strftime('%Y-%m-%d')})")
    st.markdown("---")

    st.markdown(f"### 📅 Date: {trip['Date']}")
    st.markdown(f"**Driver:** {trip['Driver']}")
    st.markdown(f"**Vehicle:** {trip['Vehicle']}")
    st.markdown(f"**Destination / Purpose:** {trip['Destination / Purpose']}")
    
    st.markdown("---")
    st.markdown("#### 👥 Student Passengers")
    st.markdown(f'<div class="print-students-box"><strong>{trip["Students"]}</strong></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    print_html_grid = f"""
    <div class="print-grid">
        <div><strong>Start Mileage:</strong> {trip['Start Mileage']} &nbsp;&nbsp;|&nbsp;&nbsp; <strong>End Mileage:</strong> {trip['End Mileage']} &nbsp;&nbsp;|&nbsp;&nbsp; <strong>Total Miles:</strong> {trip['Total Miles']}</div>
    </div>
    <div style="margin-top: 4px; margin-bottom: 5px;">
        <strong>Start Time:</strong> {trip['Start Time']} &nbsp;&nbsp;|&nbsp;&nbsp; 
        <strong>End Time:</strong> {trip['End Time'] if trip['End Time'] else 'N/A'}
    </div>
    """
    st.markdown(print_html_grid, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Download Trip text file link (works natively on iOS standalone web apps for instant viewing/printing)
    trip_txt = (
        f"VEHICLE USE LOG - TRIP #{trip['id']}\n"
        f"----------------------------------------\n"
        f"Date: {trip['Date']}\n"
        f"Driver: {trip['Driver']}\n"
        f"Vehicle: {trip['Vehicle']}\n"
        f"Destination: {trip['Destination / Purpose']}\n"
        f"Start Mileage: {trip['Start Mileage']}\n"
        f"End Mileage: {trip['End Mileage']}\n"
        f"Total Miles: {trip['Total Miles']}\n"
        f"Start Time: {trip['Start Time']}\n"
        f"End Time: {trip['End Time']}\n"
        f"Passengers: {trip['Students']}\n"
    )
    
    st.download_button(
        label="📥 Download / Print Trip Summary (TXT)",
        data=trip_txt,
        file_name=f"trip_{trip['id']}_report.txt",
        mime="text/plain",
        use_container_width=True
    )

    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("⬅️ Back to Home / Entry Form", use_container_width=True):
        st.session_state.print_target_idx = None
        st.rerun()

else:
    # --- NORMAL APP & FORM MODE ---
    st.markdown('<h1 style="padding-left: 0.2rem; margin-bottom: 1rem;">🚐 Vehicle Use Log</h1>', unsafe_allow_html=True)

    # Check main form 'now' trigger before widget instantiation
    main_now_trigger = "trigger_main_now"
    if st.session_state.get(main_now_trigger, False):
        st.session_state.main_end_time_val = get_current_utc5_time_24h()
        st.session_state[main_now_trigger] = False

    with st.form(f"vehicle_log_form_{st.session_state.form_counter}"):
        
        with st.expander("Trip Details", expanded=False):
            driver_name = st.text_input("Driver Name", value="Steven Hartl", key=f"main_dn_{st.session_state.form_counter}")
            trip_date = st.date_input("Date", value=datetime.today(), key=f"main_date_{st.session_state.form_counter}")
            vehicle = st.selectbox("Select Vehicle", vehicle_options, key=f"main_veh_{st.session_state.form_counter}")
            destination = st.text_input("Destination / Purpose", value="Nehemiah 2.0", key=f"main_dest_{st.session_state.form_counter}")

        with st.expander("Student Passengers", expanded=False):
            selected_students = st.multiselect("Select Students on Trip (Grouped Roster)", grouped_students, key=f"main_students_{st.session_state.form_counter}")

        with st.expander("Trip Start", expanded=False):
            start_time = st.text_input("Start Time (HH:MM)", value=st.session_state.main_start_time_val, placeholder="HH:MM", key=f"main_st_{st.session_state.form_counter}")
            start_mileage = st.number_input("Starting Mileage (Required)", min_value=0, value=None, step=1, format="%d", key=f"main_sm_{st.session_state.form_counter}")

        with st.expander("Trip End", expanded=False):
            tc1, tc2 = st.columns([2, 1])
            with tc1:
                end_time = st.text_input("End Time (HH:MM)", value=st.session_state.main_end_time_val, placeholder="HH:MM", key=f"main_end_t_{st.session_state.form_counter}")
            with tc2:
                if st.form_submit_button("⏱️ Now"):
                    st.session_state[main_now_trigger] = True
                    st.rerun()

            end_mileage = st.number_input("Ending Mileage (Optional)", min_value=0, value=None, step=1, format="%d", key=f"main_em_{st.session_state.form_counter}")

        submitted = st.form_submit_button("Save Trip Entry")

    if submitted:
        valid_selected_students = [s for s in selected_students if not s.startswith("---")]
        
        if not driver_name.strip():
            st.error("Driver Name is required.")
        elif start_mileage is None:
            st.error("Starting Mileage is required.")
        elif not valid_selected_students:
            st.error("Please select at least one student passenger.")
        elif not start_time.strip() or not validate_time_format(start_time):
            st.error("Start Time is required and must be in valid HH:MM format (24-hour).")
        elif end_time.strip() and not validate_time_format(end_time):
            st.error("End Time must be in valid HH:MM format (24-hour).")
        else:
            s_mileage = int(start_mileage)
            e_mileage = int(end_mileage) if end_mileage is not None else 0
            total_miles = e_mileage - s_mileage if e_mileage >= s_mileage else 0

            trip_entry = {
                "Date": trip_date.strftime("%Y-%m-%d"),
                "Driver": driver_name,
                "Vehicle": vehicle,
                "Destination / Purpose": destination,
                "Start Mileage": s_mileage,
                "End Mileage": e_mileage,
                "Total Miles": total_miles,
                "Start Time": start_time.strip(),
                "End Time": end_time.strip(),
                "Students": ", ".join(valid_selected_students),
            }

            save_log_to_db(trip_entry)
            st.session_state.log_history = load_logs_from_db()
            st.session_state.form_counter += 1
            st.session_state.main_end_time_val = ""
            st.success("Trip successfully logged and saved to database!")
            st.rerun()

    # --- PRINTABLE & EDITABLE LOG SECTION ---
    st.markdown("---")
    st.markdown("<h3>📋 Log History</h3>", unsafe_allow_html=True)

    if len(st.session_state.log_history) == 0:
        st.info("No trip logs found yet. Save a trip above to see it appear here!")
    else:
        st.markdown('<div class="scrollable-log-container">', unsafe_allow_html=True)

        for idx, trip in enumerate(st.session_state.log_history):
            with st.expander(f"Trip ID #{trip['id']}: {trip['Date']} - {trip['Vehicle']} (Driver: {trip['Driver']})"):
                
                now_trigger_key = f"trigger_now_{trip['id']}"
                if st.session_state.get(now_trigger_key, False):
                    st.session_state[f"ed_et_{trip['id']}"] = get_current_utc5_time_24h()
                    st.session_state[now_trigger_key] = False

                with st.form(f"edit_form_{trip['id']}"):
                    try:
                        default_d = datetime.strptime(trip["Date"], "%Y-%m-%d").date()
                    except ValueError:
                        default_d = datetime.today().date()
                    
                    with st.expander("Trip Details", expanded=False):
                        e_date = st.date_input("Date", value=default_d, key=f"ed_date_{trip['id']}")
                        e_driver = st.text_input("Driver Name", value=trip["Driver"], key=f"ed_driver_{trip['id']}")
                        
                        v_idx = vehicle_options.index(trip["Vehicle"]) if trip["Vehicle"] in vehicle_options else 0
                        e_vehicle = st.selectbox("Select Vehicle", vehicle_options, index=v_idx, key=f"ed_veh_{trip['id']}")
                        
                        e_dest = st.text_input("Destination / Purpose", value=trip["Destination / Purpose"], key=f"ed_dest_{trip['id']}")

                    with st.expander("Student Passengers", expanded=False):
                        current_trip_students = [s.strip() for s in trip["Students"].split(",") if s.strip() in clean_students_list]
                        e_students = st.multiselect("Student Passengers", grouped_students, default=current_trip_students, key=f"ed_students_{trip['id']}")

                    with st.expander("Trip Start", expanded=False):
                        existing_sm = int(trip["Start Mileage"]) if trip["Start Mileage"] is not None and trip["Start Mileage"] != 0 else None
                        e_start_m = st.number_input("Start Mileage", min_value=0, value=existing_sm, step=1, format="%d", key=f"ed_sm_{trip['id']}")
                        est_t = convert_to_24h(trip["Start Time"])
                        ed_st_val = st.text_input("Start Time (HH:MM)", value=est_t, key=f"ed_st_{trip['id']}")

                    with st.expander("Trip End", expanded=True):
                        existing_em = int(trip["End Mileage"]) if trip["End Mileage"] is not None and trip["End Mileage"] != 0 else None
                        eet_t = convert_to_24h(trip["End Time"])
                        
                        edit_key = f"ed_et_{trip['id']}"
                        if edit_key not in st.session_state:
                            st.session_state[edit_key] = eet_t
                        
                        etc1, etc2 = st.columns([2, 1])
                        with etc1:
                            ed_et_val = st.text_input("End Time (HH:MM)", key=edit_key)
                        with etc2:
                            if st.form_submit_button("⏱️ Now", key=f"ed_now_btn_{trip['id']}"):
                                st.session_state[now_trigger_key] = True
                                st.rerun()

                        e_end_m = st.number_input("Ending Mileage", min_value=0, value=existing_em, step=1, format="%d", key=f"ed_em_{trip['id']}")

                    e_saved = st.form_submit_button("Update Trip Entry")
                    if e_saved:
                        if not validate_time_format(ed_st_val):
                            st.error("Start Time must be in valid HH:MM format (24-hour).")
                        elif ed_et_val.strip() and not validate_time_format(ed_et_val):
                            st.error("End Time must be in valid HH:MM format (24-hour).")
                        else:
                            valid_e_students = [s for s in e_students if not s.startswith("---")]
                            calc_sm = e_start_m if e_start_m is not None else 0
                            calc_em = e_end_m if e_end_m is not None else 0
                            calc_total = calc_em - calc_sm if calc_em >= calc_sm else 0

                            updated_trip = {
                                "Date": e_date.strftime("%Y-%m-%d"),
                                "Driver": e_driver.strip(),
                                "Vehicle": e_vehicle,
                                "Destination / Purpose": e_dest,
                                "Start Mileage": calc_sm,
                                "End Mileage": calc_em,
                                "Total Miles": calc_total,
                                "Start Time": ed_st_val.strip(),
                                "End Time": ed_et_val.strip(),
                                "Students": ", ".join(valid_e_students) if valid_e_students else "None logged"
                            }

                            update_log_in_db(trip["id"], updated_trip)
                            st.session_state.log_history = load_logs_from_db()
                            st.success("Trip updated successfully!")
                            st.rerun()

                # Action links placed directly inside each trip expander container for reliable visibility
                action_links_html = f"""
                <div class="action-links-row">
                    <a href="?action=print&trip_id={trip['id']}" target="_self">🖨️ Print</a>
                    <span>|</span>
                    <a href="?action=delete&trip_id={trip['id']}" target="_self" style="color: #d9534f;">🗑️ Delete</a>
                </div>
                """
                st.markdown(action_links_html, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        df_logs = pd.DataFrame(st.session_state.log_history)
        csv = df_logs.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Entire Log History as CSV",
            data=csv,
            file_name=f"vehicle_usage_log_{datetime.today().strftime('%Y-%m-%d')}.csv",
            mime="text/csv",
        )
