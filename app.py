import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os

st.set_page_config(page_title="Cost Tracker", layout="centered", initial_sidebar_state="collapsed")

st.title("🏗️ Cost Tracker")

# Create receipts folder
if not os.path.exists("receipts"):
    os.makedirs("receipts")

# ====================== DATABASE ======================
def init_db():
    conn = sqlite3.connect('company_costs.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS jobs (job_name TEXT PRIMARY KEY)''')
    
    default_jobs = ["Office Renovation", "Kitchen Remodel", "Bathroom Addition", "Deck Build", "General Maintenance"]
    for job in default_jobs:
        c.execute("INSERT OR IGNORE INTO jobs (job_name) VALUES (?)", (job,))
    
    c.execute('''CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY, date TEXT, job_name TEXT, category TEXT,
                    description TEXT, amount REAL, receipt_path TEXT, entered_by TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS time_entries (
                    id INTEGER PRIMARY KEY, date TEXT, employee TEXT, job_name TEXT,
                    task TEXT, hours REAL, rate REAL, entered_by TEXT)''')
    conn.commit()
    conn.close()

init_db()

def get_jobs():
    conn = sqlite3.connect('company_costs.db')
    jobs = pd.read_sql_query("SELECT job_name FROM jobs", conn)['job_name'].tolist()
    conn.close()
    return jobs

def add_job(job_name):
    conn = sqlite3.connect('company_costs.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO jobs (job_name) VALUES (?)", (job_name,))
    conn.commit()
    conn.close()

def add_expense(date, job, cat, desc, amt, receipt_path, entered_by):
    conn = sqlite3.connect('company_costs.db')
    c = conn.cursor()
    c.execute("INSERT INTO expenses VALUES (NULL,?,?,?,?,?,?,?)", (date, job, cat, desc, amt, receipt_path, entered_by))
    conn.commit()
    conn.close()

def add_time_entry(date, emp, job, task, hours, rate, entered_by):
    conn = sqlite3.connect('company_costs.db')
    c = conn.cursor()
    c.execute("INSERT INTO time_entries VALUES (NULL,?,?,?,?,?,?,?)", (date, emp, job, task, hours, rate, entered_by))
    conn.commit()
    conn.close()

def get_expenses():
    conn = sqlite3.connect('company_costs.db')
    df = pd.read_sql_query("SELECT * FROM expenses ORDER BY date DESC", conn)
    conn.close()
    return df

def get_time_entries():
    conn = sqlite3.connect('company_costs.db')
    df = pd.read_sql_query("SELECT * FROM time_entries ORDER BY date DESC", conn)
    conn.close()
    return df

# ====================== NAVIGATION ======================
page = st.sidebar.selectbox("Go to", ["Quick Log", "Dashboard", "All Expenses", "All Time Entries", "Manage Jobs"])

if page == "Quick Log":
    st.header("Quick Entry")
    tab1, tab2 = st.tabs(["💰 Expense", "⏱️ Time"])
    
    with tab1:
        st.subheader("New Expense")
        jobs = get_jobs()
        date = st.date_input("Date", datetime.today())
        job = st.selectbox("Job", jobs, key="q_job")
        
        new_job = st.text_input("New Job Name (optional)")
        if new_job and st.button("Add Job"):
            add_job(new_job)
            st.success("Job added")
            st.rerun()
        
        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox("Category", ["Materials", "Tools", "Fuel", "Other"])
            amount = st.number_input("Amount ($)", min_value=0.01, step=1.0)
        with col2:
            description = st.text_input("Description")
            entered_by = st.text_input("Entered by", value="Daylan")
        
        receipt = st.file_uploader("Receipt Photo", type=["jpg", "jpeg", "png"])
        
        if st.button("Save Expense", type="primary", use_container_width=True):
            receipt_path = None
            if receipt:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                receipt_path = f"receipts/{ts}_{receipt.name}"
                with open(receipt_path, "wb") as f:
                    f.write(receipt.getbuffer())
            add_expense(str(date), job, category, description, amount, receipt_path, entered_by)
            st.success("✅ Expense Saved!")

    with tab2:
        st.subheader("New Time Entry")
        jobs = get_jobs()
        date = st.date_input("Date", datetime.today(), key="t_date")
        job = st.selectbox("Job", jobs, key="t_job")
        employee = st.text_input("Employee")
        task = st.text_input("Task")
        col1, col2 = st.columns(2)
        with col1:
            hours = st.number_input("Hours", min_value=0.25, step=0.25)
        with col2:
            rate = st.number_input("Rate $/hr", min_value=0.0, value=45.0, step=5.0)
        entered_by = st.text_input("Entered by", value="Daylan", key="e_by")
        
        if st.button("Save Time", type="primary", use_container_width=True):
            add_time_entry(str(date), employee, job, task, hours, rate, entered_by)
            st.success("✅ Time Saved!")

elif page == "Dashboard":
    st.header("📊 Dashboard")
    exp = get_expenses()
    time = get_time_entries()
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Spent", f"${exp['amount'].sum():,.0f}" if not exp.empty else "$0")
    c2.metric("Total Hours", f"{time['hours'].sum():.1f}" if not time.empty else "0")
    c3.metric("Est. Labor", f"${(time['hours']*time.get('rate',0)).sum():,.0f}" if not time.empty else "$0")
    st.info("Charts available in full version later")

elif page == "All Expenses":
    st.header("All Expenses")
    df = get_expenses()
    st.dataframe(df, use_container_width=True)
    if not df.empty:
        st.download_button("Download CSV", df.to_csv(index=False), "expenses.csv", use_container_width=True)

elif page == "All Time Entries":
    st.header("All Time Entries")
    df = get_time_entries()
    st.dataframe(df, use_container_width=True)
    if not df.empty:
        st.download_button("Download CSV", df.to_csv(index=False), "time.csv", use_container_width=True)

elif page == "Manage Jobs":
    st.header("Manage Jobs")
    jobs = get_jobs()
    st.write("Current Jobs:", ", ".join(jobs) if jobs else "None")
    new_job = st.text_input("Add New Job")
    if st.button("Add", use_container_width=True) and new_job:
        add_job(new_job)
        st.success("Job added!")
        st.rerun()

st.caption("Data saved locally • Back up company_costs.db")
