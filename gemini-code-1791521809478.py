from datetime import datetime, time, timedelta
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
    return utc_minus_5.time()

current_t = get_utc_minus_5_time()

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
        # Native time input defaulting to current UTC-5 time
        start_time = st.time_input("Start Time (UTC-5)", value=current_t)

    with col4:
        end_mileage = st.number_input(
            "Ending Mileage", min_value=0, value=None, step=1, format="%d"
        )
        # Native time input defaulting to current UTC-5 time (identical field)
        end_time = st.time_input("End Time (UTC-5)", value=current_t)

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
            "Date": trip_date.strftime("%Y-%m-%d"),
            "Driver": driver_name,
            "Vehicle": vehicle,
            "Destination / Purpose": destination,
            "Start Mileage": s_mileage,
            "End Mileage": e_mileage,
            "Total Miles": total_miles,
            "Start Time": start_time.strftime("%I:%M %p").lstrip("0"),
            "End Time": end_time.strftime("%I:%M %p").lstrip("0"),
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
                
                # Parse existing time strings back into time objects for the identical time inputs
                try:
                    default_st_t = datetime.strptime(trip["Start Time"], "%I:%M %p").time()
                except ValueError:
                    default_st_t = current_t

                try:
                    default_et_t = datetime.strptime(trip["End Time"], "%I:%M %p").time()
                except ValueError:
                    default_et_t = current_t

                # Identical time inputs in the edit section
                e_start_time = st.time_input("Start Time (UTC-5)", value=default_st_t, key=f"ed_st_{idx}")
                e_end_time = st.time_input("End Time (UTC-5)", value=default_et_t, key=f"ed_et_{idx}")
                
                e_saved = st.form_submit_button("Update Trip Entry")
                if e_saved:
                    calc_sm = e_start_m if e_start_m is not None else 0
                    calc_em = e_end_m if e_end_m is not None else 0
                    calc_total = calc_em - calc_sm if calc_em >= calc_sm else 0

                    st.session_state.log_history[idx]["Date"] = e_date.strftime("%Y-%m-%d")
                    st.session_state.log_history[idx]["Destination / Purpose"] = e_dest
                    st.session_state.log_history[idx]["Start Mileage"] = calc_sm
                    st.session_state.log_history[idx]["End Mileage"] = calc_em
                    st.session_state.log_history[idx]["Start Time"] = e_start_time.strftime("%I:%M %p").lstrip("0")
                    st.session_state.log_history[idx]["End Time"] = e_end_time.strftime("%I:%M %p").lstrip("0")
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
