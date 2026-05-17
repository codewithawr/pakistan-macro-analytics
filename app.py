import os
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from google.cloud import bigquery
from sklearn.linear_model import LinearRegression

# =====================================================================
# 1. GLOBAL WEB APP PAGE SETUP
# =====================================================================
st.set_page_config(
    page_title="Pakistan Macroeconomic Analytics Platform",
    page_icon="PK",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Global CSS to lock all KPI text styles to solid pitch-black
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    
    /* White Card containers formatting */
    .stMetric { 
        background-color: #ffffff !important; 
        padding: 18px; 
        border-radius: 8px; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); 
        border: 1px solid #eef0f2;
    }
    
    /* STYLES INTERCEPT: Force Metric Labels & Values to Deep Black text */
    div[data-testid="stMetricLabel"] > div,
    div[data-testid="stMetricLabel"] p,
    div[data-testid="stMetricValue"] > div,
    div[data-testid="stMetricValue"] p,
    div[data-testid="stMetric"] div,
    div[data-testid="stMetric"] span,
    .stMetric label {
        color: #000000 !important;
        font-weight: 700 !important;
        -webkit-text-fill-color: #000000 !important;
    }
    
    div[data-testid="stMetricLabel"] > div {
        font-weight: 500 !important;
        color: #222222 !important;
    }
    
    h1 { color: #2c3e50; font-family: 'Helvetica Neue', Arial, sans-serif; font-weight: 700; }
    h3 { color: #34495e; font-family: 'Helvetica Neue', Arial, sans-serif; border-bottom: 2px solid #eef0f2; padding-bottom: 8px; }
    h4 { color: #2c3e50; font-family: 'Helvetica Neue', Arial, sans-serif; font-weight: 600; margin-top: 15px; }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 2. DATA ENGINE CONNECTOR (CACHED CLOUD INTEGRATION)
# =====================================================================
@st.cache_data
def fetch_and_clean_data():
    # Check if running locally or in the cloud
    if "gcp_service_account" in st.secrets:
        # Secure cloud deployment path using Streamlit Secrets dashboard
        import json
        from google.oauth2 import service_account
        
        info = dict(st.secrets["gcp_service_account"])
        credentials = service_account.Credentials.from_service_account_info(info)
        client = bigquery.Client(credentials=credentials, project=info['project_id'])
    else:
        # Fallback local path for your machine
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "pakistan-macro-analytics-17991db4c9f5.json"
        client = bigquery.Client()

# Key Definitions
target_key = 'IND_INFLATION_CPI'       
policy_rate_key = 'IND_POLICY_RATE_PCT' 
gdp_key = 'IND_GDP_GROWTH_PCT'

latest_year = int(df_matrix.index.max())
latest_inflation = float(df_matrix.loc[latest_year, target_key])
latest_policy_rate = float(df_matrix.loc[latest_year, policy_rate_key])
latest_gdp = float(df_matrix.loc[latest_year, gdp_key]) if gdp_key in df_matrix.columns else 0.0

# =====================================================================
# 3. SIDEBAR NAVIGATION CONTROLLER
# =====================================================================
st.sidebar.title("Navigation Hub")
st.sidebar.markdown("Use this panel to switch between analytical dimensions.")

current_page = st.sidebar.radio(
    "Select Dashboard Domain View:",
    [
        "Page 1: Policy Simulation & Forecasting", 
        "Page 2: Macro Data Insights Explorer",
        "Page 3: Dual-Axis Comparison Desk"
    ]
)

st.sidebar.markdown("---")
st.sidebar.success("Connected to BigQuery Production Data")

# =====================================================================
# 4. VIEW RENDERING DOMAIN ROUTING
# =====================================================================

if current_page == "Page 1: Policy Simulation & Forecasting":
    st.title("Policy Simulation and Machine Learning Portal")
    st.markdown("Evaluate alternative monetary policy scenarios using a trained supervised linear model.")
    
    @st.cache_resource
    def train_forecasting_engine(df):
        ml_data = pd.DataFrame(index=df.index)
        ml_data['Current_Inflation'] = df[target_key]
        ml_data['Current_Policy_Rate'] = df[policy_rate_key]
        ml_data['Next_Year_Inflation'] = ml_data['Current_Inflation'].shift(-1)
        ml_data_clean = ml_data.dropna()
        X = ml_data_clean[['Current_Inflation', 'Current_Policy_Rate']].to_numpy()
        y = ml_data_clean['Next_Year_Inflation'].to_numpy()
        model = LinearRegression()
        model.fit(X, y)
        return model

    forecaster = train_forecasting_engine(df_matrix)
    
    st.sidebar.header("Simulation Controls")
    user_choice = st.sidebar.slider(
        "Simulate New Interest Rate Lever (%):",
        min_value=5.0, max_value=25.0, value=latest_policy_rate, step=0.25
    )
    
    user_input = np.array([[latest_inflation, user_choice]])
    predicted_inflation = forecaster.predict(user_input)[0]
    
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1: st.metric(label=f"Baseline Inflation Rate ({latest_year})", value=f"{latest_inflation:.2f}%")
    with kpi2: st.metric(label=f"Baseline Central Bank Rate ({latest_year})", value=f"{latest_policy_rate:.2f}%")
    with kpi3: st.metric(label=f"Baseline Real GDP Growth ({latest_year})", value=f"{latest_gdp:.2f}%")
    
    st.markdown("### Live Analytics & Forecasting Scenarios")
    col1, col2 = st.columns(2)
    
    with col1:
        fig1, ax1 = plt.subplots(figsize=(7, 4.2))
        sns.set_theme(style="whitegrid")
        ax1.plot(df_matrix.index, df_matrix[target_key], marker='o', linewidth=2, label='Inflation Rate (%)', color='#e74c3c')
        ax1.plot(df_matrix.index, df_matrix[policy_rate_key], marker='s', linewidth=2, label='Policy Rate (%)', color='#3498db')
        ax1.set_title("Historical Co-Movements Timeline", fontsize=11, fontweight='bold', color='#2c3e50')
        ax1.set_xlabel("Reporting Calendar Year")
        ax1.set_ylabel("Metrics (%)")
        ax1.legend(loc='upper left')
        ax1.set_xticks(df_matrix.index[::2])
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig1)

    with col2:
        fig2, ax2 = plt.subplots(figsize=(7, 4.2))
        labels = ['Current Baseline', f'Predicted Inflation ({latest_year + 1})']
        height_metrics = [latest_inflation, predicted_inflation]
        bars = ax2.bar(labels, height_metrics, color=['#95a5a6', '#9b59b6'], width=0.4)
        ax2.set_title(f"Predictive Model Response (Simulated Interest Rate: {user_choice:.2f}%)", fontsize=11, fontweight='bold', color='#2c3e50')
        ax2.set_ylabel("Inflation Outlook Response (%)")
        ax2.set_ylim(0, max(max(height_metrics) + 6, 25))
        for bar in bars:
            h = bar.get_height()
            ax2.annotate(f'{h:.2f}%', xy=(bar.get_x() + bar.get_width() / 2, h),
                         xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontweight='bold')
        plt.tight_layout()
        st.pyplot(fig2)

    st.markdown("### Production Data Warehouse Registry")
    with st.expander("Expand this tray to inspect raw tabular records connected to Google BigQuery"):
        st.dataframe(df_matrix.sort_index(ascending=False), use_container_width=True)

elif current_page == "Page 2: Macro Data Insights Explorer":
    st.title("Macroeconomic Insights Explorer")
    st.markdown("Analyze baseline timelines, historical records, and baseline distribution metrics.")
    
    st.markdown("### Historical Metrics Deep-Dive Panel")
    available_indicators = list(df_matrix.columns)
    
    selected_indicator = st.selectbox(
        "Choose an economic indicator variable to extract:",
        options=available_indicators,
        index=available_indicators.index(target_key) if target_key in available_indicators else 0
    )
    
    indicator_series = df_matrix[selected_indicator]
    avg_stat = float(indicator_series.mean())
    max_stat = float(indicator_series.max())
    max_year = int(indicator_series.idxmax())
    min_stat = float(indicator_series.min())
    min_year = int(indicator_series.idxmin())
    
    eda_col1, eda_col2, eda_col3 = st.columns(3)
    with eda_col1: st.metric(label=f"Historical Metric Average (2000-{latest_year})", value=f"{avg_stat:.2f}%")
    with eda_col2: st.metric(label=f"Historical Peak Value (Year {max_year})", value=f"{max_stat:.2f}%")
    with eda_col3: st.metric(label=f"Historical Minimum Value (Year {min_year})", value=f"{min_stat:.2f}%")
        
    st.markdown("---")
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("#### Longitudinal Timeline Profile")
        fig_timeline, ax_timeline = plt.subplots(figsize=(7, 4.5))
        sns.lineplot(data=df_matrix, x=df_matrix.index, y=selected_indicator, color='#16a085', linewidth=2.5, marker='o', ax=ax_timeline)
        ax_timeline.set_title(f"Historical Trend Pattern: {selected_indicator}", fontsize=11, fontweight='bold', color='#2c3e50')
        ax_timeline.set_xlabel("Calendar Reporting Year")
        ax_timeline.set_ylabel("Reporting Scale Units / Percentages")
        ax_timeline.set_xticks(df_matrix.index[::2])
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig_timeline)
        
    with chart_col2:
        st.markdown("#### Value Density & Distribution Variance")
        fig_dist, ax_dist = plt.subplots(figsize=(7, 4.5))
        sns.histplot(df_matrix[selected_indicator], kde=True, color='#2c3e50', bins=8, ax=ax_dist, edgecolor='white')
        ax_dist.set_title(f"Density Concentration Profile: {selected_indicator}", fontsize=11, fontweight='bold', color='#2c3e50')
        ax_dist.set_xlabel("Recorded Value Ranges")
        ax_dist.set_ylabel("Historical Occurrence Frequency")
        plt.tight_layout()
        st.pyplot(fig_dist)
        
    st.markdown("---")
    st.markdown("### Macroeconomic Correlation Matrix Heatmap")
    
    core_features = [target_key, policy_rate_key, gdp_key]
    additional_options = ['IND_EXCHANGE_RATE', 'IND_PUBLIC_DEBT_GDP_PCT', 'IND_UNEMPLOYMENT_PCT', 'IND_TRADE_BALANCE_USD_BN']
    for opt in additional_options:
        if opt in df_matrix.columns:
            core_features.append(opt)
            
    corr_matrix = df_matrix[core_features].corr()
    fig_heatmap, ax_heatmap = plt.subplots(figsize=(10, 5.5))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f", linewidths=1, ax=ax_heatmap, annot_kws={"size": 10, "weight": "bold"})
    ax_heatmap.set_title("Inter-Variable Linear Correlation Map", fontsize=12, fontweight='bold', pad=15, color='#2c3e50')
    plt.xticks(rotation=30, ha='right', fontsize=9)
    plt.yticks(fontsize=9)
    plt.tight_layout()
    st.pyplot(fig_heatmap)

elif current_page == "Page 3: Dual-Axis Comparison Desk":
    # -----------------------------------------------------------------
    # PAGE 3 LOGIC: AUTOMATED DUAL-SERIES INTERACTIVE RATIO HUB
    # -----------------------------------------------------------------
    st.title("Dual-Axis and Proportional Ratio Comparison Desk")
    st.markdown("Compare variables across decoupled graphs, analyze proportional values, and assign custom math denominators.")

    # Workspace Parameter Input Configuration Dock
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2, 2, 2])
    available_indicators = list(df_matrix.columns)
    
    with ctrl_col1:
        series_1_selection = st.selectbox("Select Series 1 (Line 1):", options=available_indicators, index=available_indicators.index(target_key))
    with ctrl_col2:
        series_2_selection = st.selectbox("Select Series 2 (Line 2):", options=available_indicators, index=available_indicators.index(policy_rate_key))
    with ctrl_col3:
        st.markdown("<p style='margin-bottom:8px; font-weight:bold; color:#2c3e50;'>Axis Configuration Options:</p>", unsafe_allow_html=True)
        use_dual_axis = st.checkbox("Enable Secondary Y-Axis Scaling", value=True)

    # Denominator Dynamic Allocation Control Panel
    st.markdown("<p style='margin-bottom:2px; font-weight:bold; color:#2c3e50;'>Ratio Calculation Setup:</p>", unsafe_allow_html=True)
    denominator_selection = st.radio(
        "Select Denominator Variable for Ratio Calculation (Numerator / Denominator):",
        options=[series_1_selection, series_2_selection],
        index=1,
        horizontal=True
    )
            
    st.markdown("---")
    
    # Process Proportional Ratio Math vectors safely
    numerator_selection = series_1_selection if denominator_selection == series_2_selection else series_2_selection
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio_series = df_matrix[numerator_selection] / df_matrix[denominator_selection]
        ratio_series = ratio_series.replace([np.inf, -np.inf], np.nan).fillna(0)

    # Statistical Summaries Calculation
    calculated_correlation = float(df_matrix[series_1_selection].corr(df_matrix[series_2_selection]))
    latest_ratio = float(ratio_series.loc[latest_year])
    avg_ratio = float(ratio_series.mean())
    
    kpi_p3_1, kpi_p3_2, kpi_p3_3 = st.columns(3)
    with kpi_p3_1:
        st.metric(label="Linear Correlation Coefficient", value=f"{calculated_correlation:.3f}")
    with kpi_p3_2:
        st.metric(label=f"Current Proportional Ratio ({latest_year}) [{numerator_selection}/{denominator_selection}]", value=f"{latest_ratio:.2f}x")
    with kpi_p3_3:
        st.metric(label="Historical Average Proportional Ratio", value=f"{avg_ratio:.2f}x")

    st.markdown("---")
    
    # Visual Graphs Grid Row 1: Time-Series Line Graphs side-by-side
    chart_row1_col1, chart_row1_col2 = st.columns(2)
    
    with chart_row1_col1:
        st.markdown("#### Longitudinal Time-Series Comparison")
        fig_comp, ax_left = plt.subplots(figsize=(7, 4.2))
        sns.set_theme(style="whitegrid")
        
        ax_s1 = ax_left
        ax_s2 = ax_left
        
        if use_dual_axis:
            ax_right = ax_left.twinx()
            ax_right.grid(False) 
            ax_s1 = ax_left    
            ax_s2 = ax_right   

        # Render Variable 1 Graph Line
        ax_s1.plot(df_matrix.index, df_matrix[series_1_selection], marker='o', linewidth=2, color='#2980b9', label=series_1_selection)
        ax_s1.set_ylabel(f"Scale: {series_1_selection}", color='#2980b9', fontweight='bold')
        ax_s1.tick_params(axis='y', labelcolor='#2980b9')
        
        # Render Variable 2 Graph Line
        ax_s2.plot(df_matrix.index, df_matrix[series_2_selection], marker='^', linewidth=2, color='#27ae60', label=series_2_selection)
        if not use_dual_axis:
            ax_left.set_ylabel("Unified Scale Matrix Values", fontweight='bold', color='#2c3e50')
        else:
            ax_right.set_ylabel(f"Scale: {series_2_selection}", color='#27ae60', fontweight='bold')
            ax_right.tick_params(axis='y', labelcolor='#27ae60')

        ax_left.set_title("Macro Trend Matrix Alignment", fontsize=11, fontweight='bold', color='#2c3e50')
        ax_left.set_xlabel("Calendar Reporting Year")
        ax_left.set_xticks(df_matrix.index[::2])
        plt.xticks(rotation=45)
        
        lines_1, labels_1 = ax_s1.get_legend_handles_labels()
        if use_dual_axis:
            lines_2, labels_2 = ax_s2.get_legend_handles_labels()
            ax_left.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')
        else:
            ax_left.legend(loc='upper left')
            
        plt.tight_layout()
        st.pyplot(fig_comp)
        
    with chart_row1_col2:
        st.markdown("#### Proportional Ratio Timeline")
        fig_ratio, ax_rat = plt.subplots(figsize=(7, 4.2))
        ax_rat.plot(df_matrix.index, ratio_series, marker='p', linewidth=2, color='#e67e22', label="Proportional Multiplier Factor")
        
        ax_rat.set_title(f"Proportional Ratio Timeline ({numerator_selection} / {denominator_selection})", fontsize=11, fontweight='bold', color='#2c3e50')
        ax_rat.set_xlabel("Calendar Reporting Year")
        ax_rat.set_ylabel("Ratio Multiplier Amplitude (x)")
        ax_rat.set_xticks(df_matrix.index[::2])
        plt.xticks(rotation=45)
        ax_rat.legend(loc='upper left')
        plt.tight_layout()
        st.pyplot(fig_ratio)
        
    st.markdown("---")
    
    # Visual Graphs Row 2: Behavioral Dependency Mapping Scatter Diagram
    st.markdown("#### Behavioral Dependency Mapping (Regression Analysis)")
    fig_scatter, ax_scat = plt.subplots(figsize=(10, 4))
    sns.regplot(data=df_matrix, x=series_1_selection, y=series_2_selection, color='#9b59b6', marker='p', 
                scatter_kws={'s':40, 'alpha':0.8, 'edgecolor':'white'}, line_kws={'color':'#e67e22', 'lw':2}, ax=ax_scat)
    
    ax_scat.set_title("Cross-Variable Scatter Mapping Profile", fontsize=11, fontweight='bold', color='#2c3e50')
    ax_scat.set_xlabel(f"Independent Variable Scale (X): {series_1_selection}")
    ax_scat.set_ylabel(f"Dependent Variable Scale (Y): {series_2_selection}")
    
    plt.tight_layout()
    st.pyplot(fig_scatter)
