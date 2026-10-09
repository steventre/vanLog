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

# Initialize session state for storing logs if not already present
if "log_history" not in st.session_state:
    st.session_state.log_history = []

# Helper function to get current UTC-5 time in 12-hour components
def get_current_utc5_components():
    utc_minus_5 = datetime.utcnow() - timedelta(hours=5)
    hour_24 = utc_minus_5.hour
    minute = utc_minus_5.minute
    
    is_pm = hour_24 >= 12
    hour_12 = hour_24 % 12
    if hour_12 == 0:
        hour_12 = 12
    return hour_12, minute, ("PM" if is_pm else "AM")

cur_h, cur_m, cur_ap = get_current_utc5_components()

# Helper function to render a 12-hour AM/PM time selector block (with optional blank support)
def render_time_selector(label, default_h, default_m, default_ap, key_prefix, allow_blank=False):
    st.markdown(f"**{label} (UTC-5)**")
    c1, c2, c3 = st.columns(3)
    
    hour_options = ["--"] + list(range(1, 13)) if allow_blank else list(range(1, 13))
    default_h_idx = 0 if allow_blank and default_h is None else (default_h - 1 if not allow_blank else default_h)
    
    with c1:
        h = st.selectbox("Hour", hour_options, index=default_h_idx if isinstance(default_h_idx, int) else 0, key=f"{key_prefix}_h")
    with c2:
        m = st.selectbox("Min", list(range(0, 60)), index=default_m if default_m is not None else 0, key=f"{key_prefix}_m")
    with c3:
        ap = st.selectbox("AM/PM", ["AM", "PM"], index=0 if default_ap == "AM" else 1, key=f"{key_prefix}_ap")
    
    if h == "--":
        return ""
    return f"{h}:{m:02d} {ap}"

# Helper function to parse existing time string back into components for the edit form
def parse_time_string(time_str):
    if not time_str:
        return None, 0, "AM"
    try:
        parts = time_str.split()
        hm = parts[0].split(":")
        h = int(hm[0])
        m = int(hm[1])
        ap = parts[1] if len(parts) > 1 else "AM"
        return h, m, ap
    except (ValueError, IndexError):
        return None, 0, "AM"

# --- FORM INPUTS ---
with st.form("vehicle_log_form", clear_on_submit=True):
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
        start_time_str = render_time_selector("Start Time", cur_h, cur_m, cur_ap, "main_start", allow_blank=False)

    with col4:
        end_mileage = st.number_input(
            "Ending Mileage (Optional)", min_value=0, value=None, step=1, format="%d"
        )
        end_time_str = render_time_selector("End Time", None, 0, "AM", "main_end", allow_blank=True)

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
            st.success("Trip successfully logged!")

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
                
                # Parse existing times for edit form
                est_h, est_m, est_ap = parse_time_string(trip["Start Time"])
                if est_h is None:
                    est_h, est_m, est_ap = cur_h, cur_m, cur_ap
                e_start_time_str = render_time_selector("Start Time", est_h, est_m, est_ap, f"ed_start_{idx}", allow_blank=False)

                eet_h, eet_m, eet_ap = parse_time_string(trip["End Time"])
                e_end_time_str = render_time_selector("End Time", eet_h, eet_m, eet_ap, f"ed_end_{idx}", allow_blank=True)
                
                e_saved = st.form_submit_button("Update Trip Entry")
                if e_saved:
                    calc_sm = e_start_m if e_start_m is not None else 0
                    calc_em = e_end_m if e_end_m is not None else 0
                    calc_total = calc_em - calc_sm if calc_em >= calc_sm else 0

                    st.session_state.log_history[idx]["Date"] = e_date.strftime("%Y-%m-%d")
                    st.session_state.log_history[idx]["Destination / Purpose"] = e_dest
                    st.session_state.log_history[idx]["Start Mileage"] = calc_sm
                    st.session_state.log_history[idx]["End Mileage"] = calc_em
                    st.session_state.log_history[idx]["Start Time"] = e_start_time_str
                    st.session_state.log_history[idx]["End Time"] = e_end_time_str
                    st.session_state.log_history[idx]["Total Miles"] = calc_total
                    st.success("Trip updated successfully!")
                    st.rerun()

    df_logs = pd.DataFrame(st.session_state.log_history)
    st.dataframe(df_logs, use_container_width=True)

    csv = df_logs.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Log as CSV (Excel Compatible)",
        data=csv,
        file_name=f"vehicle_usage_log_{datetime.today().strftime('%Y-%m-%d')}.csv",
        mime="text/csv",
    )
