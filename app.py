import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, date, timedelta
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Personal Finance Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
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
    }
    .big-font {
        font-size: 24px !important;
        font-weight: bold;
    }
    .expense-card {
        background: linear-gradient(135deg, #ff6b6b, #ee5a5a);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .income-card {
        background: linear-gradient(135deg, #51cf66, #40c057);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

DATA_FILE = "finance_data.csv"

# Enhanced categories
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

def load_data():
    """Load data with enhanced error handling and data validation"""
    try:
        df = pd.read_csv(DATA_FILE, parse_dates=['Date'])
        # Ensure proper data types
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        df = df.dropna(subset=['Amount'])
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=['Date', 'Type', 'Category', 'Amount', 'Description', 'Tags'])

def save_data(df):
    """Save data with backup"""
    df.to_csv(DATA_FILE, index=False)

def add_transaction(date, ttype, category, amount, description, tags=""):
    """Add transaction with validation"""
    df = load_data()
    
    # Convert amount based on type
    final_amount = amount if ttype == "Income" else -amount
    
    new_entry = {
        "Date": pd.to_datetime(date),
        "Type": ttype,
        "Category": category,
        "Amount": final_amount,
        "Description": description,
        "Tags": tags
    }
    
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    save_data(df)
    return True

def delete_transaction(index):
    """Delete a transaction by index"""
    df = load_data()
    if 0 <= index < len(df):
        df = df.drop(df.index[index]).reset_index(drop=True)
        save_data(df)
        return True
    return False

def get_financial_insights(df):
    """Generate financial insights and recommendations"""
    if df.empty:
        return []
    
    insights = []
    
    # Calculate key metrics
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
    
    # Category analysis
    if not df[df['Amount'] < 0].empty:
        expense_by_category = df[df['Amount'] < 0].groupby('Category')['Amount'].sum().abs()
        top_expense = expense_by_category.idxmax()
        top_expense_pct = (expense_by_category.max() / total_expenses) * 100
        
        insights.append(f"📊 Your highest expense category is {top_expense} ({top_expense_pct:.1f}% of total expenses).")
    
    return insights

# Main App
st.title("💰 Enhanced Personal Finance Tracker")
st.markdown("Track your income and expenses with advanced analytics and insights")

# Sidebar for adding transactions
st.sidebar.header("💳 Add New Transaction")

with st.sidebar:
    with st.form("transaction_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            transaction_type = st.selectbox(
                "Type",
                ["Income", "Expense"],
                help="Select whether this is money coming in or going out"
            )
        
        with col2:
            transaction_date = st.date_input(
                "Date",
                value=datetime.today(),
                max_value=datetime.today()
            )
        
        # Dynamic category selection based on type
        categories = INCOME_CATEGORIES if transaction_type == "Income" else EXPENSE_CATEGORIES
        category = st.selectbox(
            "Category",
            categories,
            help="Choose the most appropriate category"
        )
        
        amount = st.number_input(
            "Amount ($)",
            min_value=0.01,
            format="%.2f",
            help="Enter the transaction amount"
        )
        
        description = st.text_input(
            "Description",
            placeholder="Optional description...",
            help="Add details about this transaction"
        )
        
        tags = st.text_input(
            "Tags",
            placeholder="work, urgent, monthly...",
            help="Add comma-separated tags for better organization"
        )
        
        submitted = st.form_submit_button(
            "Add Transaction",
            type="primary",
            use_container_width=True
        )
        
        if submitted and amount > 0:
            if add_transaction(transaction_date, transaction_type, category, amount, description, tags):
                st.success(f"✅ {transaction_type} of ${amount:.2f} added successfully!")
                st.rerun()

# Load and display data
df = load_data()

if df.empty:
    st.info("🚀 Welcome! Add your first transaction using the sidebar to get started.")
    st.markdown("""
    ### Getting Started
    1. Use the sidebar to add your income and expenses
    2. Choose appropriate categories for better tracking
    3. View your financial analytics and insights
    4. Set goals and track your progress
    """)
else:
    # Date range filter
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        start_date = st.date_input(
            "From Date",
            value=df['Date'].min().date() if not df.empty else date.today() - timedelta(days=30),
            max_value=date.today()
        )
    
    with col2:
        end_date = st.date_input(
            "To Date",
            value=date.today(),
            max_value=date.today()
        )
    
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📅 Last 30 Days", use_container_width=True):
            start_date = date.today() - timedelta(days=30)
            end_date = date.today()
            st.rerun()
    
    # Filter data by date range
    mask = (df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)
    filtered_df = df.loc[mask].copy()
    
    if filtered_df.empty:
        st.warning("No transactions found in the selected date range.")
    else:
        # Key Metrics Dashboard
        st.header("📊 Financial Dashboard")
        
        total_income = filtered_df[filtered_df['Amount'] > 0]['Amount'].sum()
        total_expenses = abs(filtered_df[filtered_df['Amount'] < 0]['Amount'].sum())
        net_balance = total_income - total_expenses
        
        # Calculate trends (compare with previous period)
        period_days = (end_date - start_date).days
        prev_start = start_date - timedelta(days=period_days)
        prev_end = start_date
        
        prev_mask = (df['Date'].dt.date >= prev_start) & (df['Date'].dt.date < prev_end)
        prev_df = df.loc[prev_mask]
        
        prev_income = prev_df[prev_df['Amount'] > 0]['Amount'].sum() if not prev_df.empty else 0
        prev_expenses = abs(prev_df[prev_df['Amount'] < 0]['Amount'].sum()) if not prev_df.empty else 0
        prev_balance = prev_income - prev_expenses
        
        # Display metrics with trends
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            income_delta = total_income - prev_income if prev_income > 0 else None
            st.metric(
                "💰 Total Income",
                f"${total_income:,.2f}",
                delta=f"${income_delta:,.2f}" if income_delta is not None else None
            )
        
        with col2:
            expense_delta = total_expenses - prev_expenses if prev_expenses > 0 else None
            st.metric(
                "💸 Total Expenses",
                f"${total_expenses:,.2f}",
                delta=f"${expense_delta:,.2f}" if expense_delta is not None else None,
                delta_color="inverse"
            )
        
        with col3:
            balance_delta = net_balance - prev_balance if prev_balance != 0 else None
            st.metric(
                "💵 Net Balance",
                f"${net_balance:,.2f}",
                delta=f"${balance_delta:,.2f}" if balance_delta is not None else None
            )
        
        with col4:
            if total_income > 0:
                savings_rate = (net_balance / total_income) * 100
                st.metric(
                    "💾 Savings Rate",
                    f"{savings_rate:.1f}%",
                    help="Percentage of income saved"
                )
            else:
                st.metric("💾 Savings Rate", "N/A")
        
        # Financial Insights
        insights = get_financial_insights(filtered_df)
        if insights:
            st.header("💡 Financial Insights")
            for insight in insights:
                st.info(insight)
        
        # Enhanced Visualizations
        st.header("📈 Analytics & Visualizations")
        
        tab1, tab2, tab3, tab4 = st.tabs(["💹 Cash Flow", "🥧 Category Breakdown", "📅 Monthly Trends", "🏷️ Tag Analysis"])
        
        with tab1:
            # Cash Flow Chart
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
            
            # Cumulative balance
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
                # Income breakdown
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
                # Expense breakdown
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
            # Monthly trends
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
            # Tag analysis
            if 'Tags' in filtered_df.columns:
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
                    tag_summary = tag_df.groupby('Tag')['Amount'].sum().sort_values(ascending=False)
                    
                    fig_tags = px.bar(
                        x=tag_summary.index,
                        y=tag_summary.values,
                        title="Spending by Tags",
                        labels={'x': 'Tags', 'y': 'Amount ($)'}
                    )
                    fig_tags.update_layout(height=400)
                    st.plotly_chart(fig_tags, use_container_width=True)
                else:
                    st.info("No tagged transactions found")
            else:
                st.info("Tags feature not available in current data")
        
        # Transaction Management
        st.header("📋 Transaction Management")
        
        # Search and filter
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_term = st.text_input("🔍 Search transactions", placeholder="Search description, category...")
        
        with col2:
            type_filter = st.selectbox("Filter by Type", ["All", "Income", "Expense"])
        
        with col3:
            category_filter = st.selectbox(
                "Filter by Category",
                ["All"] + sorted(filtered_df['Category'].unique().tolist())
            )
        
        # Apply filters
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
        
        # Display transactions table
        if not display_df.empty:
            # Format the dataframe for display
            display_df_formatted = display_df.copy()
            display_df_formatted['Amount'] = display_df_formatted['Amount'].apply(lambda x: f"${x:,.2f}")
            display_df_formatted['Date'] = display_df_formatted['Date'].dt.strftime('%Y-%m-%d')
            
            # Reorder columns
            column_order = ['Date', 'Type', 'Category', 'Amount', 'Description']
            if 'Tags' in display_df_formatted.columns:
                column_order.append('Tags')
            
            st.dataframe(
                display_df_formatted[column_order].sort_values('Date', ascending=False),
                use_container_width=True,
                hide_index=True
            )
            
            # Export functionality
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
st.markdown(
    "💡 **Tip:** Use tags to better categorize your transactions and gain more insights into your spending patterns!"
)
