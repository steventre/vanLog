from datetime import datetime, timedelta
import sqlite3
import pandas as pd
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Vehicle Use Log", page_icon="🚐", layout="centered"
)

# Custom CSS for compact icon buttons and standardized expanders
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
    
    /* Tightly pack icon buttons together */
    [data-testid="stHorizontalBlock"] {
        gap: 4px !important;
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
    
    if st.button("⬅️ Back to Home / Entry Form"):
        st.session_state.print_target_idx = None
        st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="print-hide">💡 <em>Tip: Use `Cmd+P` or `Ctrl+P` to print this individual trip page cleanly.</em></p>', unsafe_allow_html=True)

else:
    # --- NORMAL APP & FORM MODE ---
    st.title("🚐 Vehicle Use Log")

    with st.form(f"vehicle_log_form_{st.session_state.form_counter}"):
        
        # Collapsible Trip Details (Closed by default)
        with st.expander("Trip Details", expanded=False):
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

        # Collapsible Mileage & Time Tracking (Expanded by default)
        with st.expander("Mileage & Time Tracking", expanded=True):
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
                    end_t_val = st.text_input("End Time (HH:MM)", value=st.session_state.main_end_time_val, placeholder="HH:MM", key=f"main_end_t_{st.session_state.form_counter}")
                with ec2:
                    end_ap_options = ["--", "AM", "PM"]
                    end_ap_idx = end_ap_options.index(st.session_state.main_end_ap_val) if st.session_state.main_end_ap_val in end_ap_options else 0
                    end_ap_val = st.selectbox("End AM/PM", end_ap_options, index=end_ap_idx, key=f"main_end_ap_{st.session_state.form_counter}")

                end_mileage = st.number_input(
                    "Ending Mileage (Optional)", min_value=0, value=None, step=1, format="%d", key=f"main_em_{st.session_state.form_counter}"
                )

        # Collapsible Student Passengers (Expanded by default)
        with st.expander("Student Passengers", expanded=True):
            selected_students = st.multiselect(
                "Select Students on Trip (Grouped Roster)", grouped_students, key=f"main_students_{st.session_state.form_counter}"
            )

        submitted = st.form_submit_button("Save Trip Entry")

    # --- INSTANT "SET NOW" BUTTON (OUTSIDE FORM) ---
    if st.button("⏱️ Set End Time to Current Time Now"):
        cur_t, cur_a = get_current_utc5_time()
        st.session_state.main_end_time_val = cur_t
        st.session_state.main_end_ap_val = cur_a
        st.session_state.form_counter += 1
        st.rerun()

    if submitted:
        try:
            driver_name_val = driver_name
        except NameError:
            driver_name_val = "Steven Hartl"
        try:
            trip_date_val = trip_date
        except NameError:
            trip_date_val = datetime.today()
        try:
            vehicle_val = vehicle
        except NameError:
            vehicle_val = "Silver Van"
        try:
            destination_val = destination
        except NameError:
            destination_val = "Nehemiah 2.0"

        valid_selected_students = [s for s in selected_students if not s.startswith("---")]
        start_time_str = f"{start_t_val.strip()} {start_ap_val}" if start_t_val.strip() else ""
        end_time_str = f"{end_t_val.strip()} {end_ap_val}" if end_t_val.strip() and end_ap_val != "--" else ""

        if not driver_name_val.strip():
            st.error("Driver Name is required.")
        elif start_mileage is None:
            st.error("Starting Mileage is required.")
        elif not valid_selected_students:
            st.error("Please select at least one student passenger.")
        elif not start_time_str:
            st.error("Start Time is required.")
        else:
            s_mileage = int(start_mileage)
            e_mileage = int(end_mileage) if end_mileage is not None else 0
            total_miles = e_mileage - s_mileage if e_mileage >= s_mileage else 0

            trip_entry = {
                "Date": trip_date_val.strftime("%Y-%m-%d"),
                "Driver": driver_name_val,
                "Vehicle": vehicle_val,
                "Destination / Purpose": destination_val,
                "Start Mileage": s_mileage,
                "End Mileage": e_mileage,
                "Total Miles": total_miles,
                "Start Time": start_time_str,
                "End Time": end_time_str,
                "Students": ", ".join(valid_selected_students),
            }

            save_log_to_db(trip_entry)
            st.session_state.log_history = load_logs_from_db()
            st.session_state.form_counter += 1
            st.session_state.main_end_time_val = ""
            st.session_state.main_end_ap_val = "--"
            st.success("Trip successfully logged and saved to database!")
            st.rerun()

    # --- PRINTABLE & EDITABLE LOG SECTION ---
    st.markdown("---")
    st.subheader("📋 Log History")

    if len(st.session_state.log_history) == 0:
        st.info("No trip logs found yet. Save a trip above to see it appear here!")
    else:
        st.markdown('<div class="scrollable-log-container">', unsafe_allow_html=True)

        for idx, trip in enumerate(st.session_state.log_history):
            with st.expander(f"Trip ID #{trip['id']}: {trip['Date']} - {trip['Vehicle']} (Driver: {trip['Driver']})"):
                
                # Compact icon-only buttons in tight side-by-side columns
                bc1, bc2, bc3, bc_spacer = st.columns([0.5, 0.5, 0.5, 8.5])
                with bc1:
                    if st.button("🖨️", key=f"print_btn_{trip['id']}", help=f"Print Trip #{trip['id']}"):
                        st.session_state.print_target_idx = idx
                        st.rerun()
                with bc2:
                    if st.button("⏱️", key=f"btn_now_{trip['id']}", help="Set End Time to Now"):
                        cur_t, cur_a = get_current_utc5_time()
                        st.session_state[f"ed_et_{trip['id']}"] = cur_t
                        st.session_state[f"ed_ea_{trip['id']}"] = cur_a
                        st.rerun()
                with bc3:
                    if st.button("🗑️", key=f"del_btn_{trip['id']}", help=f"Delete Trip #{trip['id']}"):
                        delete_log_from_db(trip['id'])
                        st.session_state.log_history = load_logs_from_db()
                        st.success(f"Trip #{trip['id']} deleted successfully!")
                        st.rerun()

                with st.form(f"edit_form_{trip['id']}"):
                    try:
                        default_d = datetime.strptime(trip["Date"], "%Y-%m-%d").date()
                    except ValueError:
                        default_d = datetime.today().date()
                    
                    e_date = st.date_input("Date", value=default_d, key=f"ed_date_{trip['id']}")
                    e_dest = st.text_input("Destination / Purpose", value=trip["Destination / Purpose"], key=f"ed_dest_{trip['id']}")
                    
                    existing_sm = int(trip["Start Mileage"]) if trip["Start Mileage"] is not None and trip["Start Mileage"] != 0 else None
                    existing_em = int(trip["End Mileage"]) if trip["End Mileage"] is not None and trip["End Mileage"] != 0 else None
                    
                    e_start_m = st.number_input("Start Mileage", min_value=0, value=existing_sm, step=1, format="%d", key=f"ed_sm_{trip['id']}")
                    e_end_m = st.number_input("Ending Mileage", min_value=0, value=existing_em, step=1, format="%d", key=f"ed_em_{trip['id']}")
                    
                    est_t, est_ap = parse_time_string(trip["Start Time"])
                    eet_t, eet_ap = parse_time_string(trip["End Time"])

                    st.markdown("**Start Time (UTC-5)**")
                    esc1, esc2 = st.columns([2, 1])
                    with esc1:
                        ed_st_val = st.text_input("Start Time", value=est_t, key=f"ed_st_{trip['id']}")
                    with esc2:
                        ed_sa_val = st.selectbox("Start AM/PM", ["AM", "PM"], index=0 if est_ap == "AM" else 1, key=f"ed_sa_{trip['id']}")

                    st.markdown("**End Time (UTC-5)**")
                    eec1, eec2 = st.columns([2, 1])
                    with eec1:
                        default_et_val = st.session_state.get(f"ed_et_{trip['id']}", eet_t)
                        ed_et_val = st.text_input("End Time", value=default_et_val, key=f"ed_et_{trip['id']}")
                    with eec2:
                        ed_ea_opts = ["--", "AM", "PM"]
                        current_ea = st.session_state.get(f"ed_ea_{trip['id']}", eet_ap)
                        ed_ea_idx = ed_ea_opts.index(current_ea) if current_ea in ed_ea_opts else 0
                        ed_ea_val = st.selectbox("End AM/PM", ed_ea_opts, index=ed_ea_idx, key=f"ed_ea_{trip['id']}")
                    
                    current_trip_students = [s.strip() for s in trip["Students"].split(",") if s.strip() in clean_students_list]
                    e_students = st.multiselect("Student Passengers", grouped_students, default=current_trip_students, key=f"ed_students_{trip['id']}")

                    e_saved = st.form_submit_button("Update Trip Entry")
                    if e_saved:
                        valid_e_students = [s for s in e_students if not s.startswith("---")]
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
                            "Start Time": f"{ed_st_val.strip()} {ed_sa_val}",
                            "End Time": f"{ed_et_val.strip()} {ed_ea_val}" if ed_et_val.strip() and ed_ea_val != "--" else "",
                            "Students": ", ".join(valid_e_students) if valid_e_students else "None logged"
                        }

                        update_log_in_db(trip["id"], updated_trip)
                        st.session_state.log_history = load_logs_from_db()
                        st.success("Trip updated successfully!")
                        st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        df_logs = pd.DataFrame(st.session_state.log_history)
        csv = df_logs.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Entire Log History as CSV",
            data=csv,
            file_name=f"vehicle_usage_log_{datetime.today().strftime('%Y-%m-%d')}.csv",
            mime="text/csv",
        )
