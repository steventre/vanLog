from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="High School Vehicle Usage Log", page_icon="🚐", layout="centered"
)

# App Header
st.title("🚐 High School Vehicle Usage Log")
st.markdown("Record vehicle trips, destinations, passengers, and mileage for school transport.")

# Initialize session state for storing logs and form reset counter
if "log_history" not in st.session_state:
    st.session_state.log_history = []
if "form_counter" not in st.session_state:
    st.session_state.form_counter = 0

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

# Helper function to render an identical HH:MM text input + AM/PM dropdown for both start and end
def render_time_input(label, default_time, default_ampm, key_prefix, allow_blank=False):
    st.markdown(f"**{label} (UTC-5)**")
    c1, c2 = st.columns([2, 1])
    
    with c1:
        t_val = st.text_input("Time (HH:MM)", value=default_time, placeholder="e.g. 04:15", key=f"{key_prefix}_time")
    with c2:
        ap_options = ["--", "AM", "PM"] if allow_blank else ["AM", "PM"]
        default_ap_idx = 0 if allow_blank and not default_ampm else (ap_options.index(default_ampm) if default_ampm in ap_options else 1)
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

# --- FORM INPUTS (Dynamic key forces clean reset on success) ---
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
        # End time uses the exact same layout, defaulting to blank with "--" option
        end_time_str = render_time_input("End Time", "", "", "main_end", allow_blank=True)

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
                "Students": ", ".join(selected_students),
            }

            st.session_state.log_history.append(trip_entry)
            st.session_state.form_counter += 1
            st.success("Trip successfully logged!")
            st.rerun()

# --- PRINTABLE & EDITABLE LOG ---
if st.session_state.log_history:
    st.markdown("---")
    st.subheader("📋 Printable & Editable Vehicle Log")
    st.info(
        "Tip: Use your browser's print function (`Ctrl+P` or `Cmd+P`) to print this section cleanly. Expand records below to update mileage or times later."
    )

    # Interactive Editing section for recorded trips
    for idx, trip in enumerate(st.session_state.log_history):
        with st.expander(f"Trip #{idx + 1}: {trip['Date']} - {trip['Vehicle']} (Driver: {trip['Driver']})"):
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
                
                # Identical time inputs for edit form
                est_t, est_ap = parse_
