import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

DATA_FILE = "finance_data.csv"

def load_data():
    try:
        df = pd.read_csv(DATA_FILE, parse_dates=['Date'])
    except FileNotFoundError:
        df = pd.DataFrame(columns=['Date', 'Type', 'Category', 'Amount', 'Description'])
    return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def add_transaction(date, ttype, category, amount, description):
    df = load_data()
    new_entry = {
        "Date": date,
        "Type": ttype,
        "Category": category,
        "Amount": amount,
        "Description": description
    }
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    save_data(df)

st.title("📊 Personal Finance Tracker")

st.sidebar.header("Add Transaction")
with st.sidebar.form("entry_form"):
    ttype = st.radio("Type", ["Income", "Expense"])
    date = st.date_input("Date", datetime.today())
    category = st.selectbox("Category", ["Salary", "Groceries", "Bills", "Entertainment", "Investment", "Other"])
    amount = st.number_input("Amount", min_value=0.01, format="%.2f")
    description = st.text_input("Description")
    submitted = st.form_submit_button("Add")
    if submitted:
        add_transaction(date, ttype, category, amount if ttype=="Income" else -amount, description)
        st.success("Transaction added!")

df = load_data()
if df.empty:
    st.info("No data. Add a transaction to get started!")
else:
    # Analytics
    st.header("Summary")
    total_income = df[df['Amount'] > 0]['Amount'].sum()
    total_expense = -df[df['Amount'] < 0]['Amount'].sum()
    balance = total_income - total_expense

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Income", f"${total_income:,.2f}")
    col2.metric("Total Expense", f"${total_expense:,.2f}")
    col3.metric("Balance", f"${balance:,.2f}")

    st.subheader("All Transactions")
    st.dataframe(df.sort_values("Date", ascending=False).reset_index(drop=True))

    # Charts
    st.header("Visual Analytics")

    df['AmountAbs'] = df['Amount'].abs()
    df['Month'] = df['Date'].dt.to_period('M')

    fig1 = px.bar(df, x='Date', y='Amount', color='Type', title="Cash Flow Over Time")
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = px.pie(df[df['Amount'] < 0], names='Category', values='AmountAbs', title="Expense Breakdown by Category")
    st.plotly_chart(fig2, use_container_width=True)

    monthly = df.groupby(['Month', 'Type'])['Amount'].sum().reset_index()
    fig3 = px.bar(monthly, x='Month', y='Amount', color='Type', barmode='group', title="Monthly Income vs Expenses")
    st.plotly_chart(fig3, use_container_width=True)