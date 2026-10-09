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

# Helper function to get current time in UTC-5
def get_utc_minus_5_time():
    # UTC offset for UTC-5
    utc_minus_5 = datetime.utcnow() - timedelta(hours=5)
    return utc_minus_5.time()

current_t = get_utc_minus_5_time()
current_hour_24 = current_t.hour
current_minute = current_t.minute

# Convert to 12-hour format for the dropdown defaults
default_is_pm = current_hour_24 >= 12
default_hour_12 = current_hour_24 % 12
if default_hour_12 == 0:
    default_hour_12 = 12

# --- FORM INPUTS ---
with st.form("vehicle_log_form"):
    st.subheader("Trip Details")

    col1, col2 = st.columns(2)
    with col1:
        # Default driver name
        driver_name = st.text_input("Driver Name", value="Steven Hartl")
    with col2:
        # Default to today's date
        trip_date = st.date_input("Date", value=datetime.today())

    # Vehicle Selection Field
    vehicle = st.selectbox(
        "Select Vehicle",
        ["Silver Van", "White Van", "Honda Pilot"]
    )

    # Destination / Purpose defaulted to "Nehemiah 2.0"
    destination = st.text_input("Destination / Purpose", value="Nehemiah 2.0")

    st.markdown("---")
    st.subheader("Mileage & Time Tracking")

    col3, col4 = st.columns(2)
    with col3:
        # Numeric field only, blank by default (value=None)
        start_mileage = st.number_input(
            "Starting Mileage", min_value=0, value=None, step=1, format="%d"
        )
        
        st.markdown("**Start Time (UTC-5)**")
        t_col1, t_col2, t_col3 = st.columns(3)
        with t_col1:
            start_h = st.selectbox("Hour", list(range(1, 13)), index=default_hour_12 - 1, key="start_h")
        with t_col2:
            start_m = st.selectbox("Min", list(range(0, 60)), index=current_minute, key="start_m")
        with t_col3:
            start_ap = st.selectbox("AM/PM", ["AM", "PM"], index=1 if default_is_pm else 0, key="start_ap")

    with col4:
        end_mileage = st.number_input(
            "Ending Mileage", min_value=0, value=None, step=1, format="%d"
        )
        
        st.markdown("**End Time (UTC-5)**")
        te_col1, te_col2, te_col3 = st.columns(3)
        with te_col1:
            end_h = st.selectbox("Hour", list(range(1, 13)), index=default_hour_12 - 1, key="end_h")
        with te_col2:
            end_m = st.selectbox("Min", list(range(0, 60)), index=current_minute, key="end_m")
        with te_col3:
            end_ap = st.selectbox("AM/PM", ["AM", "PM"], index=1 if default_is_pm else 0, key="end_ap")

    st.markdown("---")
    st.subheader("Student Passengers")

    # Provided student list, sorted alphabetically
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
        "Select Students on Trip (Alphabetical)", sorted_students
    )

    # Submit button
    submitted = st.form_submit_button("Save Trip Entry")

    if submitted:
        s_mileage = start_mileage if start_mileage is not None else 0
        e_mileage = end_mileage if end_mileage is not None else 0
        total_miles = e_mileage - s_mileage if e_mileage >= s_mileage else 0

        start_time_str = f"{start_h}:{start_m:02d} {start_ap}"
        end_time_str = f"{end_h}:{end_m:02d} {end_ap}"

        trip_entry = {
            "Date": trip_date.strftime("%Y-%m-%d"),
            "Driver": driver_name,
            "Vehicle": vehicle,
            "Destination / Purpose": destination,
            "Start Mileage": s_mileage,
            "End Mileage": e_mileage,
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
        "Tip: Use your browser's print function (`Ctrl+P` or `Cmd+P`) to print this section cleanly. You can also expand records below to update end times or ending mileage later."
    )

    # Interactive Editing section for recorded trips
    for idx, trip in enumerate(st.session_state.log_history):
        with st.expander(f"Trip #{idx + 1}: {trip['Date']} - {trip['Vehicle']} (Driver: {trip['Driver']})"):
            with st.form(f"edit_form_{idx}"):
                e_dest = st.text_input("Destination / Purpose", value=trip["Destination / Purpose"], key=f"ed_dest_{idx}")
                e_start_m = st.number_input("Start Mileage", min_value=0, value=int(trip["Start Mileage"]), step=1, key=f"ed_sm_{idx}")
                e_end_m = st.number_input("End Mileage", min_value=0, value=int(trip["End Mileage"]), step=1, key=f"ed_em_{idx}")
                
                e_saved = st.form_submit_button("Update Trip Entry")
                if e_saved:
                    calc_total = e_end_m - e_start_m if e_end_m >= e_start_m else 0
                    st.session_state.log_history[idx]["Destination / Purpose"] = e_dest
                    st.session_state.log_history[idx]["Start Mileage"] = e_start_m
                    st.session_state.log_history[idx]["End Mileage"] = e_end_m
                    st.session_state.log_history[idx]["Total Miles"] = calc_total
                    st.success("Trip updated successfully!")
                    st.rerun()

    # Convert log history to DataFrame for viewing and downloading
    df_logs = pd.DataFrame(st.session_state.log_history)

    # Display as a clean table
    st.dataframe(df_logs, use_container_width=True)

    # CSV Download Button for record keeping
    csv = df_logs.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Log as CSV (Excel Compatible)",
        data=csv,
        file_name=f"vehicle_usage_log_{datetime.today().strftime('%Y-%m-%d')}.csv",
        mime="text/csv",
    )
