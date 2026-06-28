import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
from collections import Counter

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AFU Global Network Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 1.2rem 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        text-align: center;
        border-left: 4px solid #2E6DA4;
    }
    .metric-value { font-size: 2.2rem; font-weight: 700; color: #2E6DA4; }
    .metric-label { font-size: 0.85rem; color: #666; margin-top: 4px; }
    .section-title {
        font-size: 1.15rem; font-weight: 600; color: #2E6DA4;
        border-bottom: 2px solid #2E6DA4; padding-bottom: 6px;
        margin-bottom: 1rem;
    }
    .insight-box {
        background: #EBF3FB;
        border-left: 4px solid #2E6DA4;
        padding: 0.8rem 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0 1rem 0;
        font-size: 0.9rem;
    }
    .warning-box {
        background: #FEF3E2;
        border-left: 4px solid #F39C12;
        padding: 0.8rem 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0 1rem 0;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Data ───────────────────────────────────────────────────────────────────
@st.cache_data
def load_country_data():
    return pd.DataFrame([
        ("United States","North America",106,4773,37.09,-95.71),
        ("Canada","North America",11,383,56.13,-106.35),
        ("Ireland","Europe",9,26,53.41,-8.24),
        ("United Kingdom","Europe",2,160,55.37,-3.43),
        ("Portugal","Europe",2,35,39.39,-8.22),
        ("Spain","Europe",2,83,40.46,-3.74),
        ("Croatia","Europe",1,10,45.10,15.20),
        ("Czech Republic","Europe",1,26,49.81,15.47),
        ("Hungary","Europe",1,22,47.16,19.50),
        ("Israel","Europe",1,25,31.04,34.85),
        ("Slovakia","Europe",1,20,48.66,19.69),
        ("Slovenia","Europe",1,5,46.15,14.99),
        ("Switzerland","Europe",1,12,46.81,8.22),
        ("South Korea","Asia",3,401,35.90,127.76),
        ("China","Asia",1,3167,35.86,104.19),
        ("Philippines","Asia",1,366,12.87,121.77),
        ("Hong Kong SAR","Asia",1,10,22.39,114.10),
        ("Australia","Oceania",2,43,-25.27,133.77),
        ("Brazil","South America",3,1264,-14.23,-51.92),
        ("Chile","South America",2,60,-35.67,-71.54),
        ("Ghana","Africa (Unofficial)",1,80,7.95,-1.02),
    ], columns=["Country","Region","AFU_Members","Total_Universities","Latitude","Longitude"])

@st.cache_data
def load_regional_data():
    return pd.DataFrame([
        ("North America",2,23,117),
        ("Europe",13,44,22),
        ("Asia",4,48,6),
        ("Oceania",1,14,2),
        ("South America",2,12,5),
        ("Africa",1,54,1),
    ], columns=["Region","Countries_in_AFU","Total_Countries","AFU_Institutions"])

@st.cache_data
def load_principles_data():
    return pd.DataFrame([
        (1,"Encourage participation\nof older adults",18,72.0,"Well Implemented"),
        (2,"Personal & career\ndevelopment",8,32.0,"Moderately Implemented"),
        (3,"Recognize educational\nneeds of older adults",7,28.0,"Moderately Implemented"),
        (4,"Promote intergenerational\nlearning",14,56.0,"Well Implemented"),
        (5,"Online access for\nolder adults",4,16.0,"Underimplemented"),
        (6,"Research agenda\ninformed by aging",12,48.0,"Well Implemented"),
        (7,"Student understanding\nof longevity dividend",4,16.0,"Underimplemented"),
        (8,"Health, wellness &\ncultural access",12,48.0,"Well Implemented"),
        (9,"Engage retired\ncommunity",7,28.0,"Moderately Implemented"),
        (10,"Dialogue with aging\norganizations",5,20.0,"Underimplemented"),
    ], columns=["Principle_Number","Short_Label","Mentions","Pct","Gap_Flag"])

@st.cache_data
def load_best_practices():
    import os
    # Works both locally and on Streamlit Cloud
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "Form Data Entry-Grid view.csv")
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]
    return df

# Colour palette
REGION_COLORS = {
    "North America": "#2E6DA4",
    "Europe": "#27AE60",
    "Asia": "#E74C3C",
    "Oceania": "#F39C12",
    "South America": "#8E44AD",
    "Africa (Unofficial)": "#95A5A6",
    "Africa": "#95A5A6",
}

GAP_COLORS = {
    "Well Implemented": "#27AE60",
    "Moderately Implemented": "#F39C12",
    "Underimplemented": "#E74C3C",
}

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://www.afugn.org/assets/images/logo.png", width=160, use_container_width=False)
    st.markdown("## 📊 Navigation")
    page = st.radio("", [
        "🌍 Global Overview",
        "📐 Principle Gap Analysis",
        "🗺️ Regional Equity",
        "📋 Best Practices Explorer",
    ], label_visibility="collapsed")

    st.markdown("---")
    st.markdown("**Data Sources**")
    st.markdown("- AFU GN Website (June 2026)\n- AFU Best Practices Database\n- UNESCO UIS 2024\n- National HEI Registries")
    st.markdown("---")
    st.caption("Paper: *Implementation Gap Analysis of the AFU Global Network*\nConference: Generations at Work, DCU, Oct 2026")

# ── Load data ──────────────────────────────────────────────────────────────
df_country = load_country_data()
df_country["Penetration_Pct"] = (df_country["AFU_Members"] / df_country["Total_Universities"] * 100).round(2)
df_regional = load_regional_data()
df_regional["Countries_Missing"] = df_regional["Total_Countries"] - df_regional["Countries_in_AFU"]
df_regional["Country_Coverage_Pct"] = (df_regional["Countries_in_AFU"] / df_regional["Total_Countries"] * 100).round(1)
df_principles = load_principles_data()
df_bp = load_best_practices()

# ══════════════════════════════════════════════════════════════════════════
# PAGE 1 — GLOBAL OVERVIEW
# ══════════════════════════════════════════════════════════════════════════
if page == "🌍 Global Overview":
    st.title("🌍 AFU Global Network — Implementation Gap Analysis")
    st.markdown("*Age-Friendly University Global Network • Geographic & Thematic Analysis • June 2026*")
    st.markdown("---")

    # KPI cards
    c1, c2, c3, c4, c5 = st.columns(5)
    kpis = [
        (c1, "153", "Member Institutions"),
        (c2, "21", "Countries Represented"),
        (c3, "195", "Countries Worldwide"),
        (c4, "25", "Best Practice Submissions"),
        (c5, "11%", "Submission Participation Rate"),
    ]
    for col, val, label in kpis:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{val}</div>
                <div class="metric-label">{label}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # World map
    st.markdown('<div class="section-title">🗺️ Member Institutions by Country</div>', unsafe_allow_html=True)
    fig_map = px.scatter_geo(
        df_country,
        lat="Latitude", lon="Longitude",
        size="AFU_Members",
        color="Region",
        hover_name="Country",
        hover_data={"AFU_Members": True, "Penetration_Pct": True,
                    "Latitude": False, "Longitude": False},
        color_discrete_map=REGION_COLORS,
        size_max=50,
        projection="natural earth",
        title="",
    )
    fig_map.update_layout(
        height=460,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="white",
        geo=dict(showframe=False, showcoastlines=True,
                 coastlinecolor="#CCCCCC", showland=True,
                 landcolor="#F5F5F5", showocean=True, oceancolor="#EAF4FB"),
        legend=dict(orientation="h", y=-0.05)
    )
    st.plotly_chart(fig_map, use_container_width=True)

    st.markdown("""
    <div class="insight-box">
    💡 <strong>Key Finding:</strong> North America accounts for <strong>77% of all AFU member institutions</strong>
    (117/153), with the United States alone representing <strong>70%</strong> (106/153) of the global network.
    Africa has no official members despite Ghana actively submitting best practices.
    </div>""", unsafe_allow_html=True)

    # Regional donut
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown('<div class="section-title">Regional Distribution of Institutions</div>', unsafe_allow_html=True)
        fig_donut = px.pie(
            df_regional, values="AFU_Institutions", names="Region",
            color="Region", color_discrete_map=REGION_COLORS,
            hole=0.45,
        )
        fig_donut.update_traces(textinfo="percent+label", textposition="outside")
        fig_donut.update_layout(height=380, showlegend=False,
                                margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_donut, use_container_width=True)

    with col2:
        st.markdown('<div class="section-title">Institutions per Region</div>', unsafe_allow_html=True)
        fig_bar = px.bar(
            df_regional.sort_values("AFU_Institutions"),
            x="AFU_Institutions", y="Region",
            color="Region", color_discrete_map=REGION_COLORS,
            orientation="h", text="AFU_Institutions",
        )
        fig_bar.update_traces(textposition="outside")
        fig_bar.update_layout(height=380, showlegend=False,
                              xaxis_title="Number of Institutions",
                              yaxis_title="",
                              margin=dict(l=10, r=40, t=20, b=20))
        st.plotly_chart(fig_bar, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════
# PAGE 2 — PRINCIPLE GAP ANALYSIS
# ══════════════════════════════════════════════════════════════════════════
elif page == "📐 Principle Gap Analysis":
    st.title("📐 AFU Principle Implementation Gap Analysis")
    st.markdown("*Based on 25 Best Practice submissions from 17 institutions*")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        well = df_principles[df_principles["Gap_Flag"]=="Well Implemented"].shape[0]
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#27AE60">{well}</div><div class="metric-label">Well Implemented Principles</div></div>', unsafe_allow_html=True)
    with col2:
        mod = df_principles[df_principles["Gap_Flag"]=="Moderately Implemented"].shape[0]
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#F39C12">{mod}</div><div class="metric-label">Moderately Implemented</div></div>', unsafe_allow_html=True)
    with col3:
        under = df_principles[df_principles["Gap_Flag"]=="Underimplemented"].shape[0]
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#E74C3C">{under}</div><div class="metric-label">Underimplemented Principles</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Main bar chart
    st.markdown('<div class="section-title">Principle Citation Frequency in Best Practices (% of 25 submissions)</div>', unsafe_allow_html=True)

    df_p = df_principles.copy()
    df_p["Label"] = df_p.apply(lambda r: f"P{r['Principle_Number']}: {r['Short_Label']}", axis=1)

    fig_p = px.bar(
        df_p.sort_values("Pct"),
        x="Pct", y="Label",
        color="Gap_Flag",
        color_discrete_map=GAP_COLORS,
        orientation="h",
        text="Pct",
        labels={"Pct": "% of Submissions", "Label": ""},
    )
    fig_p.update_traces(texttemplate="%{text}%", textposition="outside")
    fig_p.update_layout(
        height=480,
        xaxis=dict(range=[0, 85], title="% of Submissions Citing Principle"),
        legend_title="Implementation Status",
        margin=dict(l=10, r=60, t=20, b=20),
        legend=dict(orientation="h", y=-0.12)
    )
    # Add 50% reference line
    fig_p.add_vline(x=50, line_dash="dot", line_color="gray",
                    annotation_text="50% threshold", annotation_position="top")
    st.plotly_chart(fig_p, use_container_width=True)

    st.markdown("""
    <div class="insight-box">
    💡 <strong>Key Finding:</strong> <strong>Principle 5</strong> (Online access for older adults) and
    <strong>Principle 7</strong> (Student understanding of the longevity dividend) are both cited in only
    <strong>16% of submissions</strong> — the lowest of all 10 principles. These youth-facing and
    digital-access dimensions represent the most significant implementation gaps across the network.
    </div>""", unsafe_allow_html=True)

    # Audience breakdown
    st.markdown("---")
    st.markdown('<div class="section-title">Who Do Best Practice Activities Target?</div>', unsafe_allow_html=True)

    audience_col = [c for c in df_bp.columns if "aimed at" in c.lower()][0]
    aud_counter = Counter()
    for val in df_bp[audience_col].dropna():
        for a in val.split(","):
            aud_counter[a.strip()] += 1

    df_aud = pd.DataFrame(aud_counter.items(), columns=["Audience", "Count"]).sort_values("Count", ascending=True)
    fig_aud = px.bar(df_aud, x="Count", y="Audience", orientation="h",
                     color="Count", color_continuous_scale="Blues",
                     text="Count")
    fig_aud.update_traces(textposition="outside")
    fig_aud.update_layout(height=350, showlegend=False,
                          coloraxis_showscale=False,
                          margin=dict(l=10, r=40, t=20, b=20))
    st.plotly_chart(fig_aud, use_container_width=True)

    st.markdown("""
    <div class="warning-box">
    ⚠️ Despite Principle 7 calling for increased <em>student</em> understanding of aging,
    the audience data shows activities are primarily co-designed for mixed audiences.
    Dedicated student-only programming is rare, reinforcing the P7 implementation gap.
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# PAGE 3 — REGIONAL EQUITY
# ══════════════════════════════════════════════════════════════════════════
elif page == "🗺️ Regional Equity":
    st.title("🗺️ Geographic Equity & Penetration Analysis")
    st.markdown("*Country coverage gaps and institutional adoption rates across AFU regions*")
    st.markdown("---")

    tab1, tab2 = st.tabs(["Country Coverage Gap", "Penetration Rate by Country"])

    with tab1:
        st.markdown('<div class="section-title">Countries Represented vs. Total Countries Per Region</div>', unsafe_allow_html=True)

        df_melt = df_regional.melt(
            id_vars="Region",
            value_vars=["Countries_in_AFU","Countries_Missing"],
            var_name="Type", value_name="Count"
        )
        df_melt["Type"] = df_melt["Type"].map({
            "Countries_in_AFU": "In AFU GN",
            "Countries_Missing": "Not in AFU GN"
        })
        fig_cov = px.bar(
            df_melt, x="Count", y="Region", color="Type",
            orientation="h",
            color_discrete_map={"In AFU GN": "#2E6DA4", "Not in AFU GN": "#D5E8F5"},
            barmode="stack",
            text="Count"
        )
        fig_cov.update_traces(textposition="inside")
        fig_cov.update_layout(height=400, legend_title="",
                              xaxis_title="Number of Countries",
                              margin=dict(l=10, r=20, t=20, b=20),
                              legend=dict(orientation="h", y=-0.12))
        st.plotly_chart(fig_cov, use_container_width=True)

        st.markdown("""
        <div class="insight-box">
        💡 <strong>Africa:</strong> 54 countries, 0 official members — yet Ghana actively participates
        in best practices without formal membership. <strong>Asia:</strong> 48 countries, only 4 represented (8.3%).
        </div>""", unsafe_allow_html=True)

        # Coverage % table
        st.markdown('<div class="section-title">Country Coverage Summary</div>', unsafe_allow_html=True)
        df_display = df_regional[["Region","Countries_in_AFU","Total_Countries","Countries_Missing","Country_Coverage_Pct"]].copy()
        df_display.columns = ["Region","In AFU GN","Total Countries","Not Represented","Coverage %"]
        st.dataframe(df_display.style.background_gradient(subset=["Coverage %"], cmap="RdYlGn"),
                     use_container_width=True, hide_index=True)

    with tab2:
        st.markdown('<div class="section-title">AFU Adoption as % of National University System</div>', unsafe_allow_html=True)
        st.markdown("*How many of a country's universities have joined AFU GN?*")

        df_pen = df_country.sort_values("Penetration_Pct", ascending=False).copy()
        df_pen["Color"] = df_pen["Region"].map(REGION_COLORS)

        fig_pen = px.bar(
            df_pen,
            x="Country", y="Penetration_Pct",
            color="Region",
            color_discrete_map=REGION_COLORS,
            text=df_pen["Penetration_Pct"].apply(lambda x: f"{x}%"),
            hover_data={"AFU_Members": True, "Total_Universities": True}
        )
        fig_pen.update_traces(textposition="outside", textfont_size=10)
        fig_pen.update_layout(
            height=500,
            xaxis_tickangle=-45,
            yaxis_title="Penetration Rate (%)",
            xaxis_title="",
            legend_title="Region",
            margin=dict(l=10, r=10, t=20, b=120),
        )
        st.plotly_chart(fig_pen, use_container_width=True)

        st.markdown("""
        <div class="insight-box">
        💡 <strong>Ireland (34.6%)</strong> has by far the highest penetration — a founder effect,
        since DCU established AFU in 2012. <strong>China (0.03%)</strong>, with 3,167 universities,
        has just one AFU member — the lowest penetration rate of any represented country.
        </div>""", unsafe_allow_html=True)

        # Scatter: AFU members vs total unis
        st.markdown("---")
        st.markdown('<div class="section-title">AFU Members vs. National University System Size</div>', unsafe_allow_html=True)
        fig_sc = px.scatter(
            df_country,
            x="Total_Universities", y="AFU_Members",
            color="Region", size="Penetration_Pct",
            hover_name="Country",
            color_discrete_map=REGION_COLORS,
            log_x=True,
            labels={"Total_Universities":"Total Universities (log scale)",
                    "AFU_Members":"AFU Member Institutions"},
            size_max=30
        )
        fig_sc.update_layout(height=420, margin=dict(l=10, r=10, t=20, b=20))
        st.plotly_chart(fig_sc, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════
# PAGE 4 — BEST PRACTICES EXPLORER
# ══════════════════════════════════════════════════════════════════════════
elif page == "📋 Best Practices Explorer":
    st.title("📋 Best Practices Explorer")
    st.markdown("*All 25 submissions from the AFU GN Best Practices Database*")
    st.markdown("---")

    # Parse principles per submission
    pcol = [c for c in df_bp.columns if "Principle(s)" in c][0]
    ucol = [c for c in df_bp.columns if "Submitting University" in c][0]
    tcol = [c for c in df_bp.columns if "Title" in c][0]
    typecol = [c for c in df_bp.columns if "Type of Activity" in c][0]

    def extract_principles(val):
        if pd.isna(val): return []
        nums = re.findall(r'Principle\s*(\d+)', str(val))
        return sorted(set(int(n) for n in nums))

    df_bp["Principles"] = df_bp[pcol].apply(extract_principles)
    df_bp["Principles_str"] = df_bp["Principles"].apply(lambda x: ", ".join(f"P{p}" for p in x))

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        principle_filter = st.multiselect(
            "Filter by Principle",
            options=list(range(1,11)),
            format_func=lambda x: f"Principle {x}",
            default=[]
        )
    with col2:
        uni_filter = st.multiselect(
            "Filter by University",
            options=sorted(df_bp[ucol].dropna().unique()),
            default=[]
        )

    df_filtered = df_bp.copy()
    if principle_filter:
        df_filtered = df_filtered[df_filtered["Principles"].apply(
            lambda ps: any(p in ps for p in principle_filter)
        )]
    if uni_filter:
        df_filtered = df_filtered[df_filtered[ucol].isin(uni_filter)]

    st.markdown(f"**Showing {len(df_filtered)} of 25 submissions**")

    # Summary metrics
    c1, c2, c3 = st.columns(3)
    with c1:
        ongoing = (df_filtered[typecol].str.contains("Ongoing", na=False)).sum()
        st.markdown(f'<div class="metric-card"><div class="metric-value">{ongoing}</div><div class="metric-label">Ongoing Activities</div></div>', unsafe_allow_html=True)
    with c2:
        onetime = (df_filtered[typecol].str.contains("One-Time", na=False)).sum()
        st.markdown(f'<div class="metric-card"><div class="metric-value">{onetime}</div><div class="metric-label">One-Time Activities</div></div>', unsafe_allow_html=True)
    with c3:
        n_unis = df_filtered[ucol].nunique()
        st.markdown(f'<div class="metric-card"><div class="metric-value">{n_unis}</div><div class="metric-label">Unique Universities</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Principle frequency for filtered set
    if len(df_filtered) > 0:
        filtered_counter = Counter()
        for ps in df_filtered["Principles"]:
            for p in ps:
                filtered_counter[p] += 1

        df_filt_p = pd.DataFrame([
            (f"P{p}", filtered_counter.get(p, 0)) for p in range(1,11)
        ], columns=["Principle","Count"])

        fig_fp = px.bar(df_filt_p, x="Principle", y="Count",
                        color="Count", color_continuous_scale="Blues",
                        text="Count", title="Principle Frequency in Selected Submissions")
        fig_fp.update_traces(textposition="outside")
        fig_fp.update_layout(height=300, showlegend=False,
                             coloraxis_showscale=False,
                             margin=dict(l=10, r=10, t=40, b=20))
        st.plotly_chart(fig_fp, use_container_width=True)

    # Cards for each submission
    st.markdown("---")
    for _, row in df_filtered.iterrows():
        with st.expander(f"📌 {row[tcol]} — *{row[ucol]}*"):
            c1, c2 = st.columns([2,1])
            with c1:
                purpose_col = [c for c in df_bp.columns if "primary purpose" in c.lower()][0]
                outcome_col = [c for c in df_bp.columns if "outcomes" in c.lower()][0]
                unique_col = [c for c in df_bp.columns if "unique" in c.lower()][0]
                st.markdown(f"**Purpose:** {row.get(purpose_col, 'N/A')}")
                st.markdown(f"**Outcomes:** {row.get(outcome_col, 'N/A')}")
                st.markdown(f"**What makes it unique:** {row.get(unique_col, 'N/A')}")
            with c2:
                duration_col = [c for c in df_bp.columns if "How long" in c][0]
                st.markdown(f"**Principles:** {row['Principles_str']}")
                st.markdown(f"**Type:** {row.get(typecol, 'N/A')}")
                st.markdown(f"**Duration:** {row.get(duration_col, 'N/A')}")
