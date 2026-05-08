"""
Quality Check Dashboard — Multi-City
Supports: Agra, Lucknow, Mathura, Prayagraj
"""

import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="QC Dashboard",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────

CITIES = ["Agra", "Lucknow", "Mathura", "Prayagraj"]

FILE_HINTS = {
    "Agra":      "CSV (.csv) or Excel (.xlsx)",
    "Lucknow":   "Excel (.xlsx)",
    "Mathura":   "Excel (.xlsx)",
    "Prayagraj": "Excel (.xlsx)",
}

QC_COLOR_MAP = {
    "Correct":      "#22c55e",
    "Incorrect":    "#ef4444",
    "Pending":      "#f59e0b",
    "WIP":          "#3b82f6",
    "Not Feasible": "#8b5cf6",
}

SLA_COLOR_MAP = {
    "Within SLA":  "#22c55e",
    "Beyond SLA":  "#ef4444",
}

# ─────────────────────────────────────────────────────────────
# PARSERS  – each returns a normalised DataFrame
# ─────────────────────────────────────────────────────────────

def _sla_from_violation_col(series: pd.Series) -> pd.Series:
    """Derive Within/Beyond SLA from an SLA Violation Time column."""
    def _classify(v):
        if pd.isna(v):
            return "Within SLA"
        s = str(v).strip()
        if s in ("", "0", "nan"):
            return "Within SLA"
        return "Beyond SLA"
    return series.map(_classify)


def parse_prayagraj(file) -> pd.DataFrame:
    df = pd.read_excel(file)

    status_map = {
        "Correct":                    "Correct",
        "Incorrect":                  "Incorrect",
        "Status Yet to be Updated":   "Pending",
    }

    return pd.DataFrame({
        "city":              "Prayagraj",
        "ticket_id":         df.get("Complaint Number", pd.Series(dtype=str)),
        "qc_l1":             df["Review Status"].map(status_map).fillna("Pending"),
        "qc_l2":             pd.Series([None] * len(df), dtype=object),
        "fail_reason_l1":    df.get("Comments", pd.Series(dtype=str)),
        "fail_reason_l2":    pd.Series([None] * len(df), dtype=object),
        "reviewer":          df.get("Surveyor Name", pd.Series(dtype=str)),
        "zone":              df.get("Zone", pd.Series(dtype=str)),
        "ward":              df.get("Ward", pd.Series(dtype=str)),
        "complaint_type":    df.get("Complaint Sub type", pd.Series(dtype=str)),
        "complaint_subtype": pd.Series([None] * len(df), dtype=object),
        "sla_status":        df.get("SLA Status", pd.Series(dtype=str)),
        "reg_date":          pd.to_datetime(df.get("Complaint Registration Date"), dayfirst=True, errors="coerce"),
        "res_date":          pd.to_datetime(df.get("Resolution Date"), dayfirst=True, errors="coerce"),
    })


def parse_agra(file) -> pd.DataFrame:
    try:
        df = pd.read_csv(file)
    except Exception:
        df = pd.read_excel(file)

    l2_raw = df.get("Quality of QC (2nd L)", pd.Series(dtype=str)).fillna("")
    l2_map = {"QC is Okay": "Correct", "": "Pending"}
    l2 = l2_raw.map(lambda v: l2_map.get(str(v).strip(), str(v).strip() if str(v).strip() else "Pending"))

    sla = (_sla_from_violation_col(df["SLA Violation Time"])
           if "SLA Violation Time" in df.columns
           else pd.Series([""] * len(df)))

    return pd.DataFrame({
        "city":              "Agra",
        "ticket_id":         df.get("Issue Number", pd.Series(dtype=str)),
        "qc_l1":             df.get("Quality (1st L)", pd.Series(dtype=str)).fillna("Pending"),
        "qc_l2":             l2,
        "fail_reason_l1":    df.get("Reasons for Incorrect (1st L)", pd.Series(dtype=str)),
        "fail_reason_l2":    df.get("Reasons for Incorrect (2nd L)", pd.Series(dtype=str)),
        "reviewer":          df.get("1st Level QC by", pd.Series(dtype=str)),
        "zone":              df.get("Zone Name", pd.Series(dtype=str)),
        "ward":              df.get("Ward Name", pd.Series(dtype=str)),
        "complaint_type":    df.get("Category", pd.Series(dtype=str)),
        "complaint_subtype": df.get("Subcategory", pd.Series(dtype=str)),
        "sla_status":        sla,
        "reg_date":          pd.to_datetime(df.get("Created At"), dayfirst=True, errors="coerce"),
        "res_date":          pd.to_datetime(df.get("Resolved At"), dayfirst=True, errors="coerce"),
    })


def parse_lucknow(file) -> pd.DataFrame:
    df = pd.read_excel(file)

    sla = (_sla_from_violation_col(df["SLA Violation Time"])
           if "SLA Violation Time" in df.columns
           else pd.Series([""] * len(df)))

    reviewer = (df.get("Operator Name", pd.Series(dtype=str))
                .where(df.get("Operator Name", pd.Series(dtype=str)).notna(),
                       df.get("User Name", pd.Series(dtype=str))))

    return pd.DataFrame({
        "city":              "Lucknow",
        "ticket_id":         df.get("Issue Number", pd.Series(dtype=str)),
        "qc_l1":             df.get("Quality (L1)", pd.Series(dtype=str)).fillna("Pending"),
        "qc_l2":             df.get("Quality (L2)", pd.Series(dtype=str)).fillna("Pending"),
        "fail_reason_l1":    df.get("Reason (L1)", pd.Series(dtype=str)),
        "fail_reason_l2":    df.get("Reason (L2)", pd.Series(dtype=str)),
        "reviewer":          reviewer,
        "zone":              df.get("Zone Name", pd.Series(dtype=str)),
        "ward":              df.get("Ward Name", pd.Series(dtype=str)),
        "complaint_type":    df.get("Category", pd.Series(dtype=str)),
        "complaint_subtype": df.get("Subcategory", pd.Series(dtype=str)),
        "sla_status":        sla,
        "reg_date":          pd.to_datetime(df.get("Created At"), dayfirst=True, errors="coerce"),
        "res_date":          pd.to_datetime(df.get("Resolved At"), dayfirst=True, errors="coerce"),
    })


def parse_mathura(file) -> pd.DataFrame:
    df = pd.read_excel(file)

    status_map = {"ok": "Correct", "wrong": "Incorrect"}

    reviewer = df.get("SFI Name", pd.Series(dtype=str)).where(
        df.get("SFI Name", pd.Series(dtype=str)).notna(),
        df.get("Assignee", pd.Series(dtype=str))
    )

    return pd.DataFrame({
        "city":              "Mathura",
        "ticket_id":         df.get("compId", pd.Series(dtype=str)),
        "qc_l1":             df.get("Status.1", pd.Series(dtype=str))
                               .map(lambda v: status_map.get(str(v).strip().lower(), "Pending")),
        "qc_l2":             pd.Series([None] * len(df), dtype=object),
        "fail_reason_l1":    df.get("Supervisor Remark", pd.Series(dtype=str)),
        "fail_reason_l2":    pd.Series([None] * len(df), dtype=object),
        "reviewer":          reviewer,
        "zone":              df.get("Zone", pd.Series(dtype=str)),
        "ward":              df.get("Ward", pd.Series(dtype=str)),
        "complaint_type":    df.get("Complainttype", pd.Series(dtype=str)),
        "complaint_subtype": df.get("complaintsubtype", pd.Series(dtype=str)),
        "sla_status":        pd.Series([""] * len(df)),
        "reg_date":          pd.to_datetime(df.get("Complaint Registered Date"), dayfirst=True, errors="coerce"),
        "res_date":          pd.to_datetime(df.get("Closing Date"), dayfirst=True, errors="coerce"),
    })


PARSERS = {
    "Agra":      parse_agra,
    "Lucknow":   parse_lucknow,
    "Mathura":   parse_mathura,
    "Prayagraj": parse_prayagraj,
}

# ─────────────────────────────────────────────────────────────
# CHART HELPERS
# ─────────────────────────────────────────────────────────────

def _clean_series(s: pd.Series) -> pd.Series:
    return s.dropna().loc[s.astype(str).str.strip() != ""]


def pie_qc(df: pd.DataFrame, col: str, title: str):
    counts = df[col].value_counts().reset_index()
    counts.columns = ["Status", "Count"]
    fig = px.pie(
        counts, names="Status", values="Count", title=title,
        color="Status", color_discrete_map=QC_COLOR_MAP, hole=0.45,
    )
    fig.update_traces(textposition="outside", textinfo="percent+label")
    fig.update_layout(
        showlegend=True, height=320,
        margin=dict(t=50, b=20, l=10, r=10),
        title_font_size=14,
    )
    return fig


def bar_reasons(df: pd.DataFrame, col: str, title: str):
    series = _clean_series(df[col])
    if series.empty:
        return None
    counts = series.value_counts().head(8).reset_index()
    counts.columns = ["Reason", "Count"]
    fig = px.bar(
        counts, x="Count", y="Reason", orientation="h",
        title=title, color_discrete_sequence=["#ef4444"],
    )
    fig.update_layout(
        height=300, margin=dict(t=50, b=10, l=10, r=10),
        yaxis={"categoryorder": "total ascending"}, title_font_size=14,
    )
    return fig


def _subcat_melted(df: pd.DataFrame, n: int = 12):
    """Shared helper: returns (melted_df, cat_order) using actual qc_l1 values — no Other bucket."""
    sub = df["complaint_subtype"].where(
        df["complaint_subtype"].notna() & (df["complaint_subtype"].astype(str).str.strip() != ""),
        df["complaint_type"],
    )
    tmp = df.copy()
    tmp["_sub"] = sub
    tmp = tmp[tmp["_sub"].notna() & (tmp["_sub"].astype(str).str.strip() != "")]
    if tmp.empty:
        return None

    top = tmp["_sub"].value_counts().head(n).index
    tmp = tmp[tmp["_sub"].isin(top)]

    # Group by subcategory + actual qc_l1 value — no hardcoded buckets
    grp = (
        tmp.groupby(["_sub", "qc_l1"])
        .size()
        .reset_index(name="Count")
        .rename(columns={"_sub": "Subcategory", "qc_l1": "QC Status"})
    )
    totals = grp.groupby("Subcategory")["Count"].sum().rename("_total")
    grp = grp.join(totals, on="Subcategory")
    cat_order = (
        grp.drop_duplicates("Subcategory")
        .sort_values("_total")["Subcategory"]
        .tolist()
    )
    grp["Pct"] = (grp["Count"] / grp["_total"] * 100).round(1)
    grp["Label"] = grp["Pct"].apply(lambda p: f"{p:.0f}%" if p >= 5 else "")
    grp = grp.drop(columns="_total")
    return grp, cat_order


def bar_subcategory(df: pd.DataFrame, title: str):
    result = _subcat_melted(df)
    if result is None:
        return None
    melted, cat_order = result

    fig = px.bar(
        melted, x="Count", y="Subcategory", color="QC Status",
        orientation="h", title=title, barmode="stack",
        text="Label",
        color_discrete_map=QC_COLOR_MAP,
        custom_data=["Pct"],
    )
    fig.update_traces(
        textposition="inside",
        insidetextanchor="middle",
        textfont_size=11,
        hovertemplate="<b>%{y}</b><br>%{fullData.name}: %{x} tickets (%{customdata[0]:.1f}%)<extra></extra>",
    )
    fig.update_layout(
        height=420, margin=dict(t=50, b=10, l=10, r=10),
        yaxis={"categoryorder": "array", "categoryarray": cat_order},
        legend_title="QC Status", title_font_size=14,
        xaxis_title="Tickets",
    )
    return fig


def pie_sla(df: pd.DataFrame, title: str):
    sla_df = df[df["sla_status"].isin(["Within SLA", "Beyond SLA"])]
    if sla_df.empty:
        return None
    counts = sla_df["sla_status"].value_counts().reset_index()
    counts.columns = ["SLA", "Count"]
    fig = px.pie(
        counts, names="SLA", values="Count", title=title,
        color="SLA", color_discrete_map=SLA_COLOR_MAP, hole=0.45,
    )
    fig.update_traces(textposition="outside", textinfo="percent+label")
    fig.update_layout(height=320, margin=dict(t=50, b=20, l=10, r=10), title_font_size=14)
    return fig


def bar_zone_stacked(df: pd.DataFrame, title: str):
    zone_col = _clean_series(df["zone"])
    if zone_col.empty:
        return None
    tmp = df[df["zone"].notna() & (df["zone"].astype(str).str.strip() != "")]
    grp = (
        tmp.groupby(["zone", "qc_l1"])
        .size()
        .reset_index(name="Count")
        .rename(columns={"qc_l1": "QC Status"})
    )
    totals = grp.groupby("zone")["Count"].sum().rename("_total")
    grp = grp.join(totals, on="zone")
    grp["Pct"] = (grp["Count"] / grp["_total"] * 100).round(1)
    grp["Label"] = grp["Pct"].apply(lambda p: f"{p:.0f}%" if p >= 5 else "")
    grp = grp.drop(columns="_total")

    fig = px.bar(
        grp, x="zone", y="Count", color="QC Status",
        title=title, barmode="stack",
        text="Label",
        color_discrete_map=QC_COLOR_MAP,
        custom_data=["Pct"],
    )
    fig.update_traces(
        textposition="inside",
        insidetextanchor="middle",
        textfont_size=11,
        hovertemplate="<b>%{x}</b><br>%{fullData.name}: %{y} tickets (%{customdata[0]:.1f}%)<extra></extra>",
    )
    fig.update_layout(height=320, margin=dict(t=50, b=10, l=10, r=10),
                      xaxis_title="Zone", yaxis_title="Tickets", title_font_size=14)
    return fig


def agent_table(df: pd.DataFrame):
    rev = _clean_series(df["reviewer"])
    if rev.empty:
        return None
    grp = (
        df[df["reviewer"].notna() & (df["reviewer"].astype(str).str.strip() != "")]
        .groupby("reviewer")
        .apply(lambda x: pd.Series({
            "Total":     len(x),
            "Correct":   (x["qc_l1"] == "Correct").sum(),
            "Incorrect": (x["qc_l1"] == "Incorrect").sum(),
            "Pass Rate": f"{(x['qc_l1'] == 'Correct').sum() / len(x) * 100:.1f}%",
        }))
        .reset_index()
        .rename(columns={"reviewer": "Reviewer"})
        .sort_values("Total", ascending=False)
        .reset_index(drop=True)
    )
    return grp


# ─────────────────────────────────────────────────────────────
# METRICS ROW
# ─────────────────────────────────────────────────────────────

def metrics_row(df: pd.DataFrame):
    total     = len(df)
    correct   = (df["qc_l1"] == "Correct").sum()
    incorrect = (df["qc_l1"] == "Incorrect").sum()
    other     = total - correct - incorrect
    pass_rate = round(correct / total * 100, 1) if total > 0 else 0.0

    sla_vals  = df["sla_status"].astype(str)
    within    = (sla_vals == "Within SLA").sum()
    beyond    = (sla_vals == "Beyond SLA").sum()
    sla_total = within + beyond
    sla_rate  = round(within / sla_total * 100, 1) if sla_total > 0 else None

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("📋 Total Tickets",  f"{total:,}")
    c2.metric("✅ Correct",         f"{correct:,}")
    c3.metric("❌ Incorrect",        f"{incorrect:,}")
    c4.metric("⏳ Other / Pending", f"{other:,}")
    c5.metric("📈 Pass Rate (L1)",  f"{pass_rate}%")
    if sla_rate is not None:
        c6.metric("⏱️ Within SLA",  f"{sla_rate}%")
    else:
        c6.metric("⏱️ SLA Data", "N/A")


# ─────────────────────────────────────────────────────────────
# PER-CITY TAB
# ─────────────────────────────────────────────────────────────

def render_city(df: pd.DataFrame, city: str):
    has_l2 = df["qc_l2"].notna().any() and (df["qc_l2"].astype(str).str.strip() != "").any()

    st.subheader(f"📊 {city} — Quality Check Summary")
    metrics_row(df)
    st.divider()

    # ── Row 1: QC status pies ─────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(pie_qc(df, "qc_l1", "L1 QC Status"), use_container_width=True)
    with col2:
        if has_l2:
            st.plotly_chart(pie_qc(df, "qc_l2", "L2 QC Status"), use_container_width=True)
        else:
            fig = pie_sla(df, "SLA Status")
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No SLA data available for this city.")

    # ── Row 2: Fail reasons + complaint types ─────────────────
    col3, col4 = st.columns(2)
    with col3:
        fig = bar_reasons(df, "fail_reason_l1", "Top Failure Reasons (L1)")
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No failure reason data for L1.")
    with col4:
        if has_l2:
            fig = bar_reasons(df, "fail_reason_l2", "Top Failure Reasons (L2)")
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No failure reason data for L2.")
        else:
            fig = bar_subcategory(df, "Subcategory Distribution")
            if fig:
                st.plotly_chart(fig, use_container_width=True)

    # ── Row 3: Zone breakdown ──────────────────────────────────
    fig = bar_zone_stacked(df, "QC Results by Zone")
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No zone data available.")

    # ── Row 4: Subcategory (if has_l2, complaint type col was used in row 2 for L2 reasons) ──
    if has_l2:
        fig = bar_subcategory(df, "Subcategory Distribution")
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    # ── Raw data ──────────────────────────────────────────────
    with st.expander("🔍 View Raw Normalised Data"):
        st.dataframe(df, use_container_width=True)


# ─────────────────────────────────────────────────────────────
# OVERVIEW TAB
# ─────────────────────────────────────────────────────────────

def render_overview(city_data: dict):
    st.subheader("🌆 All Cities — Overview")

    combined = pd.concat(list(city_data.values()), ignore_index=True)

    # ── Per-city headline metrics ──────────────────────────────
    cols = st.columns(len(city_data))
    city_stats = []
    for i, (city, df) in enumerate(city_data.items()):
        total    = len(df)
        correct  = (df["qc_l1"] == "Correct").sum()
        incorrect= (df["qc_l1"] == "Incorrect").sum()
        rate     = round(correct / total * 100, 1) if total > 0 else 0.0
        delta_color = "normal" if rate >= 80 else "inverse"
        cols[i].metric(city, f"{rate}% pass", f"{total:,} tickets", delta_color=delta_color)
        city_stats.append({
            "City": city, "Total": total,
            "Correct": correct, "Incorrect": incorrect,
            "Pass Rate (%)": rate,
        })
    stats_df = pd.DataFrame(city_stats)

    st.divider()

    # ── Row 1: Stacked bar + pass-rate comparison ──────────────
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(
            stats_df, x="City", y=["Correct", "Incorrect"],
            title="QC Results by City (Stacked)", barmode="stack",
            color_discrete_map={"Correct": "#22c55e", "Incorrect": "#ef4444"},
        )
        fig.update_layout(height=360, margin=dict(t=50, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        avg = stats_df["Pass Rate (%)"].mean()
        fig = px.bar(
            stats_df, x="City", y="Pass Rate (%)",
            title="Pass Rate Comparison (%)",
            color="Pass Rate (%)",
            color_continuous_scale=["#ef4444", "#f59e0b", "#22c55e"],
            range_color=[50, 100],
            text="Pass Rate (%)",
        )
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        fig.add_hline(
            y=avg, line_dash="dash", line_color="gray",
            annotation_text=f"Avg {avg:.1f}%", annotation_position="top right",
        )
        fig.update_layout(height=360, margin=dict(t=50, b=10, l=10, r=10),
                          coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # ── Row 2: Combined failure reasons ───────────────────────
    st.subheader("❌ Top Failure Reasons Across All Cities")
    col3, col4 = st.columns(2)
    with col3:
        all_reasons = _clean_series(combined["fail_reason_l1"])
        if not all_reasons.empty:
            rc = all_reasons.value_counts().head(10).reset_index()
            rc.columns = ["Reason", "Count"]
            fig = px.bar(
                rc, x="Count", y="Reason", orientation="h",
                title="All Cities — L1 Failure Reasons",
                color_discrete_sequence=["#ef4444"],
            )
            fig.update_layout(height=320, margin=dict(t=50, b=10, l=10, r=10),
                              yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True)

    with col4:
        # Failure reasons broken out by city
        reason_city = (
            combined[combined["fail_reason_l1"].notna() &
                     (combined["fail_reason_l1"].astype(str).str.strip() != "")]
            .groupby(["city", "fail_reason_l1"])
            .size()
            .reset_index(name="Count")
            .sort_values("Count", ascending=False)
            .head(20)
        )
        if not reason_city.empty:
            fig = px.bar(
                reason_city, x="Count", y="fail_reason_l1", color="city",
                orientation="h", title="Failure Reasons by City",
                barmode="stack",
            )
            fig.update_layout(height=320, margin=dict(t=50, b=10, l=10, r=10),
                              yaxis={"categoryorder": "total ascending"},
                              legend_title="City")
            st.plotly_chart(fig, use_container_width=True)

    # ── Summary table ──────────────────────────────────────────
    st.subheader("📊 Summary Table")
    summary = stats_df.copy()
    summary["Pass Rate (%)"] = summary["Pass Rate (%)"].map(lambda x: f"{x}%")
    st.dataframe(summary, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────

def sidebar_uploads() -> dict:
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/city.png", width=60)
        st.title("QC Dashboard")
        st.caption("Quality Check Ticket Analyser")
        st.divider()

        st.header("📂 Upload City Files")
        uploads = {}
        for city in CITIES:
            st.markdown(f"**{city}** — _{FILE_HINTS[city]}_")
            f = st.file_uploader(
                label=city, type=["xlsx", "csv"],
                key=f"upload_{city}", label_visibility="collapsed",
            )
            if f:
                uploads[city] = f
            st.markdown("")

        st.divider()
        if uploads:
            st.success(f"✅ {len(uploads)} city file(s) loaded")
        else:
            st.info("Upload files above to start.")

    return uploads


# ─────────────────────────────────────────────────────────────
# LANDING PAGE
# ─────────────────────────────────────────────────────────────

def landing():
    st.title("🏙️ Quality Check Dashboard")
    st.markdown(
        "Upload Excel / CSV quality check files for any or all cities "
        "using the **sidebar on the left** to get started."
    )

    cols = st.columns(4)
    city_icons = {"Agra": "🏯", "Lucknow": "🕌", "Mathura": "🙏", "Prayagraj": "🌊"}
    for col, city in zip(cols, CITIES):
        with col:
            with st.container(border=True):
                st.markdown(f"## {city_icons[city]}")
                st.markdown(f"**{city}**")
                st.caption(FILE_HINTS[city])

    st.divider()
    st.markdown("#### 📈 What you'll see after uploading:")

    features = [
        ("📊", "QC Pass / Fail rates", "L1 and L2 breakdown where available"),
        ("❌", "Failure Reasons",       "Top reasons tickets were marked Incorrect"),
        ("🗺️", "Zone Breakdown",        "Pass rates per Zone and Ward"),
        ("🌆", "City Comparison",       "Side-by-side overview of all uploaded cities"),
    ]
    cols2 = st.columns(3)
    for i, (icon, title, desc) in enumerate(features):
        with cols2[i % 3]:
            with st.container(border=True):
                st.markdown(f"### {icon} {title}")
                st.caption(desc)


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    uploads = sidebar_uploads()

    if not uploads:
        landing()
        return

    # Parse files
    city_data: dict = {}
    for city, file in uploads.items():
        try:
            df = PARSERS[city](file)
            city_data[city] = df
        except Exception as exc:
            st.error(f"⚠️ Could not parse **{city}** file: {exc}")

    if not city_data:
        return

    # Build tabs: Overview (if >1 city) + one tab per city
    if len(city_data) > 1:
        tab_labels = ["🌆 Overview"] + [f"🏙️ {c}" for c in city_data]
        tabs = st.tabs(tab_labels)
        with tabs[0]:
            render_overview(city_data)
        for i, (city, df) in enumerate(city_data.items()):
            with tabs[i + 1]:
                render_city(df, city)
    else:
        city, df = next(iter(city_data.items()))
        st.tabs([f"🏙️ {city}"])  # cosmetic only
        render_city(df, city)


if __name__ == "__main__":
    main()
