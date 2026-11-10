import streamlit as st
import requests
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Financial Budget Tracker",
    page_icon="💰",
    layout="centered"
)

# URL of your backend API hosted on Render (update with your actual Render URL)
API_URL = "https://budget-tracker-api.onrender.com"

st.title("💰 Financial Budget Tracker")
st.write("Manage your categories, deposits, withdrawals, transfers, and view visual ASCII spend charts.")

st.markdown("---")

# Navigation tabs using Streamlit
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Create Category", "Deposit", "Withdraw", "Transfer", "Ledgers", "Spend Chart"
])

# Tab 1: Create Category
with tab1:
    st.header("Create a New Category")
    new_cat_name = st.text_input("Category Name", placeholder="e.g., Food, Clothing")
    if st.button("Create Category", type="primary"):
        if not new_cat_name.strip():
            st.warning("Please enter a valid category name.")
        else:
            try:
                res = requests.post(f"{API_URL}/categories", json={"name": new_cat_name})
                if res.status_code == 201:
                    st.success(f"Category '{new_cat_name}' created successfully!")
                else:
                    st.error(res.json().get("detail", "Error creating category."))
            except Exception as e:
                st.error(f"Connection error: {e}")

# Tab 2: Deposit
with tab2:
    st.header("Deposit Funds")
    dep_cat = st.text_input("Category Name", placeholder="e.g., Food", key="dep_cat")
    dep_amount = st.number_input("Amount", min_value=0.0, value=0.0, key="dep_amount")
    dep_desc = st.text_input("Description", placeholder="e.g., Initial paycheck", key="dep_desc")
    
    if st.button("Submit Deposit"):
        if not dep_cat.strip():
            st.warning("Please specify the category.")
        else:
            try:
                res = requests.post(
                    f"{API_URL}/categories/{dep_cat}/deposit",
                    json={"amount": dep_amount, "description": dep_desc}
                )
                if res.status_code == 200:
                    data = res.json()
                    st.success(f"Deposit successful! New balance: R$ {data.get('new_balance', 0):.2f}")
                else:
                    st.error(res.json().get("detail", "Error processing deposit."))
            except Exception as e:
                st.error(f"Connection error: {e}")

# Tab 3: Withdraw
with tab3:
    st.header("Withdraw Funds")
    wit_cat = st.text_input("Category Name", placeholder="e.g., Food", key="wit_cat")
    wit_amount = st.number_input("Amount", min_value=0.0, value=0.0, key="wit_amount")
    wit_desc = st.text_input("Description", placeholder="e.g., Groceries", key="wit_desc")
    
    if st.button("Submit Withdrawal"):
        if not wit_cat.strip():
            st.warning("Please specify the category.")
        else:
            try:
                res = requests.post(
                    f"{API_URL}/categories/{wit_cat}/withdraw",
                    json={"amount": wit_amount, "description": wit_desc}
                )
                if res.status_code == 200:
                    data = res.json()
                    st.success(f"Withdrawal successful! New balance: R$ {data.get('new_balance', 0):.2f}")
                else:
                    st.error(res.json().get("detail", "Insufficient funds or category not found."))
            except Exception as e:
                st.error(f"Connection error: {e}")

# Tab 4: Transfer
with tab4:
    st.header("Transfer Between Categories")
    tr_source = st.text_input("Source Category", placeholder="e.g., Food", key="tr_source")
    tr_dest = st.text_input("Destination Category", placeholder="e.g., Clothing", key="tr_dest")
    tr_amount = st.number_input("Amount", min_value=0.0, value=0.0, key="tr_amount")
    
    if st.button("Submit Transfer"):
        if not tr_source.strip() or not tr_dest.strip():
            st.warning("Please specify both source and destination categories.")
        else:
            try:
                res = requests.post(
                    f"{API_URL}/categories/{tr_source}/transfer",
                    json={"amount": tr_amount, "destination_category": tr_dest}
                )
                if res.status_code == 200:
                    st.success("Transfer successful!")
                    st.json(res.json())
                else:
                    st.error(res.json().get("detail", "Error processing transfer."))
            except Exception as e:
                st.error(f"Connection error: {e}")

# Tab 5: Ledgers Overview
with tab5:
    st.header("All Category Ledgers")
    if st.button("Refresh Ledgers"):
        try:
            res = requests.get(f"{API_URL}/categories")
            if res.status_code == 200:
                ledgers = res.json()
                if not ledgers:
                    st.info("No categories created yet.")
                else:
                    for name, ledger_str in ledgers.items():
                        st.code(ledger_str, language="text")
            else:
                st.error("Error fetching categories.")
        except Exception as e:
            st.error(f"Connection error: {e}")

# Tab 6: Spend Chart
with tab6:
    st.header("ASCII Spend Chart")
    if st.button("Generate Chart"):
        try:
            res = requests.get(f"{API_URL}/spend-chart")
            if res.status_code == 200:
                chart_data = res.json().get("spend_chart", "")
                st.code(chart_data, language="text")
            else:
                st.error(res.json().get("detail", "Error generating spend chart."))
        except Exception as e:
            st.error(f"Connection error: {e}")