"""TrainOps Intelligence — Training Analytics, Reporting & AI Insights.

Main Streamlit Application for Enterprise Training Operations Analytics,
Data Quality Governance, Power BI / Excel Automation, and Groq GenAI Reporting.
"""

from datetime import datetime, timedelta
import io
import json
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd

from src.ai_insights import generate_management_insights, prepare_llm_payload
from src.analytics import (
    compute_kpis,
    get_course_kpis,
    get_department_kpis,
    get_monthly_completion_trends,
)
from src.config import (
    CANONICAL_DEPARTMENTS,
    DATA_EXPORT_DIR,
    DEFAULT_AS_OF_DATE,
    DELIVERY_MODES,
    GROQ_API_KEY,
    GROQ_MODEL,
    REGIONS,
)
from src.data_generator import generate_clean_dataset, generate_flawed_raw_dataset
from src.database import (
    get_clean_records_df,
    get_flagged_records_df,
    get_raw_records_df,
    get_report_history_df,
    get_validation_runs_df,
    init_db,
    log_validation_run,
    reset_and_seed_db,
    save_clean_records,
    save_flagged_records,
    save_raw_records,
)
from src.excel_export import generate_excel_workbook
from src.power_bi_export import export_power_bi_datasets
from src.reporting import generate_full_report_workflow
from src.utils import (
    ACCENT_BLUE,
    CARD_BG,
    DARK_NAVY,
    ENTERPRISE_PALETTE,
    NAVY,
    TEXT_SECONDARY,
    create_kpi_card_html,
    format_chart_layout,
    get_custom_css,
)
from src.validation import validate_training_dataset

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="TrainOps Intelligence — Training Analytics & AI Reporting",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject Enterprise CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)


# Session State Initialization
def ensure_database_initialized():
    """Ensure database exists and contains initial seed dataset if empty."""
    init_db()
    clean_df = get_clean_records_df()
    if clean_df.empty:
        with st.spinner("Initializing TrainOps SQLite database and seeding synthetic data..."):
            clean_seed = generate_clean_dataset(num_records=1250, seed=42)
            raw_seed = generate_flawed_raw_dataset(clean_seed, seed=42)
            # Run initial validation pipeline
            validated_df, flagged_df, summary = validate_training_dataset(raw_seed)
            reset_and_seed_db(validated_df, raw_seed)
            save_flagged_records(flagged_df.to_dict(orient="records"))
            log_validation_run(summary)


ensure_database_initialized()

# Load data into session state
if "df_clean" not in st.session_state or st.session_state.df_clean is None:
    st.session_state.df_clean = get_clean_records_df()
if "df_flagged" not in st.session_state or st.session_state.df_flagged is None:
    st.session_state.df_flagged = get_flagged_records_df()
if "df_raw" not in st.session_state or st.session_state.df_raw is None:
    st.session_state.df_raw = get_raw_records_df()

# Sidebar Header & Brand
with st.sidebar:
    st.markdown(
        f"""
        <div style="padding: 4px 0 16px 0;">
            <div style="font-size: 1.25rem; font-weight: 700; color: {DARK_NAVY};">TrainOps Intelligence</div>
            <div style="font-size: 0.8rem; color: {TEXT_SECONDARY};">Training Analytics, Reporting & AI Insights</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Navigation Menu
    nav_selection = st.radio(
        "Navigation",
        options=[
            "Overview Dashboard",
            "Training Records",
            "Data Quality & Validation",
            "Reports & Exports",
            "AI Insights",
            "Data Dictionary & Methodology",
        ],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown(
        f"<div style='font-size: 0.85rem; font-weight: 600; color: {DARK_NAVY}; margin-bottom: 8px;'>OPERATIONAL FILTERS</div>",
        unsafe_allow_html=True,
    )

    # As-of Date filter
    default_as_of = datetime.strptime(DEFAULT_AS_OF_DATE, "%Y-%m-%d").date()
    as_of_input = st.date_input(
        "As-of Reference Date",
        value=default_as_of,
        help="Benchmark date for calculating overdue assignments.",
    )
    as_of_str = as_of_input.strftime("%Y-%m-%d")

    # Date Range Filter
    df_current = st.session_state.df_clean
    if not df_current.empty and "assigned_date" in df_current.columns:
        min_date = datetime.strptime(df_current["assigned_date"].min(), "%Y-%m-%d").date()
        max_date = datetime.strptime(df_current["assigned_date"].max(), "%Y-%m-%d").date()
    else:
        min_date = datetime(2026, 1, 1).date()
        max_date = datetime(2026, 12, 31).date()

    date_range = st.date_input(
        "Assigned Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    start_date_filter = date_range[0].strftime("%Y-%m-%d") if isinstance(date_range, (list, tuple)) and len(date_range) > 0 else min_date.strftime("%Y-%m-%d")
    end_date_filter = date_range[1].strftime("%Y-%m-%d") if isinstance(date_range, (list, tuple)) and len(date_range) > 1 else max_date.strftime("%Y-%m-%d")

    # Department Filter
    dept_options = sorted(list(df_current["department"].dropna().unique())) if not df_current.empty else CANONICAL_DEPARTMENTS
    selected_depts = st.multiselect(
        "Department",
        options=dept_options,
        default=dept_options,
    )

    # Training Category Filter
    cat_options = sorted(list(df_current["training_category"].dropna().unique())) if not df_current.empty else []
    selected_cats = st.multiselect(
        "Training Category",
        options=cat_options,
        default=cat_options,
    )

    # Mandatory Status Filter
    mand_selection = st.radio(
        "Mandatory vs Optional",
        options=["All Training", "Mandatory Only", "Optional Only"],
        index=0,
    )

    # Delivery Mode Filter
    delivery_options = sorted(list(df_current["delivery_mode"].dropna().unique())) if not df_current.empty else DELIVERY_MODES
    selected_modes = st.multiselect(
        "Delivery Mode",
        options=delivery_options,
        default=delivery_options,
    )

    # Region Filter
    region_options = sorted(list(df_current["region"].dropna().unique())) if not df_current.empty else REGIONS
    selected_regions = st.multiselect(
        "Region",
        options=region_options,
        default=region_options,
    )

    st.markdown("---")

    # Data Freshness & Status Indicator
    clean_count = len(st.session_state.df_clean) if st.session_state.df_clean is not None else 0
    flagged_count = len(st.session_state.df_flagged) if st.session_state.df_flagged is not None else 0

    st.markdown(
        f"""
        <div style="font-size: 0.75rem; color: {TEXT_SECONDARY}; line-height: 1.4;">
            <b>Database:</b> Local SQLite (Active)<br>
            <b>Valid Records:</b> {clean_count:,}<br>
            <b>Flagged Quarantined:</b> {flagged_count:,}<br>
            <b>Freshness:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")
    with st.expander("Database Administration"):
        st.write("Reset SQLite database with deterministic synthetic seed (1,250 clean records + controlled raw anomalies).")
        if st.button("Confirm Reset Database", type="secondary"):
            with st.spinner("Resetting database..."):
                clean_seed = generate_clean_dataset(num_records=1250, seed=42)
                raw_seed = generate_flawed_raw_dataset(clean_seed, seed=42)
                val_df, flg_df, smm = validate_training_dataset(raw_seed)
                reset_and_seed_db(val_df, raw_seed)
                save_flagged_records(flg_df.to_dict(orient="records"))
                log_validation_run(smm)
                st.session_state.df_clean = get_clean_records_df()
                st.session_state.df_flagged = get_flagged_records_df()
                st.session_state.df_raw = get_raw_records_df()
            st.success("Database successfully reset and reseeded!")
            st.rerun()


# Filter the clean DataFrame based on user selections
def apply_active_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all sidebar filter criteria to the active DataFrame."""
    if df.empty:
        return df

    filtered = df.copy()

    # Date filter
    filtered = filtered[
        (filtered["assigned_date"] >= start_date_filter) &
        (filtered["assigned_date"] <= end_date_filter)
    ]

    # Department filter
    if selected_depts:
        filtered = filtered[filtered["department"].isin(selected_depts)]

    # Category filter
    if selected_cats:
        filtered = filtered[filtered["training_category"].isin(selected_cats)]

    # Mandatory filter
    if mand_selection == "Mandatory Only":
        filtered = filtered[filtered["mandatory_training"] == True]
    elif mand_selection == "Optional Only":
        filtered = filtered[filtered["mandatory_training"] == False]

    # Delivery mode
    if selected_modes:
        filtered = filtered[filtered["delivery_mode"].isin(selected_modes)]

    # Region
    if selected_regions:
        filtered = filtered[filtered["region"].isin(selected_regions)]

    return filtered


filtered_df = apply_active_filters(st.session_state.df_clean)
active_kpis = compute_kpis(filtered_df, as_of_date=as_of_str)
dept_kpi_df = get_department_kpis(filtered_df, as_of_date=as_of_str)
course_kpi_df = get_course_kpis(filtered_df, as_of_date=as_of_str)
monthly_trend_df = get_monthly_completion_trends(filtered_df)

# ==============================================================================
# SECTION 1: OVERVIEW DASHBOARD
# ==============================================================================
if nav_selection == "Overview Dashboard":
    st.markdown(
        f"""
        <div style="margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 1.85rem; color: {DARK_NAVY};">Training Operations Analytics</h1>
            <p style="margin: 4px 0 0 0; color: {TEXT_SECONDARY}; font-size: 0.95rem;">
                Executive performance monitoring, completion health, compliance tracking, and overdue assignment visibility.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Active Filter Banner
    st.markdown(
        f"""
        <div class="callout-info">
            <b>Active Reporting Context:</b> Assigned <b>{start_date_filter}</b> to <b>{end_date_filter}</b>  |  
            As-of Reference Date: <b>{as_of_str}</b>  |  
            Filtered Scope: <b>{active_kpis['total_assignments']:,}</b> assignments across <b>{len(selected_depts)}</b> departments.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Row 1: KPI Cards (4 cards)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            create_kpi_card_html(
                title="Total Assignments",
                value=f"{active_kpis['total_assignments']:,}",
                subtitle=f"{active_kpis['unique_employees']:,} unique learners",
                badge_type="neutral",
            ),
            unsafe_allow_html=True,
        )
    with c2:
        comp_rate_num = active_kpis["completion_rate_pct"]
        badge_style = "good" if comp_rate_num >= 80.0 else "alert"
        st.markdown(
            create_kpi_card_html(
                title="Completion Rate",
                value=active_kpis["completion_rate_formatted"],
                subtitle=f"{active_kpis['completed_assignments']:,} completed / target 80%",
                badge_type=badge_style,
            ),
            unsafe_allow_html=True,
        )
    with c3:
        mand_rate_num = active_kpis["mandatory_completion_rate_pct"]
        m_badge = "good" if mand_rate_num >= 90.0 else "alert"
        st.markdown(
            create_kpi_card_html(
                title="Mandatory Compliance",
                value=active_kpis["mandatory_completion_rate_formatted"],
                subtitle=f"{active_kpis['mandatory_completed']:,} of {active_kpis['mandatory_assignments']:,} required",
                badge_type=m_badge,
            ),
            unsafe_allow_html=True,
        )
    with c4:
        overdue_cnt = active_kpis["overdue_assignments"]
        o_badge = "alert" if overdue_cnt > 0 else "good"
        st.markdown(
            create_kpi_card_html(
                title="Overdue Assignments",
                value=f"{overdue_cnt:,}",
                subtitle=f"{active_kpis['overdue_rate_formatted']} of total enrollments",
                badge_type=o_badge,
            ),
            unsafe_allow_html=True,
        )

    st.write("")

    # Row 2: KPI Cards (4 cards)
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        st.markdown(
            create_kpi_card_html(
                title="Attendance Rate",
                value=active_kpis["attendance_rate_formatted"],
                subtitle=f"{active_kpis['attended_count']:,} attended of {active_kpis['attendance_eligible_count']:,} tracked",
                badge_type="neutral",
            ),
            unsafe_allow_html=True,
        )
    with c6:
        st.markdown(
            create_kpi_card_html(
                title="Average Assessment Score",
                value=f"{active_kpis['avg_assessment_score_formatted']}",
                subtitle=f"Across {active_kpis['scored_assignments_count']:,} graded tests",
                badge_type="good" if (active_kpis["avg_assessment_score"] or 0) >= 80.0 else "neutral",
            ),
            unsafe_allow_html=True,
        )
    with c7:
        st.markdown(
            create_kpi_card_html(
                title="Training Hours Delivered",
                value=f"{active_kpis['total_completed_hours']:,.1f} hrs",
                subtitle=f"{active_kpis['total_assigned_hours']:,.1f} hrs total assigned",
                badge_type="neutral",
            ),
            unsafe_allow_html=True,
        )
    with c8:
        st.markdown(
            create_kpi_card_html(
                title="In Progress / Not Started",
                value=f"{active_kpis['in_progress_count'] + active_kpis['not_started_count']:,}",
                subtitle=f"{active_kpis['in_progress_count']:,} active, {active_kpis['not_started_count']:,} unstarted",
                badge_type="neutral",
            ),
            unsafe_allow_html=True,
        )

    st.write("")
    st.markdown("---")

    # Interactive Visualizations
    st.subheader("Operational Analytics & Performance Visualizations")

    # Chart Row 1: Monthly Trends & Department Completion
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        if not monthly_trend_df.empty:
            fig_trend = px.line(
                monthly_trend_df,
                x="completion_month",
                y="completions",
                markers=True,
                title="Monthly Training Completion Volume",
                labels={"completion_month": "Completion Month", "completions": "Completions"},
                color_discrete_sequence=[NAVY],
            )
            fig_trend.add_bar(
                x=monthly_trend_df["completion_month"],
                y=monthly_trend_df["total_hours"],
                name="Training Hours Delivered",
                marker_color="#CBD5E1",
                opacity=0.6,
            )
            st.plotly_chart(format_chart_layout(fig_trend, "Monthly Completions & Hours Trend"), use_container_width=True)
        else:
            st.info("No completed training records within the filtered date range.")

    with chart_col2:
        if not dept_kpi_df.empty:
            fig_dept = px.bar(
                dept_kpi_df.sort_values("completion_rate_pct", ascending=True),
                x="completion_rate_pct",
                y="department",
                orientation="h",
                title="Completion Rate by Department (%)",
                labels={"completion_rate_pct": "Completion Rate (%)", "department": "Department"},
                color="completion_rate_pct",
                color_continuous_scale=[[0, "#93C5FD"], [1, NAVY]],
            )
            fig_dept.add_vline(x=80.0, line_dash="dash", line_color="#DC2626", annotation_text="80% Target")
            st.plotly_chart(format_chart_layout(fig_dept, "Department Completion Rate vs Target"), use_container_width=True)
        else:
            st.info("No department data available.")

    # Chart Row 2: Attendance by Category & Mandatory vs Optional
    chart_col3, chart_col4 = st.columns(2)

    with chart_col3:
        if not filtered_df.empty:
            cat_attend = (
                filtered_df.groupby("training_category")
                .agg(
                    total=("record_id", "count"),
                    attended=("attendance_status", lambda s: (s == "Attended").sum()),
                )
                .reset_index()
            )
            cat_attend["attendance_pct"] = (cat_attend["attended"] / cat_attend["total"] * 100).round(1)

            fig_cat = px.bar(
                cat_attend.sort_values("attendance_pct", ascending=False),
                x="training_category",
                y="attendance_pct",
                title="Attendance Rate by Training Category (%)",
                labels={"attendance_pct": "Attendance Rate (%)", "training_category": "Category"},
                color_discrete_sequence=[ACCENT_BLUE],
            )
            st.plotly_chart(format_chart_layout(fig_cat, "Attendance Rate by Curriculum Category"), use_container_width=True)
        else:
            st.info("No data available for attendance analysis.")

    with chart_col4:
        if not dept_kpi_df.empty:
            fig_mand = go.Figure()
            fig_mand.add_trace(
                go.Bar(
                    x=dept_kpi_df["department"],
                    y=dept_kpi_df["mandatory_completion_rate_pct"],
                    name="Mandatory %",
                    marker_color=NAVY,
                )
            )
            fig_mand.add_trace(
                go.Bar(
                    x=dept_kpi_df["department"],
                    y=dept_kpi_df["completion_rate_pct"],
                    name="Overall %",
                    marker_color="#60A5FA",
                )
            )
            fig_mand.update_layout(barmode="group")
            st.plotly_chart(format_chart_layout(fig_mand, "Mandatory vs Overall Completion by Department"), use_container_width=True)

    # Chart Row 3: Overdue by Department & Assessment Scores
    chart_col5, chart_col6 = st.columns(2)

    with chart_col5:
        if not dept_kpi_df.empty:
            fig_overdue = px.bar(
                dept_kpi_df.sort_values("overdue_assignments", ascending=False),
                x="department",
                y="overdue_assignments",
                title="Overdue Training Assignments by Department",
                labels={"overdue_assignments": "Overdue Count", "department": "Department"},
                color="overdue_assignments",
                color_continuous_scale=[[0, "#FCD34D"], [1, "#DC2626"]],
            )
            st.plotly_chart(format_chart_layout(fig_overdue, "Overdue Assignment Volume by Department"), use_container_width=True)

    with chart_col6:
        if not filtered_df.empty and filtered_df["assessment_score"].notna().sum() > 0:
            fig_box = px.box(
                filtered_df[filtered_df["assessment_score"].notna()],
                x="department",
                y="assessment_score",
                title="Assessment Score Distribution by Department",
                labels={"assessment_score": "Score (0-100)", "department": "Department"},
                color_discrete_sequence=[ACCENT_BLUE],
            )
            st.plotly_chart(format_chart_layout(fig_box, "Learner Assessment Score Spread by Department"), use_container_width=True)

    # Chart Row 4: Training Hours by Course & Status Distribution
    chart_col7, chart_col8 = st.columns(2)

    with chart_col7:
        if not course_kpi_df.empty:
            top_courses = course_kpi_df.sort_values("total_hours_delivered", ascending=True).tail(8)
            fig_hours = px.bar(
                top_courses,
                x="total_hours_delivered",
                y="course_name",
                orientation="h",
                title="Total Training Hours Delivered by Course",
                labels={"total_hours_delivered": "Total Hours Delivered", "course_name": "Course"},
                color_discrete_sequence=[NAVY],
            )
            st.plotly_chart(format_chart_layout(fig_hours, "Curriculum Hours Delivered (Top Courses)"), use_container_width=True)

    with chart_col8:
        if not filtered_df.empty:
            status_counts = filtered_df["completion_status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            fig_pie = px.pie(
                status_counts,
                names="Status",
                values="Count",
                title="Assignment Completion Status Breakdown",
                color="Status",
                color_discrete_map={
                    "Completed": NAVY,
                    "In Progress": "#3B82F6",
                    "Not Started": "#94A3B8",
                },
                hole=0.45,
            )
            st.plotly_chart(format_chart_layout(fig_pie, "Completion Status Distribution"), use_container_width=True)


# ==============================================================================
# SECTION 2: TRAINING RECORDS
# ==============================================================================
elif nav_selection == "Training Records":
    st.markdown(
        f"""
        <div style="margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 1.85rem; color: {DARK_NAVY};">Training Records Management</h1>
            <p style="margin: 4px 0 0 0; color: {TEXT_SECONDARY}; font-size: 0.95rem;">
                Searchable, filterable employee training registry with detailed inspection and dataset import.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_explore, tab_import = st.tabs(["Browse Records", "Import Training Dataset"])

    with tab_explore:
        s_col1, s_col2, s_col3 = st.columns([2, 1, 1])
        with s_col1:
            search_query = st.text_input("Search by Employee Name, ID, or Course Title", value="")
        with s_col2:
            status_filter = st.selectbox("Status Filter", options=["All Statuses", "Completed", "In Progress", "Not Started"])
        with s_col3:
            overdue_only = st.checkbox("Show Overdue Only", value=False)

        # Apply specific search filters
        display_df = filtered_df.copy()
        if search_query.strip():
            sq = search_query.strip().lower()
            display_df = display_df[
                display_df["employee_name"].str.lower().str.contains(sq, na=False) |
                display_df["employee_id"].str.lower().str.contains(sq, na=False) |
                display_df["course_name"].str.lower().str.contains(sq, na=False) |
                display_df["record_id"].str.lower().str.contains(sq, na=False)
            ]

        if status_filter != "All Statuses":
            display_df = display_df[display_df["completion_status"] == status_filter]

        if overdue_only:
            display_df = display_df[
                (display_df["completion_status"] != "Completed") &
                (display_df["due_date"] < as_of_str)
            ]

        st.caption(f"Showing **{len(display_df):,}** matching training records.")

        # Display interactive dataframe
        st.dataframe(
            display_df[[
                "record_id", "employee_id", "employee_name", "department",
                "course_name", "training_category", "mandatory_training",
                "assigned_date", "due_date", "completion_date",
                "completion_status", "assessment_score", "training_hours"
            ]],
            use_container_width=True,
            height=450,
        )

        # Export Buttons
        btn_c1, btn_c2, _ = st.columns([1, 1, 3])
        with btn_c1:
            csv_data = display_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download Filtered CSV",
                data=csv_data,
                file_name=f"trainops_records_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
        with btn_c2:
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                display_df.to_excel(writer, index=False, sheet_name="Records")
            st.download_button(
                label="Download Filtered Excel",
                data=excel_buffer.getvalue(),
                file_name=f"trainops_records_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        # Detailed Record Inspector
        st.markdown("---")
        st.subheader("Individual Record Inspection")
        if not display_df.empty:
            record_options = display_df["record_id"].tolist()[:100]
            selected_rec_id = st.selectbox("Select Record ID to Inspect Details:", options=record_options)
            rec_row = display_df[display_df["record_id"] == selected_rec_id].iloc[0]

            col_r1, col_r2, col_r3 = st.columns(3)
            with col_r1:
                st.write(f"**Employee:** {rec_row['employee_name']} ({rec_row['employee_id']})")
                st.write(f"**Department:** {rec_row['department']}")
                st.write(f"**Job Level:** {rec_row.get('job_level', 'N/A')}")
                st.write(f"**Region:** {rec_row.get('region', 'N/A')}")
            with col_r2:
                st.write(f"**Course:** {rec_row['course_name']} ({rec_row['course_id']})")
                st.write(f"**Category:** {rec_row['training_category']}")
                st.write(f"**Mandatory:** {'Yes' if rec_row['mandatory_training'] else 'No'}")
                st.write(f"**Credit Hours:** {rec_row['training_hours']} hrs")
            with col_r3:
                st.write(f"**Assigned Date:** {rec_row['assigned_date']}")
                st.write(f"**Due Date:** {rec_row['due_date']}")
                st.write(f"**Completion Date:** {rec_row['completion_date'] or 'Pending'}")
                st.write(f"**Status:** {rec_row['completion_status']}")
                st.write(f"**Assessment Score:** {rec_row['assessment_score'] if pd.notna(rec_row['assessment_score']) else 'N/A'}")

    with tab_import:
        st.subheader("Import External Training Records")
        st.markdown(
            """
            Upload a CSV or Excel (`.xlsx`) training record file. The ingestion engine will:
            1. Validate column schema against enterprise standards.
            2. Run duplicate and date logic checks.
            3. Preview valid and flagged records before appending to the database.
            """
        )

        uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx"])
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    raw_uploaded = pd.read_csv(uploaded_file)
                else:
                    raw_uploaded = pd.read_excel(uploaded_file)

                st.write(f"Uploaded file contains **{len(raw_uploaded):,}** rows.")
                st.dataframe(raw_uploaded.head(5), use_container_width=True)

                if st.button("Validate and Process Uploaded File", type="primary"):
                    with st.spinner("Executing validation pipeline on uploaded dataset..."):
                        val_up_df, flg_up_df, sum_up = validate_training_dataset(raw_uploaded)

                        st.markdown(
                            f"""
                            <div class="callout-info">
                                <b>Ingestion Audit Results:</b><br>
                                - <b>{sum_up['valid_records']:,}</b> valid records ready for import.<br>
                                - <b>{sum_up['flagged_records']:,}</b> flagged records quarantined for review.<br>
                                - <b>{sum_up['duplicates']:,}</b> duplicates identified.<br>
                                - <b>{sum_up['date_errors']:,}</b> date anomalies identified.
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        if not val_up_df.empty:
                            # Non-destructive append
                            existing_clean = get_clean_records_df()
                            combined_clean = pd.concat([existing_clean, val_up_df], ignore_index=True).drop_duplicates(subset=["record_id"])
                            save_clean_records(combined_clean)
                            st.session_state.df_clean = get_clean_records_df()
                            st.success(f"Successfully integrated {len(val_up_df):,} validated records into SQLite!")
                        else:
                            st.warning("No records passed the critical validation gate.")

            except Exception as e:
                st.error(f"Error processing uploaded file: {str(e)}")


# ==============================================================================
# SECTION 3: DATA QUALITY & VALIDATION
# ==============================================================================
elif nav_selection == "Data Quality & Validation":
    st.markdown(
        f"""
        <div style="margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 1.85rem; color: {DARK_NAVY};">Data Quality Governance & Audit Engine</h1>
            <p style="margin: 4px 0 0 0; color: {TEXT_SECONDARY}; font-size: 0.95rem;">
                Pipeline validation metrics, anomaly quarantine logs, and automated schema standardization traceability.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_flagged = st.session_state.df_flagged
    val_runs_df = get_validation_runs_df()

    # Most recent run summary
    dq_total = len(st.session_state.df_raw) if st.session_state.df_raw is not None else 0
    dq_valid = len(st.session_state.df_clean) if st.session_state.df_clean is not None else 0
    dq_flagged = len(df_flagged) if df_flagged is not None else 0

    q1, q2, q3, q4 = st.columns(4)
    with q1:
        st.markdown(
            create_kpi_card_html("Total Ingested", f"{dq_total:,}", "Raw records received", "neutral"),
            unsafe_allow_html=True,
        )
    with q2:
        st.markdown(
            create_kpi_card_html("Clean Validated", f"{dq_valid:,}", "Active in KPI calculations", "good"),
            unsafe_allow_html=True,
        )
    with q3:
        st.markdown(
            create_kpi_card_html("Flagged Quarantined", f"{dq_flagged:,}", "Held for human review", "alert" if dq_flagged > 0 else "good"),
            unsafe_allow_html=True,
        )
    with q4:
        clean_health_pct = round(dq_valid / dq_total * 100.0, 1) if dq_total > 0 else 100.0
        st.markdown(
            create_kpi_card_html("Data Health Score", f"{clean_health_pct}%", "Passing rate through gates", "good" if clean_health_pct >= 90.0 else "alert"),
            unsafe_allow_html=True,
        )

    st.write("")
    st.markdown("---")

    # Issue breakdown
    if not df_flagged.empty:
        col_iss1, col_iss2 = st.columns([1, 2])
        with col_iss1:
            st.subheader("Issues by Category")
            issue_counts = df_flagged["issue_type"].value_counts().reset_index()
            issue_counts.columns = ["Issue Category", "Count"]

            fig_issue = px.bar(
                issue_counts,
                x="Count",
                y="Issue Category",
                orientation="h",
                color_discrete_sequence=[NAVY],
            )
            st.plotly_chart(format_chart_layout(fig_issue, "Detected Data Quality Exceptions", height=320), use_container_width=True)

        with col_iss2:
            st.subheader("Quarantined Records Log")
            st.caption("These records violated business rules and were safely excluded from KPI calculations without data loss.")

            filter_issue = st.selectbox(
                "Filter by Issue Type",
                options=["All Issues"] + list(df_flagged["issue_type"].unique()),
            )
            inspect_flagged = df_flagged.copy()
            if filter_issue != "All Issues":
                inspect_flagged = inspect_flagged[inspect_flagged["issue_type"] == filter_issue]

            st.dataframe(
                inspect_flagged[[
                    "record_id", "employee_id", "course_id",
                    "issue_type", "issue_severity", "issue_description"
                ]],
                use_container_width=True,
                height=320,
            )

        # Download Validation Audit Report
        st.write("")
        csv_dq = df_flagged.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Complete Validation Audit Log (CSV)",
            data=csv_dq,
            file_name=f"trainops_validation_audit_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
    else:
        st.success("No flagged records found. All training assignments pass validation.")

    # Historical Validation Runs
    if not val_runs_df.empty:
        st.markdown("---")
        st.subheader("Validation Execution History (Audit Log)")
        st.dataframe(
            val_runs_df[[
                "run_id", "run_timestamp", "total_records_processed",
                "valid_records_count", "flagged_records_count",
                "duplicate_records_count", "date_errors_count"
            ]],
            use_container_width=True,
        )


# ==============================================================================
# SECTION 4: REPORTS & EXPORTS
# ==============================================================================
elif nav_selection == "Reports & Exports":
    st.markdown(
        f"""
        <div style="margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 1.85rem; color: {DARK_NAVY};">Executive Reporting & BI Exports</h1>
            <p style="margin: 4px 0 0 0; color: {TEXT_SECONDARY}; font-size: 0.95rem;">
                One-click automated report generation, formatted Excel workbooks, and Power BI-ready CSV data packages.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_gen, tab_pbi, tab_hist = st.tabs(["Generate Management Report", "Power BI Data Export", "Report History"])

    with tab_gen:
        st.subheader("Automated Operational Report Generation")
        st.write(
            "Synthesizes the verified KPI calculations for the currently filtered view, generates a 6-worksheet "
            "formatted Excel workbook, and compiles an executive Markdown briefing."
        )

        rep_col1, rep_col2 = st.columns([2, 1])
        with rep_col1:
            st.info(
                f"**Report Scope:** {active_kpis['total_assignments']:,} assignments | "
                f"Period: {start_date_filter} to {end_date_filter} | As-of: {as_of_str}"
            )

        if st.button("Generate Management Report", type="primary"):
            with st.spinner("Generating deterministic KPIs, executive insights, and multi-sheet workbook..."):
                dq_summary_dict = {
                    "total_records": len(st.session_state.df_raw) if st.session_state.df_raw is not None else 0,
                    "valid_records": len(st.session_state.df_clean) if st.session_state.df_clean is not None else 0,
                    "flagged_records": len(st.session_state.df_flagged) if st.session_state.df_flagged is not None else 0,
                    "duplicates": int((st.session_state.df_flagged["issue_type"] == "Duplicate Record").sum()) if not st.session_state.df_flagged.empty else 0,
                    "missing_fields": int((st.session_state.df_flagged["issue_type"] == "Missing Required Field").sum()) if not st.session_state.df_flagged.empty else 0,
                    "date_errors": int((st.session_state.df_flagged["issue_type"] == "Date Relationship Error").sum()) if not st.session_state.df_flagged.empty else 0,
                    "score_errors": int((st.session_state.df_flagged["issue_type"] == "Invalid Assessment Score").sum()) if not st.session_state.df_flagged.empty else 0,
                }

                report_result = generate_full_report_workflow(
                    df=filtered_df,
                    dq_summary=dq_summary_dict,
                    flagged_df=st.session_state.df_flagged,
                    as_of_date=as_of_str,
                    period_start=start_date_filter,
                    period_end=end_date_filter,
                    api_key=GROQ_API_KEY,
                    model_name=GROQ_MODEL,
                )
                st.session_state.last_report = report_result
            st.success(f"Report generated successfully! ({report_result['report_id']})")

        # Display last generated report
        if "last_report" in st.session_state and st.session_state.last_report:
            rep = st.session_state.last_report
            st.markdown("---")
            st.subheader(f"Report Output: {rep['report_id']}")

            # Download Buttons
            d_c1, d_c2 = st.columns(2)
            with d_c1:
                with open(rep["excel_path"], "rb") as f:
                    excel_bytes = f.read()
                st.download_button(
                    label=f"Download Excel Workbook ({rep['excel_filename']})",
                    data=excel_bytes,
                    file_name=rep["excel_filename"],
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                )
            with d_c2:
                st.download_button(
                    label=f"Download Executive Brief ({rep['markdown_filename']})",
                    data=rep["markdown_content"].encode("utf-8"),
                    file_name=rep["markdown_filename"],
                    mime="text/markdown",
                )

            # Executive Briefing Preview
            st.markdown("### Executive Briefing Preview")
            with st.container():
                st.markdown(rep["markdown_content"])

    with tab_pbi:
        st.subheader("Power BI Desktop Integration")
        st.markdown(
            """
            Export clean, relational CSV datasets configured for immediate import into Microsoft Power BI Desktop.
            Includes fact table, department dimension, course dimension, monthly trends, and data quality summary.
            """
        )

        if st.button("Export Power BI CSV Package", type="secondary"):
            with st.spinner("Generating Power BI CSV exports..."):
                dq_summary_dict = {
                    "total_records": len(st.session_state.df_raw) if st.session_state.df_raw is not None else 0,
                    "valid_records": len(st.session_state.df_clean) if st.session_state.df_clean is not None else 0,
                    "flagged_records": len(st.session_state.df_flagged) if st.session_state.df_flagged is not None else 0,
                    "duplicates": int((st.session_state.df_flagged["issue_type"] == "Duplicate Record").sum()) if not st.session_state.df_flagged.empty else 0,
                    "missing_fields": int((st.session_state.df_flagged["issue_type"] == "Missing Required Field").sum()) if not st.session_state.df_flagged.empty else 0,
                    "date_errors": int((st.session_state.df_flagged["issue_type"] == "Date Relationship Error").sum()) if not st.session_state.df_flagged.empty else 0,
                    "score_errors": int((st.session_state.df_flagged["issue_type"] == "Invalid Assessment Score").sum()) if not st.session_state.df_flagged.empty else 0,
                }
                exported_files = export_power_bi_datasets(
                    clean_df=filtered_df,
                    dept_df=dept_kpi_df,
                    course_df=course_kpi_df,
                    monthly_trends_df=monthly_trend_df,
                    dq_summary=dq_summary_dict,
                )
            st.success("Power BI datasets exported successfully to `data/exports/`!")
            for name, path in exported_files.items():
                st.write(f"- `{name}.csv` ({path.stat().st_size:,} bytes)")

        st.markdown("---")
        st.markdown(
            """
            #### Step-by-Step Power BI Setup
            1. Open **Power BI Desktop**.
            2. Click **Get Data -> Text/CSV** and select `data/exports/training_records_clean.csv`.
            3. Load `department_kpis.csv` and `course_kpis.csv`.
            4. In the **Model View**, establish 1-to-many relationships:
               - `department_kpis[department]` -> `training_records_clean[department]`
               - `course_kpis[course_id]` -> `training_records_clean[course_id]`
            5. See `docs/POWER_BI_GUIDE.md` for complete DAX measure formulas matching this application.
            """
        )

    with tab_hist:
        st.subheader("Historical Generated Reports")
        history_df = get_report_history_df()
        if not history_df.empty:
            st.dataframe(
                history_df[[
                    "report_id", "generated_at", "reporting_period_start",
                    "reporting_period_end", "as_of_date", "excel_filename",
                    "ai_assisted", "status"
                ]],
                use_container_width=True,
            )
        else:
            st.info("No reports generated yet. Click 'Generate Management Report' above.")


# ==============================================================================
# SECTION 5: AI INSIGHTS
# ==============================================================================
elif nav_selection == "AI Insights":
    st.markdown(
        f"""
        <div style="margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 1.85rem; color: {DARK_NAVY};">AI-Powered Management Insights</h1>
            <p style="margin: 4px 0 0 0; color: {TEXT_SECONDARY}; font-size: 0.95rem;">
                Grounded GenAI synthesis powered by Groq SDK with strict factual bounds and prompt explainability.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # API Configuration Bar
    ai_c1, ai_c2 = st.columns([2, 1])
    with ai_c1:
        custom_key = st.text_input(
            "Groq API Key (Optional Session Override)",
            value=GROQ_API_KEY if GROQ_API_KEY != "your_groq_api_key_here" else "",
            type="password",
            help="If not configured, the engine automatically uses the deterministic verified template.",
        )
    with ai_c2:
        model_selection = st.selectbox(
            "Groq Model",
            options=["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
            index=0,
        )

    # Action Button
    if st.button("Generate AI Management Insights", type="primary") or "current_ai_insights" not in st.session_state:
        with st.spinner("Synthesizing metrics snapshot and querying AI Engine..."):
            dq_summary_dict = {
                "total_records": len(st.session_state.df_raw) if st.session_state.df_raw is not None else 0,
                "valid_records": len(st.session_state.df_clean) if st.session_state.df_clean is not None else 0,
                "flagged_records": len(st.session_state.df_flagged) if st.session_state.df_flagged is not None else 0,
                "duplicates": int((st.session_state.df_flagged["issue_type"] == "Duplicate Record").sum()) if not st.session_state.df_flagged.empty else 0,
                "missing_fields": int((st.session_state.df_flagged["issue_type"] == "Missing Required Field").sum()) if not st.session_state.df_flagged.empty else 0,
                "date_errors": int((st.session_state.df_flagged["issue_type"] == "Date Relationship Error").sum()) if not st.session_state.df_flagged.empty else 0,
                "score_errors": int((st.session_state.df_flagged["issue_type"] == "Invalid Assessment Score").sum()) if not st.session_state.df_flagged.empty else 0,
            }
            llm_payload = prepare_llm_payload(active_kpis, dept_kpi_df, course_kpi_df, dq_summary_dict)
            insights_res, is_ai, status_info = generate_management_insights(
                payload=llm_payload,
                api_key=custom_key,
                model_name=model_selection,
            )
            st.session_state.current_ai_insights = insights_res
            st.session_state.is_ai_generated = is_ai
            st.session_state.ai_status_msg = status_info
            st.session_state.llm_payload = llm_payload

    # Display Status Badge
    is_ai_active = st.session_state.get("is_ai_generated", False)
    status_label = st.session_state.get("ai_status_msg", "")
    if is_ai_active:
        st.success(f"🟢 **AI Generation Active:** {status_label}")
    else:
        st.info(f"ℹ️ **Deterministic Fallback Active:** {status_label}")

    insights = st.session_state.get("current_ai_insights", {})

    # Display Insights in Enterprise Cards
    st.markdown("### Executive Summary")
    st.markdown(
        f"""
        <div class="section-box" style="font-size: 1.05rem; line-height: 1.6;">
            {insights.get('executive_summary', 'No summary available.')}
        </div>
        """,
        unsafe_allow_html=True,
    )

    card_c1, card_c2 = st.columns(2)
    with card_c1:
        st.markdown("### Key Operational Findings")
        for finding in insights.get("key_findings", []):
            st.markdown(f"- {finding}")

        st.markdown("### Compliance Risks & Overdue Gaps")
        for risk in insights.get("risks_and_compliance_gaps", []):
            st.markdown(f"- ⚠️ **{risk}**")

    with card_c2:
        st.markdown("### Recommended Action Plan")
        for action in insights.get("recommended_actions", []):
            st.markdown(f"- [ ] {action}")

    # Section 11: AI Prompt Transparency & Explainability
    st.markdown("---")
    st.subheader("AI Prompt Transparency & Explainability")
    st.caption("Inspect the exact payload, prompt constraints, and verification signals passed to the LLM.")

    with st.expander("1. Grounded Input Metrics Snapshot (Payload sent to LLM)"):
        st.json(st.session_state.get("llm_payload", {}))

    with st.expander("2. System Prompt & Grounding Constraints"):
        from src.ai_insights import SYSTEM_PROMPT
        st.code(SYSTEM_PROMPT, language="markdown")

    with st.expander("3. Raw Engine Response"):
        st.json(insights)


# ==============================================================================
# SECTION 6: DATA DICTIONARY & METHODOLOGY
# ==============================================================================
elif nav_selection == "Data Dictionary & Methodology":
    st.markdown(
        f"""
        <div style="margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 1.85rem; color: {DARK_NAVY};">Data Dictionary & Analytics Methodology</h1>
            <p style="margin: 4px 0 0 0; color: {TEXT_SECONDARY}; font-size: 0.95rem;">
                Official KPI calculation formulas, data governance definitions, and edge-case disclosure.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_kpi, tab_dict, tab_arch = st.tabs(["KPI Definitions & Formulas", "Schema Data Dictionary", "Architecture & Governance"])

    with tab_kpi:
        st.subheader("Official KPI Calculation Rules")
        st.markdown(
            """
            | KPI Metric | Calculation Formula | Denominator Treatment | Edge Case & Disclosures |
            | :--- | :--- | :--- | :--- |
            | **Training Completion Rate** | `Completed Assignments / Total Eligible Assignments * 100` | All assignments in filtered date range | Denominator = 0 returns `0.0%`. Flagged records are excluded. |
            | **Attendance Rate** | `Attended Sessions / Tracked Attendance Sessions * 100` | Records with `attendance_status` in `['Attended', 'Partial', 'Absent']` | Self-paced / un-scheduled courses are excluded from denominator or marked 100%. |
            | **Average Assessment Score** | `SUM(Valid Assessment Scores) / Count(Valid Scored Assignments)` | Only records with numeric scores (0–100) | If no records have been scored, returns `N/A` rather than misleading zero. |
            | **Overdue Assignments** | `Count(Uncompleted Assignments WHERE due_date < as_of_date)` | Total eligible uncompleted assignments | Evaluated against configurable As-of reference date. |
            | **Mandatory Completion Rate** | `Completed Mandatory / Total Mandatory Assignments * 100` | Only records where `mandatory_training == True` | Mandatory courses have strict 100% compliance targets. |
            | **Total Training Hours** | `SUM(training_hours for Completed records)` | Completed records only | Reflects actual verified credit hours delivered to the workforce. |
            """
        )

    with tab_dict:
        st.subheader("Dataset Schema & Field Definitions")
        dict_records = [
            {"Field": "record_id", "Type": "String", "Required": "Yes", "Definition": "Surrogate primary key for training assignment."},
            {"Field": "employee_id", "Type": "String", "Required": "Yes", "Definition": "Fictional employee identifier (EMP-XXXX)."},
            {"Field": "employee_name", "Type": "String", "Required": "Yes", "Definition": "Fictional learner full name."},
            {"Field": "department", "Type": "String", "Required": "Yes", "Definition": "Standardized canonical business unit (8 canonical)."},
            {"Field": "course_id", "Type": "String", "Required": "Yes", "Definition": "Course catalog identifier (CRS-XXX-XXX)."},
            {"Field": "course_name", "Type": "String", "Required": "Yes", "Definition": "Official course title."},
            {"Field": "training_category", "Type": "String", "Required": "Yes", "Definition": "Curriculum category (Compliance, Technical, etc.)."},
            {"Field": "mandatory_training", "Type": "Boolean", "Required": "Yes", "Definition": "Whether completion is policy or regulatory mandated."},
            {"Field": "assigned_date", "Type": "Date", "Required": "Yes", "Definition": "Date enrollment was created (YYYY-MM-DD)."},
            {"Field": "due_date", "Type": "Date", "Required": "Yes", "Definition": "Completion deadline. Must be >= assigned_date."},
            {"Field": "completion_date", "Type": "Date", "Required": "No", "Definition": "Date finished. Required if status is Completed."},
            {"Field": "attendance_status", "Type": "Enum", "Required": "No", "Definition": "Attended, Partial, Absent, Not Scheduled, Excused."},
            {"Field": "completion_status", "Type": "Enum", "Required": "Yes", "Definition": "Completed, In Progress, Not Started."},
            {"Field": "assessment_score", "Type": "Float", "Required": "No", "Definition": "Score between 0.0 and 100.0. Null if non-graded."},
            {"Field": "training_hours", "Type": "Float", "Required": "Yes", "Definition": "Accredited curriculum duration hours."},
            {"Field": "delivery_mode", "Type": "Enum", "Required": "No", "Definition": "Virtual, Self-Paced, In-Person, Hybrid."},
            {"Field": "instructor", "Type": "String", "Required": "No", "Definition": "Instructor or LMS proctor name."},
            {"Field": "region", "Type": "Enum", "Required": "No", "Definition": "Geographic operating region."},
        ]
        st.dataframe(pd.DataFrame(dict_records), use_container_width=True)

    with tab_arch:
        st.subheader("System Architecture & Data Governance")
        st.markdown(
            """
            ```
            [ Raw Ingestion / CSV Upload ]
                         │
                         ▼
            [ Validation & Standardization Engine ]
                ├── Schema Validation & Trimming
                ├── Department & Status Canonical Mapping
                ├── Duplicate Key Detection
                ├── Date Logic & Order Constraints (assigned <= due, assigned <= completion)
                └── Score Bound Validation (0 <= score <= 100)
                         │
            ┌────────────┴────────────┐
            ▼                         ▼
      [ Flagged Review ]        [ Clean Relational Database ]
     (Quarantined in SQLite)      (SQLite / clean_training_records)
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            ▼                         ▼                         ▼
    [ Deterministic KPIs ]   [ Excel / Power BI ]     [ AI Insights Engine ]
    - Completion Rates       - 6-Sheet Workbook       - Factual JSON Prompt
    - Attendance Rates       - Model-Ready CSVs       - Groq SDK Llama-3.3
    - Overdue Volume                                  - Fallback Template
            ```
            """
        )
