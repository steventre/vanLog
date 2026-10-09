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
    utc_minus_5 = datetime.utcnow() - timedelta(hours=5)
    return utc_minus_5

current_dt = get_utc_minus_5_time()
default_start_time_str = current_dt.strftime("%I:%M %p").lstrip("0")

# --- FORM INPUTS ---
with st.form("vehicle_log_form"):
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
            "Starting Mileage", min_value=0, value=None, step=1, format="%d"
        )
        # Start time defaults to current time
        start_time = st.text_input("Start Time (e.g., 08:30 AM)", value=default_start_time_str)

    with col4:
        end_mileage = st.number_input(
            "Ending Mileage", min_value=0, value=None, step=1, format="%d"
        )
        # End time defaults to blank
        end_time = st.text_input("End Time (e.g., 04:15 PM)", value="")

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
        "Select Students on Trip (Alphabetical)", sorted_students
    )

    submitted = st.form_submit_button("Save Trip Entry")

    if submitted:
        s_mileage = start_mileage if start_mileage is not None else 0
        e_mileage = end_mileage if end_mileage is not None else 0
        total_miles = e_mileage - s_mileage if e_mileage >= s_mileage else 0

        trip_entry = {
            "Date": trip_date.strftime("%m/%d/%Y"),
            "Driver": driver_name,
            "Vehicle": vehicle,
            "Destination / Purpose": destination,
            "Start Mileage": s_mileage,
            "End Mileage": e_mileage,
            "Total Miles": total_miles,
            "Start Time": start_time,
            "End Time": end_time,
            "Students": ", ".join(selected_students),
        }

        st.session_state.log_history.append(trip_entry)
        st.success("Trip successfully logged!")

# --- PRINTABLE & EDITABLE LOG ---
if st.session_state.log_history:
    st.markdown("---")
    st.subheader("📋 Printable & Editable Vehicle Log")
    st.info(
        "Tip: Use your browser's print function (`Ctrl+P` or `Cmd+P`) to print this section cleanly. Expand records below to update end times or ending mileage later."
    )

    # Interactive Editing section for recorded trips
    for idx, trip in enumerate(st.session_state.log_history):
        with st.expander(f"Trip #{idx + 1}: {trip['Date']} - {trip['Vehicle']} (Driver: {trip['Driver']})"):
            with st.form(f"edit_form_{idx}"):
                e_dest = st.text_input("Destination / Purpose", value=trip["Destination / Purpose"], key=f"ed_dest_{idx}")
                e_start_m = st.number_input("Start Mileage", min_value=0, value=int(trip["Start Mileage"]), step=1, key=f"ed_sm_{idx}")
                e_end_m = st.number_input("End Mileage", min_value=0, value=int(trip["End Mileage"]), step=1, key=f"ed_em_{idx}")
                e_end_t = st.text_input("End Time", value=trip["End Time"], key=f"ed_et_{idx}")
                
                e_saved = st.form_submit_button("Update Trip Entry")
                if e_saved:
                    calc_total = e_end_m - e_start_m if e_end_m >= e_start_m else 0
                    st.session_state.log_history[idx]["Destination / Purpose"] = e_dest
                    st.session_state.log_history[idx]["Start Mileage"] = e_start_m
                    st.session_state.log_history[idx]["End Mileage"] = e_end_m
                    st.session_state.log_history[idx]["End Time"] = e_end_t
                    st.session_state.log_history[idx]["Total Miles"] = calc_total
                    st.success("Trip updated successfully!")
                    st.rerun()

    df_logs = pd.DataFrame(st.session_state.log_history)
    st.dataframe(df_logs, use_container_width=True)

    csv = df_logs.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Log as CSV (Excel Compatible)",
        data=csv,
        file_name=f"vehicle_usage_log_{datetime.today().strftime('%m-%d-%Y')}.csv",
        mime="text/csv",
    )
