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
default_hour_12 = current_dt.strftime("%I").lstrip("0")
if not default_hour_12:
    default_hour_12 = "12"
default_min = current_dt.strftime("%M")
default_am_pm = current_dt.strftime("%p")

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
        
        st.markdown("**Start Time (UTC-5)**")
        st_c1, st_c2 = st.columns([2, 1])
        with st_c1:
            start_time_input = st.text_input("Time (HH:MM)", value=f"{default_hour_12}:{default_min}", key="main_st")
        with st_c2:
            start_ampm = st.selectbox("AM/PM", ["AM", "PM"], index=0 if default_am_pm == "AM" else 1, key="main_sap")

    with col4:
        end_mileage = st.number_input(
            "Ending Mileage", min_value=0, value=None, step=1, format="%d"
        )
        
        st.markdown("**End Time (UTC-5)**")
        et_c1, et_c2 = st.columns([2, 1])
        with et_c1:
            end_time_input = st.text_input("Time (HH:MM)", value="", placeholder="e.g. 4:15", key="main_et")
        with et_c2:
            end_ampm = st.selectbox("AM/PM", ["AM", "PM"], index=1, key="main_eap")

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

        final_start_time = f"{start_time_input} {start_ampm}".strip() if start_time_input else ""
        final_end_time = f"{end_time_input} {end_ampm}".strip() if end_time_input else ""

        trip_entry = {
            "Date": trip_date.strftime("%Y-%m-%d"),
            "Driver": driver_name,
            "Vehicle": vehicle,
            "Destination / Purpose": destination,
            "Start Mileage": s_mileage,
            "End Mileage": e_mileage,
            "Total Miles": total_miles,
            "Start Time": final_start_time,
            "End Time": final_end_time,
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
                
                # Blank-capable mileage fields for editing
                existing_sm = int(trip["Start Mileage"]) if trip["Start Mileage"] != 0 else None
                existing_em = int(trip["End Mileage"]) if trip["End Mileage"] != 0 else None
                
                e_start_m = st.number_input("Start Mileage", min_value=0, value=existing_sm, step=1, format="%d", key=f"ed_sm_{idx}")
                e_end_m = st.number_input("End Mileage", min_value=0, value=existing_em, step=1, format="%d", key=f"ed_em_{idx}")
                
                # Parse existing start/end time components if present to prepopulate edit fields cleanly
                st_parts = trip["Start Time"].split()
                st_val = st_parts[0] if len(st_parts) > 0 else ""
                st_ap_idx = 1 if len(st_parts) > 1 and st_parts[1] == "PM" else 0

                et_parts = trip["End Time"].split()
                et_val = et_parts[0] if len(et_parts) > 0 else ""
                et_ap_idx = 1 if len(et_parts) > 1 and et_parts[1] == "PM" else 0

                st.markdown("**Start Time**")
                ed_st_c1, ed_st_c2 = st.columns([2, 1])
                with ed_st_c1:
                    e_st_input = st.text_input("Time", value=st_val, key=f"ed_st_{idx}")
                with ed_st_c2:
                    e_st_ap = st.selectbox("AM/PM", ["AM", "PM"], index=st_ap_idx, key=f"ed_sap_{idx}")

                st.markdown("**End Time**")
                ed_et_c1, ed_et_c2 = st.columns([2, 1])
                with ed_et_c1:
                    e_et_input = st.text_input("Time", value=et_val, key=f"ed_et_{idx}")
                with ed_et_c2:
                    e_et_ap = st.selectbox("AM/PM", ["AM", "PM"], index=et_ap_idx, key=f"ed_eap_{idx}")
                
                e_saved = st.form_submit_button("Update Trip Entry")
                if e_saved:
                    calc_sm = e_start_m if e_start_m is not None else 0
                    calc_em = e_end_m if e_end_m is not None else 0
                    calc_total = calc_em - calc_sm if calc_em >= calc_sm else 0
                    
                    updated_start_t = f"{e_st_input} {e_st_ap}".strip() if e_st_input else ""
                    updated_end_t = f"{e_et_input} {e_et_ap}".strip() if e_et_input else ""

                    st.session_state.log_history[idx]["Date"] = e_date.strftime("%Y-%m-%d")
                    st.session_state.log_history[idx]["Destination / Purpose"] = e_dest
                    st.session_state.log_history[idx]["Start Mileage"] = calc_sm
                    st.session_state.log_history[idx]["End Mileage"] = calc_em
                    st.session_state.log_history[idx]["Start Time"] = updated_start_t
                    st.session_state.log_history[idx]["End Time"] = updated_end_t
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
