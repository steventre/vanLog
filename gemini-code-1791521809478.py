from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="High School Vehicle Usage Log", page_icon="🚐", layout="centered"
)

# Initialize session state for storing logs, form reset counter, and individual print views
if "log_history" not in st.session_state:
    st.session_state.log_history = []
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

# Helper function ensuring identical layout (HH:MM text box + AM/PM dropdown) for both start and end times
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

# --- INDIVIDUAL PRINT VIEW SCREEN ---
if st.session_state.print_target_idx is not None and st.session_state.print_target_idx < len(st.session_state.log_history):
    idx = st.session_state.print_target_idx
    trip = st.session_state.log_history[idx]
    
    st.title("🚐 Vehicle Usage Log - Trip Receipt")
    st.markdown(f"**Trip #{idx + 1} Report** (Generated: {datetime.today().strftime('%Y-%m-%d')})")
    st.markdown("---")

    # Clean vertical layout for full-page individual printing
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

    st.markdown("---")
    if st.button("⬅️ Back to Entry Form & Log History"):
        st.session_state.print_target_idx = None
        st.rerun()

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

        st.markdown("---")
        st.subheader("Student Passengers")

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

        selected_students = st.multiselect(
            "Select Students on Trip (Alphabetical, Required)", sorted_students
        )

        submitted = st.form_submit_button("Save Trip Entry")

        if submitted:
            if not driver_name.strip():
                st.error("Driver Name is required.")
            elif start_mileage is None:
                st.error("Starting Mileage is required.")
            elif not selected_students:
                st.error("Please select at least one student passenger.")
            elif not start_time_str:
                st.error("Start Time is required.")
            else:
                s_mileage = start_mileage
