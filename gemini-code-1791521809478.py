from datetime import datetime
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
        # Using text_input for mileage so it's easy to clear/type over without fighting default zeros
        start_mileage_str = st.text_input("Starting Mileage", value="0")
        
        # Start time defaults to right now (formatted in 12-hour AM/PM)
        start_time = st.time_input(
            "Start Time", 
            value=datetime.now().time()
        )
    with col4:
        end_mileage_str = st.text_input("Ending Mileage", value="0")
        
        end_time = st.time_input(
            "End Time", 
            value=datetime.now().time()
        )

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
        # Convert mileage inputs safely to integers
        try:
            start_mileage = int(start_mileage_str)
        except ValueError:
            start_mileage = 0

        try:
            end_mileage = int(end_mileage_str)
        except ValueError:
            end_mileage = 0

        # Calculations
        total_miles = (
            end_mileage - start_mileage if end_mileage >= start_mileage else 0
        )

        trip_entry = {
            "Date": trip_date.strftime("%Y-%m-%d"),
            "Driver": driver_name,
            "Vehicle": vehicle,
            "Destination / Purpose": destination,
            "Start Mileage": start_mileage,
            "End Mileage": end_mileage,
            "Total Miles": total_miles,
            "Start Time": start_time.strftime("%I:%M %p"),
            "End Time": end_time.strftime("%I:%M %p"),
            "Students": ", ".join(selected_students),
        }

        st.session_state.log_history.append(trip_entry)
        st.success("Trip successfully logged!")

# --- PRINTABLE & EXPORTABLE LOG ---
if st.session_state.log_history:
    st.markdown("---")
    st.subheader("📋 Printable Vehicle Log")
    st.info(
        "Tip: Use your browser's print function (`Ctrl+P` or `Cmd+P`) to print this section cleanly."
    )

    # Convert log history to DataFrame
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
