# =========================
# IMPORT LIBRARIES
# =========================

import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px


# =========================
# PAGE CONFIG
# =========================

st.set_page_config(layout="wide")
st.title("Financial Monitoring Dashboard")


# =========================
# LOAD DATA (CSV)
# =========================

@st.cache_data
def load_data():
    df = pd.read_csv("data.csv")

    # Ensure datetime
    df['month_date'] = pd.to_datetime(df['month_date'])

    # Month order
    month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']

    df['month_name'] = pd.Categorical(df['month_name'], categories=month_order, ordered=True)

    return df


df = load_data()


# =========================
# FILTERS (SLICERS)
# =========================

st.sidebar.header("Filters")

year_list = sorted(df['year'].dropna().unique())
month_list = [m for m in df['month_name'].unique()]
division_list = sorted(df['division'].dropna().unique())

year = st.sidebar.selectbox("Year", ['All'] + list(year_list))
month = st.sidebar.selectbox("Month", ['All'] + list(month_list))
division = st.sidebar.selectbox("Division", ['All'] + list(division_list))


# =========================
# FILTER DATA
# =========================

filtered_df = df.copy()

if year != 'All':
    filtered_df = filtered_df[filtered_df['year'] == year]

if month != 'All':
    filtered_df = filtered_df[filtered_df['month_name'] == month]

if division != 'All':
    filtered_df = filtered_df[filtered_df['division'] == division]


# =========================
# KPI CALCULATIONS
# =========================

total_feeders = filtered_df['feeder_code'].nunique()

total_billed = filtered_df['Total_Billed_Amount'].sum()
total_collection = filtered_df['Total_Collection'].sum()
revenue_gap = filtered_df['Revenue_Gap'].sum()

billed_cr = total_billed / 1e7
collection_cr = total_collection / 1e7
gap_cr = revenue_gap / 1e7

collection_eff = (total_collection / total_billed * 100) if total_billed != 0 else 0

total_consumption = filtered_df['Total_Consumption'].sum()
lt_consumers = filtered_df['lt_consumer_count'].sum()
ht_consumers = filtered_df['ht_consumer_count'].sum()

lt_revenue = filtered_df['lt_billed_amount'].sum()
ht_revenue = filtered_df['ht_billed_amount'].sum()

lt_rev_pct = (lt_revenue / total_billed * 100) if total_billed != 0 else 0
ht_rev_pct = (ht_revenue / total_billed * 100) if total_billed != 0 else 0


# =========================
# KPI DISPLAY
# =========================

# Row 1
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total Feeders", total_feeders)
col2.metric("Total Billed (Cr)", f"{billed_cr:.2f}")
col3.metric("Total Collection (Cr)", f"{collection_cr:.2f}")
col4.metric("Revenue Gap (Cr)", f"{gap_cr:.2f}")
col5.metric("Collection %", f"{collection_eff:.2f}")

# Row 2
col6, col7, col8, col9, col10 = st.columns(5)

col6.metric("Total Consumption", f"{total_consumption:.2f}")
col7.metric("LT Consumers", int(lt_consumers))
col8.metric("HT Consumers", int(ht_consumers))
col9.metric("LT Revenue %", f"{lt_rev_pct:.2f}")
col10.metric("HT Revenue %", f"{ht_rev_pct:.2f}")


# =========================
# BAR CHART
# =========================

monthly_df = filtered_df.groupby('month_name', observed=False).agg({
    'Total_Billed_Amount': 'sum',
    'Total_Collection': 'sum'
}).reset_index()

monthly_df['Total_Billed_Amount'] /= 1e7
monthly_df['Total_Collection'] /= 1e7

plot_df = monthly_df.melt(
    id_vars='month_name',
    value_vars=['Total_Billed_Amount', 'Total_Collection'],
    var_name='Type',
    value_name='Amount'
)

fig_bar = px.bar(plot_df, x='month_name', y='Amount', color='Type',
                 barmode='group', title='Month-wise Billed vs Collection (Cr)', labels={'month_name': 'Month'})

st.plotly_chart(fig_bar, use_container_width=True)


# =========================
# LINE CHART
# =========================

monthly_df['Collection_%'] = np.where(
    monthly_df['Total_Billed_Amount'] != 0,
    (monthly_df['Total_Collection'] / monthly_df['Total_Billed_Amount']) * 100,
    0
)

fig_line = px.line(monthly_df, x='month_name', y='Collection_%',
                   markers=True, title='Collection Efficiency %',labels={'month_name': 'Month'})

st.plotly_chart(fig_line, use_container_width=True)


# =========================
# REVENUE GAP
# =========================

monthly_gap = filtered_df.groupby('month_name', observed=False).agg({
    'Revenue_Gap': 'sum'
}).reset_index()

monthly_gap['Revenue_Gap'] /= 1e7

fig_gap = px.bar(monthly_gap, x='month_name', y='Revenue_Gap',
                 title='Revenue Gap (Cr)', text='Revenue_Gap',labels={'month_name': 'Month'})

st.plotly_chart(fig_gap, use_container_width=True)


# =========================
# TOP & BOTTOM TABLES
# =========================

feeder_df = filtered_df.groupby(
    ['feeder_code', 'feeder_name', 'substation_name'],
    observed=False
).agg({'Total_Consumption': 'sum'}).reset_index()

feeder_df['Total_Consumption'] /= 1e6

top10 = feeder_df.sort_values('Total_Consumption', ascending=False).head(10)
bottom10 = feeder_df.sort_values('Total_Consumption', ascending=True).head(10)

top10 = top10.rename(columns={'Total_Consumption': 'Consumption (MU)'})
bottom10 = bottom10.rename(columns={'Total_Consumption': 'Consumption (MU)'})

col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 10 Feeders")
    st.dataframe(top10)

with col2:
    st.subheader("Bottom 10 Feeders")
    st.dataframe(bottom10)
