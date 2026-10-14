if submitted:
            start_time_str = f"{start_t_val.strip()} {start_ap_val}" if start_t_val.strip() else ""
            end_time_str = f"{end_t_val.strip()} {end_ap_val}" if end_t_val.strip() and end_ap_val != "--" else ""

            if not driver_name.strip():
                st.error("Driver Name is required.")
            elif start_mileage is None:
                st.error("Starting Mileage is required.")
            elif not selected_students:
                st.error("Please select at least one student passenger.")
            elif not start_time_str:
                st.error("Start Time is required.")
            else:
                s_mileage = int(start_mileage)
                # Only default end mileage to start mileage if end mileage wasn't provided, 
                # or keep it 0 / blank if left empty. Let's make it 0 if empty.
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
                    "Start Time": start_time_str,
                    "End Time": end_time_str,
                    "Students": ", ".join(selected_students),
                }

                save_log_to_db(trip_entry)
                st.session_state.log_history = load_logs_from_db()
                st.session_state.form_counter += 1
                st.session_state.main_end_time_val = ""
                st.session_state.main_end_ap_val = "--"
                st.success("Trip successfully logged and saved to database!")
                st.rerun()
