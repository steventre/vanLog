from datetime import datetime, timedelta
import sqlite3
import pandas as pd
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Vehicle Use Log", page_icon="🚐", layout="centered"
)

# Custom CSS to strip top padding and force side-by-side buttons on mobile
st.markdown("""
    <style>
    /* Remove Streamlit's default top header whitespace/padding */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }
    header {
        visibility: hidden !important;
        height: 0px !important;
    }

    /* Force side-by-side buttons inside expander on mobile */
    [data-testid="stExpander"] [data-testid="column"] {
        width: calc(33.333% - 1rem) !important;
        flex: 1 1 calc(33.333% - 1rem) !important;
        min-width: 70px !important;
    }
    [data-testid="stExpander"] [data-testid="horizontal-block"] {
        flex-direction: row !important;
        align-items: center !important;
        gap: 0.5rem !important;
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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?,
