import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# ------------------- Sidebar Filters -------------------
st.sidebar.title("🔍 Company Comparison")

popular_companies = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Amazon": "AMZN",
    "Google": "GOOGL",
    "Meta": "META",
    "Tesla": "TSLA",
    "Nvidia": "NVDA",
    "Netflix": "NFLX",
    "Coca-Cola": "KO",
    "JP Morgan": "JPM"
}

company1_name = st.sidebar.selectbox("Select Company 1", list(popular_companies.keys()))
company2_name = st.sidebar.selectbox("Select Company 2", list(popular_companies.keys()), index=1)

statement_type = st.sidebar.selectbox("Select Financial Statement", ["Balance Sheet", "Income Statement", "Cash Flow"])
chart_type = st.sidebar.selectbox("Select Chart Type", ["Bar Chart", "Line Chart", "Area Chart"])

start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-02"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("2024-02-04"))

# ------------------- Main Page -------------------
st.title("🏦 Company Financial Statements Comparison")

if st.button("Compare Companies"):
    ticker1 = yf.Ticker(popular_companies[company1_name])
    ticker2 = yf.Ticker(popular_companies[company2_name])

    if statement_type == "Balance Sheet":
        df1 = ticker1.balance_sheet
        df2 = ticker2.balance_sheet
    elif statement_type == "Income Statement":
        df1 = ticker1.financials
        df2 = ticker2.financials
    else:
        df1 = ticker1.cashflow
        df2 = ticker2.cashflow

    df1 = df1.fillna(0).astype(int)
    df2 = df2.fillna(0).astype(int)

    st.subheader(f"📋 {statement_type} Snapshot")

    # Μορφοποίηση αριθμών σε dataframes (με κόμματα)
    def format_numbers_df(df):
        # Επιστρέφει νέο dataframe όπου όλοι οι αριθμοί μορφοποιούνται ως strings με κόμματα
        return df.applymap(lambda x: f"{x:,}" if isinstance(x, (int, float)) else x)

    st.write(f"### {company1_name}")
    st.dataframe(format_numbers_df(df1))

    st.write(f"### {company2_name}")
    st.dataframe(format_numbers_df(df2))

    # ---------------- KPIs & Trend Analysis ----------------
    st.subheader("📌 KPI Trend Comparison")

    kpi_data = {
        "KPI": [],
        "Year": [],
        company1_name: [],
        company2_name: [],
        "Performance": []
    }

    def extract_series(df, key):
        try:
            series = df.loc[key]
            series.index = pd.to_datetime(series.index).year
            series = series.sort_index()
            return series[(series.index >= start_date.year) & (series.index <= end_date.year)]
        except:
            return None

    trends = []

    if statement_type == "Income Statement":
        kpis = ["Total Revenue", "Net Income", "Gross Profit", "Operating Income or Loss"]
        # Ας προσθέσουμε και μερικούς ακόμα δείκτες από income statement
    elif statement_type == "Balance Sheet":
        kpis = ["Total Assets", "Total Liab", "Total Stockholder Equity", "Current Assets", "Current Liabilities"]
    else:
        kpis = ["Total Cash From Operating Activities", "Free Cash Flow", "Capital Expenditures", "Change In Cash"]

    for kpi in kpis:
        series1 = extract_series(df1, kpi)
        series2 = extract_series(df2, kpi)

        if series1 is not None and series2 is not None:
            years = sorted(list(set(series1.index).intersection(series2.index)))
            for year in years:
                val1 = int(series1.get(year, 0))
                val2 = int(series2.get(year, 0))
                kpi_data["KPI"].append(kpi)
                kpi_data["Year"].append(year)
                kpi_data[company1_name].append(val1)
                kpi_data[company2_name].append(val2)

                if val1 > val2:
                    kpi_data["Performance"].append(company1_name)
                elif val2 > val1:
                    kpi_data["Performance"].append(company2_name)
                else:
                    kpi_data["Performance"].append("Tie")

            # Trend ανάλυση για KPI
            trend1 = series1.pct_change().mean()
            trend2 = series2.pct_change().mean()

            if trend1 > trend2:
                trends.append(f"📈 **{company1_name}** has a better trend in **{kpi}** than {company2_name}.")
            elif trend1 < trend2:
                trends.append(f"📉 **{company2_name}** has a better trend in **{kpi}** than {company1_name}.")
            else:
                trends.append(f"➡️ Both have similar trends in **{kpi}**.")

    df_kpi = pd.DataFrame(kpi_data)

    # Απεικόνιση KPI πίνακα με χρώματα και format αριθμών
    def color_performance(val):
        if val == company1_name:
            return 'background-color: lightgreen'
        elif val == company2_name:
            return 'background-color: lightcoral'
        elif val == "Tie":
            return 'background-color: lightyellow'
        return ''

    def format_numbers(x):
        if isinstance(x, (int, float)):
            return f"{x:,}"
        return x

    df_kpi_style = df_kpi.style.format({
        company1_name: "{:,}",
        company2_name: "{:,}"
    }).applymap(color_performance, subset=["Performance"])

    st.dataframe(df_kpi_style)

    # ---------------- Trend Summary ----------------
    st.subheader("📊 Trend Summary")
    for line in trends:
        st.markdown(line)

    # ------------------ Charts ------------------
    st.subheader(f"📈 Chart Comparison: {statement_type}")

    if chart_type == "Bar Chart":
        fig = px.bar(df_kpi, x="Year", y=[company1_name, company2_name], color="KPI",
                     barmode="group", title=f"{statement_type} KPIs Comparison")
    elif chart_type == "Line Chart":
        fig = px.line(df_kpi, x="Year", y=[company1_name, company2_name], color="KPI",
                      title=f"{statement_type} KPIs Comparison")
    else:
        fig = px.area(df_kpi, x="Year", y=[company1_name, company2_name], color="KPI",
                      title=f"{statement_type} KPIs Comparison")

    st.plotly_chart(fig, use_container_width=True)

