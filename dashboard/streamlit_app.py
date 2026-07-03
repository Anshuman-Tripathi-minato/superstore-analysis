
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
from datetime import datetime

# ============================================================================
# PAGE CONFIG & LAYOUT
# ============================================================================
st.set_page_config(
    page_title="Superstore Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Superstore Sales Analytics Dashboard")
st.markdown("---")

# ============================================================================
# LOAD DATA FROM SQLITE
# ============================================================================
@st.cache_resource
def get_db_connection():
    """Establish SQLite connection"""
    return sqlite3.connect("../data/superstore.db")

@st.cache_data
def load_data():
    """Load data from SQLite database"""
    conn = sqlite3.connect("../data/superstore.db")
    df = pd.read_sql("SELECT * FROM orders", conn)
    conn.close()

    # Convert date columns
    df["Order Date"] = pd.to_datetime(df["Order Date"])
    df["Ship Date"] = pd.to_datetime(df["Ship Date"])

    return df

df = load_data()

# ============================================================================
# SIDEBAR FILTERS
# ============================================================================
with st.sidebar:
    st.header("🔍 Filters")

    # Date range filter
    min_date = df["Order Date"].min().date()
    max_date = df["Order Date"].max().date()
    date_range = st.date_input(
        "Select Date Range:",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # Region filter
    regions = st.multiselect(
        "Select Regions:",
        options=sorted(df["Region"].unique()),
        default=sorted(df["Region"].unique())
    )

    # Category filter
    categories = st.multiselect(
        "Select Categories:",
        options=sorted(df["Category"].unique()),
        default=sorted(df["Category"].unique())
    )

    # Segment filter
    segments = st.multiselect(
        "Select Customer Segments:",
        options=sorted(df["Segment"].unique()),
        default=sorted(df["Segment"].unique())
    )

    st.markdown("---")
    st.caption(f"Data Range: {min_date} to {max_date}")
    st.caption(f"Total Records: {len(df):,}")

# ============================================================================
# APPLY FILTERS
# ============================================================================
df_filtered = df[
    (df["Order Date"].dt.date >= date_range[0]) &
    (df["Order Date"].dt.date <= date_range[1]) &
    (df["Region"].isin(regions)) &
    (df["Category"].isin(categories)) &
    (df["Segment"].isin(segments))
].copy()

# ============================================================================
# KPI METRICS (TOP)
# ============================================================================
st.subheader("📈 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_sales = df_filtered["Sales"].sum()
    st.metric(
        label="Total Sales",
        value=f"${total_sales:,.0f}",
        delta=f"{(total_sales / df['Sales'].sum() * 100):.1f}% of all time"
    )

with col2:
    total_profit = df_filtered["Profit"].sum()
    profit_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
    st.metric(
        label="Total Profit",
        value=f"${total_profit:,.0f}",
        delta=f"{profit_margin:.1f}% margin",
        delta_color="inverse" if profit_margin < 0 else "normal"
    )

with col3:
    total_orders = df_filtered["Order ID"].nunique()
    st.metric(
        label="Total Orders",
        value=f"{total_orders:,}",
        delta=f"{(total_orders / df['Order ID'].nunique() * 100):.1f}% of all time"
    )

with col4:
    avg_order_value = df_filtered["Sales"].sum() / total_orders if total_orders > 0 else 0
    st.metric(
        label="Avg Order Value",
        value=f"${avg_order_value:.2f}",
        delta=f"Based on {total_orders:,} orders"
    )

st.markdown("---")

# ============================================================================
# VISUALIZATIONS - ROW 1
# ============================================================================
st.subheader("📊 Sales Analysis")

col1, col2 = st.columns(2)

# Chart 1: Sales by Category (pie)
with col1:
    category_sales = df_filtered.groupby("Category", as_index=False).agg(
        {"Sales": "sum", "Profit": "sum"}
    ).sort_values("Sales", ascending=False)

    fig_category = px.pie(
        category_sales,
        names="Category",
        values="Sales",
        title="Sales Distribution by Category",
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    st.plotly_chart(fig_category, use_container_width=True)

# Chart 2: Profit by Category (bar)
with col2:
    fig_profit = px.bar(
        category_sales,
        x="Category",
        y="Profit",
        title="Profit by Category",
        color="Profit",
        color_continuous_scale="RdYlGn",
        text="Profit"
    )
    fig_profit.update_traces(texttemplate="$%{text:.0f}", textposition="outside")
    fig_profit.update_layout(showlegend=False)
    st.plotly_chart(fig_profit, use_container_width=True)

# ============================================================================
# VISUALIZATIONS - ROW 2
# ============================================================================
col1, col2 = st.columns(2)

# Chart 3: Monthly Sales Trend
with col1:
    monthly_data = df_filtered.copy()
    monthly_data["YearMonth"] = monthly_data["Order Date"].dt.to_period("M")
    monthly_sales = monthly_data.groupby("YearMonth", as_index=False).agg(
        {"Sales": "sum", "Profit": "sum", "Order ID": "nunique"}
    )

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=monthly_sales.index,
        y=monthly_sales["Sales"],
        mode="lines+markers",
        name="Sales",
        line=dict(color="blue", width=2)
    ))
    fig_trend.add_trace(go.Scatter(
        x=monthly_sales.index,
        y=monthly_sales["Profit"],
        mode="lines+markers",
        name="Profit",
        line=dict(color="green", width=2)
    ))
    fig_trend.update_layout(
        title="Sales & Profit Trend Over Time",
        xaxis_title="Month",
        yaxis_title="Amount ($)",
        hovermode="x unified",
        height=400
    )
    st.plotly_chart(fig_trend, use_container_width=True)

# Chart 4: Regional Performance
with col2:
    region_data = df_filtered.groupby("Region", as_index=False).agg(
        {"Sales": "sum", "Profit": "sum", "Order ID": "nunique"}
    )
    region_data["Profit Margin %"] = (
        region_data["Profit"] / region_data["Sales"] * 100
    ).round(1)

    fig_region = px.scatter(
        region_data,
        x="Sales",
        y="Profit",
        size="Order ID",
        color="Region",
        title="Regional Sales vs Profit Performance",
        labels={"Order ID": "Number of Orders"},
        hover_data={"Profit Margin %": True},
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    fig_region.add_hline(y=0, line_dash="dash", line_color="red", opacity=0.5)
    st.plotly_chart(fig_region, use_container_width=True)

# ============================================================================
# VISUALIZATIONS - ROW 3
# ============================================================================
col1, col2 = st.columns(2)

# Chart 5: Top 10 Products by Profit
with col1:
    top_products = df_filtered.groupby("Product Name", as_index=False).agg(
        {"Sales": "sum", "Profit": "sum"}
    ).nlargest(10, "Profit")

    fig_top_prod = px.bar(
        top_products,
        x="Profit",
        y="Product Name",
        orientation="h",
        title="Top 10 Products by Profit",
        color="Profit",
        color_continuous_scale="Greens",
        text="Profit"
    )
    fig_top_prod.update_traces(texttemplate="$%{text:.0f}", textposition="outside")
    fig_top_prod.update_layout(showlegend=False, yaxis_title="")
    st.plotly_chart(fig_top_prod, use_container_width=True)

# Chart 6: Customer Segment Performance
with col2:
    segment_data = df_filtered.groupby("Segment", as_index=False).agg(
        {"Sales": "sum", "Profit": "sum", "Order ID": "nunique"}
    )

    fig_segment = px.bar(
        segment_data,
        x="Segment",
        y=["Sales", "Profit"],
        title="Segment Performance (Sales vs Profit)",
        barmode="group",
        color_discrete_map={"Sales": "#1f77b4", "Profit": "#2ca02c"}
    )
    st.plotly_chart(fig_segment, use_container_width=True)

# ============================================================================
# DETAILED DATA TABLES
# ============================================================================
st.markdown("---")
st.subheader("📋 Detailed Data Tables")

tab1, tab2, tab3 = st.tabs(["Top Customers", "Sub-Category Performance", "Discount Impact"])

with tab1:
    top_cust = df_filtered.groupby(
        ["Customer ID", "Customer Name", "Segment"],
        as_index=False
    ).agg({
        "Sales": "sum",
        "Profit": "sum",
        "Order ID": "nunique"
    }).nlargest(20, "Sales")

    top_cust.columns = ["Customer ID", "Customer Name", "Segment", "Total Sales", "Total Profit", "Order Count"]
    st.dataframe(top_cust, use_container_width=True)

with tab2:
    subcat_perf = df_filtered.groupby(
        ["Category", "Sub-Category"],
        as_index=False
    ).agg({
        "Sales": "sum",
        "Profit": "sum",
        "Order ID": "nunique"
    }).sort_values("Profit", ascending=False)

    subcat_perf.columns = ["Category", "Sub-Category", "Sales", "Profit", "Order Count"]
    subcat_perf["Profit Margin %"] = (subcat_perf["Profit"] / subcat_perf["Sales"] * 100).round(1)
    st.dataframe(subcat_perf, use_container_width=True)

with tab3:
    discount_data = df_filtered.copy()
    discount_data["Discount %"] = (discount_data["Discount"] * 100).round(0).astype(int)
    disc_analysis = discount_data.groupby("Discount %", as_index=False).agg({
        "Sales": "sum",
        "Profit": "sum",
        "Order ID": "nunique"
    })
    disc_analysis.columns = ["Discount %", "Total Sales", "Total Profit", "Order Count"]
    disc_analysis["Profit Margin %"] = (disc_analysis["Total Profit"] / disc_analysis["Total Sales"] * 100).round(1)
    st.dataframe(disc_analysis.sort_values("Discount %"), use_container_width=True)

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown(
    """
    **📊 Superstore Dashboard** | Built with Streamlit & Plotly  
    Data Source: SQLite Database (superstore.db)  
    Last Updated: {today}
    """.format(today=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
)
