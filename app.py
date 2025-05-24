import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
import numpy as np
import os
import uuid

# Page configuration
st.set_page_config(
    page_title="Personal Finance Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with black text for metrics and cards
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        border: 1px solid #e0e0e0;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        color: black !important;
    }
    .stMetric label, .stMetric div {
        color: black !important;
    }
    .big-font {
        font-size: 24px !important;
        font-weight: bold;
        color: black !important;
    }
    .expense-card {
        background: linear-gradient(135deg, #ff6b6b, #ee5a5a);
        color: black !important;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .income-card {
        background: linear-gradient(135deg, #51cf66, #40c057);
        color: black !important;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

DATA_FILE = "finance_data.csv"

# Categories
INCOME_CATEGORIES = [
    "Salary", "Freelance", "Investment Returns", "Rental Income", 
    "Business", "Gifts", "Refunds", "Other Income"
]

EXPENSE_CATEGORIES = [
    "Housing", "Transportation", "Food & Dining", "Groceries", 
    "Utilities", "Healthcare", "Entertainment", "Shopping", 
    "Education", "Travel", "Insurance", "Subscriptions", 
    "Debt Payments", "Savings", "Other Expenses"
]

@st.cache_data
def load_data():
    """Load data with enhanced error handling and data validation"""
    try:
        if not os.path.exists(DATA_FILE):
            return pd.DataFrame(columns=['Date', 'Type', 'Category', 'Amount', 'Description', 'Tags'])
        
        df = pd.read_csv(DATA_FILE, parse_dates=['Date'])
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        df = df.dropna(subset=['Amount', 'Date'])
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(columns=['Date', 'Type', 'Category', 'Amount', 'Description', 'Tags'])

def save_data(df):
    """Save data with backup and error handling"""
    try:
        if os.path.exists(DATA_FILE):
            backup_file = f"{DATA_FILE}.{uuid.uuid4()}.bak"
            df.to_csv(backup_file, index=False)
        df.to_csv(DATA_FILE, index=False)
    except Exception as e:
        st.error(f"Error saving data: {e}")
        return False
    return True

def add_transaction(date_input, ttype, category, amount, description, tags=""):
    """Add transaction with validation"""
    if isinstance(date_input, date) and date_input > date.today():
        st.warning("Cannot add future-dated transactions.")
        return False

    df = load_data()
    final_amount = amount if ttype == "Income" else -amount

    new_entry = {
        "Date": pd.to_datetime(date_input),
        "Type": ttype,
        "Category": category,
        "Amount": final_amount,
        "Description": description,
        "Tags": tags.strip()
    }

    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    return save_data(df)

def delete_transaction(index):
    """Delete a transaction by index"""
    df = load_data()
    if 0 <= index < len(df):
        df = df.drop(df.index[index]).reset_index(drop=True)
        return save_data(df)
    return False

def get_financial_insights(df):
    """Generate financial insights and recommendations"""
    if df.empty:
        return []
    
    insights = []
    total_income = df[df['Amount'] > 0]['Amount'].sum()
    total_expenses = abs(df[df['Amount'] < 0]['Amount'].sum())
    
    if total_income > 0:
        savings_rate = ((total_income - total_expenses) / total_income) * 100
        if savings_rate > 20:
            insights.append("🎉 Excellent! You're saving over 20% of your income.")
        elif savings_rate > 10:
            insights.append("👍 Good job! You're saving over 10% of your income.")
        elif savings_rate > 0:
            insights.append("💡 Consider increasing your savings rate to at least 10%.")
        else:
            insights.append("⚠️ You're spending more than you earn. Review your expenses.")
    
    if not df[df['Amount'] < 0].empty:
        expense_by_category = df[df['Amount'] < 0].groupby('Category')['Amount'].sum().abs()
        top_expense = expense_by_category.idxmax()
        top_expense_pct = (expense_by_category.max() / total_expenses) * 100
        insights.append(f"📊 Your highest expense category is {top_expense} ({top_expense_pct:.1f}% of total expenses).")
    
    return insights

# Main App
st.title("💰 Enhanced Personal Finance Tracker")
st.markdown("Track your income and expenses with advanced analytics and insights")

# Initialize session state for date range
if 'start_date' not in st.session_state:
    st.session_state.start_date = date.today() - timedelta(days=30)
if 'end_date' not in st.session_state:
    st.session_state.end_date = date.today()

# Sidebar for adding transactions
st.sidebar.header("💳 Add New Transaction")
with st.sidebar:
    with st.form("transaction_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            transaction_type = st.selectbox("Type", ["Income", "Expense"])
        with col2:
            transaction_date = st.date_input("Date", value=date.today(), max_value=date.today())
        
        categories = INCOME_CATEGORIES if transaction_type == "Income" else EXPENSE_CATEGORIES
        category = st.selectbox("Category", categories)
        amount = st.number_input("Amount ($)", min_value=0.01, format="%.2f")
        description = st.text_input("Description", placeholder="Optional description...")
        tags = st.text_input("Tags", placeholder="work, urgent, monthly...")
        
        if st.form_submit_button("Add Transaction", type="primary", use_container_width=True):
            if amount > 0 and add_transaction(transaction_date, transaction_type, category, amount, description, tags):
                st.success(f"✅ {transaction_type} of ${amount:.2f} added!")
                st.rerun()

# Load data
df = load_data()

if df.empty:
    st.info("🚀 Welcome! Add your first transaction using the sidebar to get started.")
else:
    # Date range filter
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        start_date = st.date_input("From Date", value=st.session_state.start_date, max_value=date.today())
    with col2:
        end_date = st.date_input("To Date", value=st.session_state.end_date, max_value=date.today())
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📅 Last 30 Days", use_container_width=True):
            st.session_state.start_date = date.today() - timedelta(days=30)
            st.session_state.end_date = date.today()
            st.rerun()
    
    # Update session state
    st.session_state.start_date = start_date
    st.session_state.end_date = end_date

    # Filter data
    mask = (df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)
    filtered_df = df.loc[mask].copy()
    
    if filtered_df.empty:
        st.warning("No transactions in selected date range.")
    else:
        # Financial Dashboard
        st.header("📊 Financial Dashboard")
        total_income = filtered_df[filtered_df['Amount'] > 0]['Amount'].sum()
        total_expenses = abs(filtered_df[filtered_df['Amount'] < 0]['Amount'].sum())
        net_balance = total_income - total_expenses
        
        period_days = (end_date - start_date).days
        prev_start = start_date - timedelta(days=period_days)
        prev_end = start_date
        prev_mask = (df['Date'].dt.date >= prev_start) & (df['Date'].dt.date < prev_end)
        prev_df = df.loc[prev_mask]
        
        prev_income = prev_df[prev_df['Amount'] > 0]['Amount'].sum() if not prev_df.empty else 0
        prev_expenses = abs(prev_df[prev_df['Amount'] < 0]['Amount'].sum()) if not prev_df.empty else 0
        prev_balance = prev_income - prev_expenses
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💰 Total Income", f"${total_income:,.2f}", delta=f"${total_income - prev_income:,.2f}" if prev_income else "N/A")
        with col2:
            st.metric("💸 Total Expenses", f"${total_expenses:,.2f}", delta=f"${total_expenses - prev_expenses:,.2f}" if prev_expenses else "N/A", delta_color="inverse")
        with col3:
            st.metric("💵 Net Balance", f"${net_balance:,.2f}", delta=f"${net_balance - prev_balance:,.2f}" if prev_balance else "N/A")
        with col4:
            st.metric("💾 Savings Rate", f"{(net_balance / total_income * 100):.1f}%" if total_income > 0 else "N/A")
        
        # Financial Insights
        insights = get_financial_insights(filtered_df)
        if insights:
            st.header("💡 Financial Insights")
            for insight in insights:
                st.info(insight)
        
        # Visualizations
        st.header("📈 Analytics & Visualizations")
        tab1, tab2, tab3, tab4 = st.tabs(["💹 Cash Flow", "🥧 Category Breakdown", "📅 Monthly Trends", "🏷️ Tag Analysis"])
        
        with tab1:
            fig_cashflow = px.bar(
                filtered_df.sort_values('Date'),
                x='Date',
                y='Amount',
                color='Type',
                color_discrete_map={'Income': '#51cf66', 'Expense': '#ff6b6b'},
                title="Daily Cash Flow",
                hover_data=['Category', 'Description']
            )
            fig_cashflow.update_layout(height=500)
            st.plotly_chart(fig_cashflow, use_container_width=True)
            
            cumulative_df = filtered_df.sort_values('Date').copy()
            cumulative_df['Cumulative'] = cumulative_df['Amount'].cumsum()
            fig_cumulative = px.line(
                cumulative_df,
                x='Date',
                y='Cumulative',
                title="Cumulative Balance Over Time",
                color_discrete_sequence=['#339af0']
            )
            fig_cumulative.update_layout(height=400)
            st.plotly_chart(fig_cumulative, use_container_width=True)
        
        with tab2:
            col1, col2 = st.columns(2)
            with col1:
                income_data = filtered_df[filtered_df['Amount'] > 0]
                if not income_data.empty:
                    fig_income = px.pie(
                        income_data,
                        names='Category',
                        values='Amount',
                        title="Income by Category",
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    st.plotly_chart(fig_income, use_container_width=True)
                else:
                    st.info("No income data to display")
            
            with col2:
                expense_data = filtered_df[filtered_df['Amount'] < 0].copy()
                if not expense_data.empty:
                    expense_data['Amount'] = expense_data['Amount'].abs()
                    fig_expense = px.pie(
                        expense_data,
                        names='Category',
                        values='Amount',
                        title="Expenses by Category",
                        color_discrete_sequence=px.colors.qualitative.Set1
                    )
                    st.plotly_chart(fig_expense, use_container_width=True)
                else:
                    st.info("No expense data to display")
        
        with tab3:
            monthly_data = filtered_df.copy()
            monthly_data['Month'] = monthly_data['Date'].dt.to_period('M').astype(str)
            monthly_summary = monthly_data.groupby(['Month', 'Type'])['Amount'].sum().reset_index()
            if not monthly_summary.empty:
                fig_monthly = px.bar(
                    monthly_summary,
                    x='Month',
                    y='Amount',
                    color='Type',
                    barmode='group',
                    title="Monthly Income vs Expenses",
                    color_discrete_map={'Income': '#51cf66', 'Expense': '#ff6b6b'}
                )
                fig_monthly.update_layout(height=500)
                st.plotly_chart(fig_monthly, use_container_width=True)
            else:
                st.info("Not enough data for monthly trends")
        
        with tab4:
            if 'Tags' in filtered_df.columns and filtered_df['Tags'].notna().any():
                tag_data = []
                for _, row in filtered_df.iterrows():
                    if pd.notna(row['Tags']) and row['Tags'].strip():
                        tags = [tag.strip() for tag in row['Tags'].split(',')]
                        for tag in tags:
                            tag_data.append({
                                'Tag': tag,
                                'Amount': abs(row['Amount']),
                                'Type': row['Type']
                            })
                
                if tag_data:
                    tag_df = pd.DataFrame(tag_data)
                    tag_summary = tag_df.groupby(['Tag', 'Type'])['Amount'].sum().reset_index()
                    fig_tags = px.bar(
                        tag_summary,
                        x='Tag',
                        y='Amount',
                        color='Type',
                        barmode='group',
                        title="Spending by Tags",
                        color_discrete_map={'Income': '#51cf66', 'Expense': '#ff6b6b'}
                    )
                    fig_tags.update_layout(height=400)
                    st.plotly_chart(fig_tags, use_container_width=True)
                else:
                    st.info("No tagged transactions found")
            else:
                st.info("Tags feature not available in current data")
        
        # Transaction Management
        st.header("📋 Transaction Management")
        col1, col2, col3 = st.columns(3)
        with col1:
            search_term = st.text_input("🔍 Search transactions", placeholder="Search description, category...")
        with col2:
            type_filter = st.selectbox("Filter by Type", ["All", "Income", "Expense"])
        with col3:
            category_filter = st.selectbox("Filter by Category", ["All"] + sorted(filtered_df['Category'].unique().tolist()))
        
        display_df = filtered_df.copy()
        if search_term:
            mask = (
                display_df['Description'].str.contains(search_term, case=False, na=False) |
                display_df['Category'].str.contains(search_term, case=False, na=False)
            )
            display_df = display_df[mask]
        
        if type_filter != "All":
            display_df = display_df[display_df['Type'] == type_filter]
        
        if category_filter != "All":
            display_df = display_df[display_df['Category'] == category_filter]
        
        if not display_df.empty:
            display_df_formatted = display_df.copy()
            display_df_formatted['Amount'] = display_df_formatted['Amount'].apply(
                lambda x: f"-${abs(x):,.2f}" if x < 0 else f"${x:,.2f}"
            )
            display_df_formatted['Date'] = display_df_formatted['Date'].dt.strftime('%Y-%m-%d')
            
            column_order = ['Date', 'Type', 'Category', 'Amount', 'Description', 'Tags']
            column_order = [col for col in column_order if col in display_df_formatted.columns]
            
            st.dataframe(
                display_df_formatted[column_order].sort_values('Date', ascending=False),
                use_container_width=True,
                hide_index=True
            )
            
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Filtered Data as CSV",
                data=csv,
                file_name=f"finance_data_{start_date}_to_{end_date}.csv",
                mime="text/csv"
            )
        else:
            st.info("No transactions match your filters.")

# Footer
st.markdown("---")
st.markdown("💡 **Tip:** Use tags to better categorize your transactions and gain more insights into your spending patterns!")
