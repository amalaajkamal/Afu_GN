import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import os
from collections import Counter

st.set_page_config(
    page_title="AFU Global Network Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Dark theme CSS for Impact Map page ─────────────────────────────────────
st.markdown("""
<style>
.impact-header {
    background: #0d1b2a;
    color: #00d4ff;
    padding: 8px 16px;
    font-size: 1.1rem;
    font-weight: 700;
    border-radius: 4px;
    margin-bottom: 8px;
}
.stat-card {
    background: #1a2744;
    border: 1px solid #2e4a8a;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 6px 0;
    text-align: center;
}
.stat-number {
    font-size: 2rem;
    font-weight: 800;
    color: #00d4ff;
}
.stat-label {
    font-size: 0.75rem;
    color: #8899bb;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.region-btn {
    background: #1a2744;
    color: #cce4ff;
    border: 1px solid #2e4a8a;
    border-radius: 4px;
    padding: 6px 10px;
    margin: 3px 0;
    width: 100%;
    text-align: left;
    font-size: 0.85rem;
    cursor: pointer;
}
.region-btn-active {
    background: #2e4a8a;
    color: #ffffff;
    border: 1px solid #00d4ff;
}
.country-item {
    color: #FF9800;
    font-size: 0.82rem;
    padding: 4px 0 4px 12px;
    border-left: 2px solid #FF9800;
    margin: 3px 0;
    cursor: pointer;
}
.section-dark {
    background: #0d1b2a;
    border-radius: 8px;
    padding: 12px;
    margin: 4px 0;
}
.overview-title {
    background: #1a2744;
    color: #ffffff;
    text-align: center;
    padding: 6px;
    border-radius: 4px;
    font-weight: 700;
    font-size: 0.9rem;
    letter-spacing: 0.1em;
    margin-bottom: 8px;
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
        ("South Korea","Asia",4,401,35.90,127.76),
        ("China","Asia",1,3167,35.86,104.19),
        ("Philippines","Asia",1,366,12.87,121.77),
        ("Hong Kong SAR","Asia",1,10,22.39,114.10),
        ("Australia","Oceania",2,43,-25.27,133.77),
        ("Brazil","South America",3,1264,-14.23,-51.92),
        ("Chile","South America",2,60,-35.67,-71.54),
    ], columns=["Country","Region","AFU_Members","Total_Universities","Latitude","Longitude"])

@st.cache_data
def load_regional_data():
    return pd.DataFrame([
        ("North America",2,23,117),
        ("Europe",13,44,22),
        ("Asia",4,48,7),
        ("Oceania",1,14,2),
        ("South America",2,12,5),
    ], columns=["Region","Countries_in_AFU","Total_Countries","AFU_Institutions"])

@st.cache_data
def load_principles_data():
    return pd.DataFrame([
        (1,"P1: Encourage participation\nof older adults",18,72.0,"Well Implemented"),
        (2,"P2: Personal & career\ndevelopment",8,32.0,"Moderately Implemented"),
        (3,"P3: Recognize educational\nneeds",7,28.0,"Moderately Implemented"),
        (4,"P4: Intergenerational\nlearning",14,56.0,"Well Implemented"),
        (5,"P5: Online access for\nolder adults",4,16.0,"Underimplemented"),
        (6,"P6: Research agenda\ninformed by aging",12,48.0,"Well Implemented"),
        (7,"P7: Student understanding\nof longevity",4,16.0,"Underimplemented"),
        (8,"P8: Health, wellness &\ncultural access",12,48.0,"Well Implemented"),
        (9,"P9: Engage retired\ncommunity",7,28.0,"Moderately Implemented"),
        (10,"P10: Dialogue with aging\norganizations",5,20.0,"Underimplemented"),
    ], columns=["Principle_Number","Short_Label","Mentions","Pct","Gap_Flag"])

@st.cache_data
def load_best_practices():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "Form_Data_Entry-Grid_view.csv")
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]
    return df

# Institution list by country
INSTITUTIONS = {
    "United States": ["University of Minnesota","University of Massachusetts Boston","Arizona State University","Duke University","Rochester Institute of Technology","University of North Carolina Wilmington","University of Michigan","Middle Tennessee State University","University of South Florida","University of New Hampshire","University of Arizona","California State University San Bernardino","California State University Fullerton","California State University Long Beach","Dominican University of California","Fielding Graduate University","Los Angeles Pierce College","Palo Alto University","San Diego State University","Santa Monica College","UCLA","UC Berkeley","University of San Francisco","University of Southern California","University of the Pacific","Colorado State University","University of Colorado Denver","University of Colorado Anschutz","University of Colorado Colorado Springs","Central Connecticut State University","Goodwin University","Quinnipiac University","University of Bridgeport","University of Connecticut","University of Hartford","Florida Atlantic University","Florida State University","Eckerd College","St. Thomas University","Georgia State University","University of North Georgia","University of Hawaii at Manoa","Northeastern Illinois University","University of Illinois Urbana-Champaign","Concordia University Chicago","Purdue University","University of Indianapolis","Wichita State University","Frontier Nursing University","Northern Kentucky University","Western Kentucky University","Franciscan Missionaries of Our Lady University","University of Maine","University of New England","Towson University","University of Maryland Baltimore","University of Maryland Baltimore County","Lasell University","UMass Amherst","UMass Dartmouth","UMass Lowell","UMass Medical School","Springfield College","William James College","Eastern Michigan University","Michigan State University","Wayne State University","University of Minnesota Duluth","University of St Thomas","St Catherine University","St Cloud State University","Mississippi State University","University of Mississippi","Missouri State University","Washington University in St Louis","University of Montana","University of Nebraska at Omaha","Fairleigh Dickinson University","Stockton University","Hofstra University","Hunter College CUNY","Ithaca College","Purchase College SUNY","Cleveland State University","Miami University","University of Akron","University of Cincinnati","University of Central Oklahoma","Portland State University","Southern Oregon University","Western Oregon University","Drexel University","Pennsylvania State University","University of Rhode Island","East Tennessee State University","Tennessee State University","University of Texas at Austin","University of Utah","University of Vermont","Virginia Commonwealth University","Shepherd University","West Virginia University","University of Wisconsin La Crosse","University of Wisconsin Green Bay","University of Wisconsin Superior"],
    "Canada": ["University of Calgary","Kwantlen Polytechnic University","UBC Okanagan","University of the Fraser Valley","Niagara College","McMaster University","Toronto Metropolitan University","Trent University","Ontario Tech University","University of Windsor","University of Manitoba"],
    "Ireland": ["Atlantic Technological University","Dublin City University","Mary Immaculate College","Munster Technological University","National College of Ireland","Royal College of Surgeons Ireland","Trinity College Dublin","University College Dublin","University of Limerick"],
    "United Kingdom": ["University of Strathclyde","Ulster University"],
    "Portugal": ["ISEG — Lisbon School of Economics","Escola Superior de Saude de Santa Maria"],
    "Spain": ["University of Murcia","Universitat Internacional de Catalunya"],
    "Croatia": ["University of Rijeka"],
    "Czech Republic": ["Masaryk University"],
    "Hungary": ["John von Neumann University"],
    "Israel": ["University of Haifa"],
    "Slovakia": ["Comenius University Bratislava"],
    "Slovenia": ["University of Maribor"],
    "Switzerland": ["University of Zurich"],
    "South Korea": ["Chosun University","Paichai University","Yonsei University","Kyung Hee University"],
    "China": ["Open University of China (Seniors University of China)"],
    "Philippines": ["University of the Philippines"],
    "Hong Kong SAR": ["Chinese University of Hong Kong"],
    "Australia": ["University of Queensland","University of the Sunshine Coast"],
    "Brazil": ["Pontifical Catholic University of Campinas","Federal University of Technology Parana","Universidade Federal de Vicosa"],
    "Chile": ["Instituto Profesional AIEP","University of Talca"],
}

REGION_COLORS = {
    "North America": "#E63946",
    "Europe": "#2196F3",
    "Asia": "#FF9800",
    "Oceania": "#9C27B0",
    "South America": "#00BCD4",
}
GAP_COLORS = {
    "Well Implemented": "#27AE60",
    "Moderately Implemented": "#F39C12",
    "Underimplemented": "#E74C3C",
}

# ── Session state ──────────────────────────────────────────────────────────
if "selected_region" not in st.session_state:
    st.session_state.selected_region = None
if "selected_country" not in st.session_state:
    st.session_state.selected_country = None

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎓 AFU GN Dashboard")
    page = st.radio("Navigate", [
        "🌍 Global Overview",
        "📐 Principle Gap Analysis",
        "🗺️ Regional Equity",
        "📋 Best Practices Explorer",
        "🌐 Impact Map",
    ])
    st.markdown("---")
    st.markdown("**Data Sources**")
    st.markdown("- AFU GN Website (June 2026)\n- AFU Best Practices Database\n- UNESCO UIS 2024\n- National HEI Registries")
    st.markdown("---")
    st.caption("Paper: *Implementation Gap Analysis of the AFU Global Network*\nGenerations at Work, DCU, Oct 2026")

df_country = load_country_data()
df_country["Penetration_Pct"] = (df_country["AFU_Members"] / df_country["Total_Universities"] * 100).round(2)
df_regional = load_regional_data()
df_regional["Countries_Missing"] = df_regional["Total_Countries"] - df_regional["Countries_in_AFU"]
df_regional["Country_Coverage_Pct"] = (df_regional["Countries_in_AFU"] / df_regional["Total_Countries"] * 100).round(1)
df_principles = load_principles_data()

# ══════════════════════════════════════════════════════════════════════════
# PAGE 1 — GLOBAL OVERVIEW
# ══════════════════════════════════════════════════════════════════════════
if page == "🌍 Global Overview":
    st.title("🌍 AFU Global Network — Implementation Gap Analysis")
    st.markdown("*Age-Friendly University Global Network • Geographic & Thematic Analysis • June 2026*")
    st.divider()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Member Institutions", "156")
    c2.metric("Countries Represented", "20")
    c3.metric("Countries Worldwide", "195")
    c4.metric("Best Practice Submissions", "25")
    c5.metric("Submission Participation Rate", "11%")

    st.divider()
    st.subheader("🗺️ Member Institutions by Country")

    fig_map = px.scatter_geo(
        df_country, lat="Latitude", lon="Longitude",
        size="AFU_Members", color="Region",
        hover_name="Country",
        hover_data={"AFU_Members": True, "Penetration_Pct": True,
                    "Latitude": False, "Longitude": False},
        color_discrete_map=REGION_COLORS,
        size_max=50, projection="natural earth",
    )
    fig_map.update_layout(
        height=500, margin=dict(l=0, r=0, t=10, b=0),
        geo=dict(showframe=False, showcoastlines=True, coastlinecolor="#FFFFFF",
                 showland=True, landcolor="#A8D5A2", showocean=True, oceancolor="#5BA4CF",
                 showlakes=True, lakecolor="#7EC8E3", showcountries=True,
                 countrycolor="#FFFFFF", countrywidth=0.8),
        legend=dict(orientation="h", y=-0.05, font=dict(size=12)),
    )
    st.plotly_chart(fig_map, use_container_width=True)
    st.info("💡 **Key Finding:** North America accounts for **77% of all AFU member institutions** (117/156), with the USA alone representing **70%** (106/156). The network spans 5 official regions across 20 countries.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Regional Share of Institutions")
        fig_donut = px.pie(df_regional, values="AFU_Institutions", names="Region",
                           color="Region", color_discrete_map=REGION_COLORS, hole=0.45)
        fig_donut.update_traces(textinfo="percent+label", textposition="outside")
        fig_donut.update_layout(height=380, showlegend=False, margin=dict(l=20,r=20,t=20,b=20))
        st.plotly_chart(fig_donut, use_container_width=True)
    with col2:
        st.subheader("Institutions per Region")
        fig_bar = px.bar(df_regional.sort_values("AFU_Institutions"),
                         x="AFU_Institutions", y="Region",
                         color="Region", color_discrete_map=REGION_COLORS,
                         orientation="h", text="AFU_Institutions")
        fig_bar.update_traces(textposition="outside")
        fig_bar.update_layout(height=380, showlegend=False,
                              xaxis_title="Number of Institutions", yaxis_title="",
                              margin=dict(l=10,r=40,t=20,b=20))
        st.plotly_chart(fig_bar, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════
# PAGE 2 — PRINCIPLE GAP ANALYSIS
# ══════════════════════════════════════════════════════════════════════════
elif page == "📐 Principle Gap Analysis":
    st.title("📐 AFU Principle Implementation Gap Analysis")
    st.markdown("*Based on 25 Best Practice submissions from 17 institutions*")
    st.divider()

    c1, c2, c3 = st.columns(3)
    well = df_principles[df_principles["Gap_Flag"]=="Well Implemented"].shape[0]
    mod  = df_principles[df_principles["Gap_Flag"]=="Moderately Implemented"].shape[0]
    unde = df_principles[df_principles["Gap_Flag"]=="Underimplemented"].shape[0]
    c1.metric("✅ Well Implemented", f"{well} principles")
    c2.metric("⚠️ Moderately Implemented", f"{mod} principles")
    c3.metric("🔴 Underimplemented", f"{unde} principles")

    st.divider()
    st.subheader("Principle Citation Frequency (% of 25 submissions)")
    fig_p = px.bar(df_principles.sort_values("Pct"),
                   x="Pct", y="Short_Label", color="Gap_Flag",
                   color_discrete_map=GAP_COLORS, orientation="h", text="Pct",
                   labels={"Pct": "% of Submissions", "Short_Label": ""})
    fig_p.update_traces(texttemplate="%{text}%", textposition="outside")
    fig_p.add_vline(x=50, line_dash="dot", line_color="gray",
                    annotation_text="50% threshold", annotation_position="top")
    fig_p.update_layout(height=480, xaxis=dict(range=[0,85]),
                        legend_title="Implementation Status",
                        margin=dict(l=10,r=60,t=20,b=20),
                        legend=dict(orientation="h", y=-0.12))
    st.plotly_chart(fig_p, use_container_width=True)
    st.info("💡 **Key Finding:** Principle 5 and Principle 7 are cited in only **16% of submissions** — the lowest of all 10 principles.")

    st.divider()
    st.subheader("Who Do Best Practice Activities Target?")
    try:
        df_bp = load_best_practices()
        audience_col = [c for c in df_bp.columns if "aimed at" in c.lower()][0]
        aud_counter = Counter()
        for val in df_bp[audience_col].dropna():
            for a in val.split(","):
                aud_counter[a.strip()] += 1
        df_aud = pd.DataFrame(aud_counter.items(), columns=["Audience","Count"]).sort_values("Count", ascending=True)
        fig_aud = px.bar(df_aud, x="Count", y="Audience", orientation="h",
                         color="Count", color_continuous_scale="Blues", text="Count")
        fig_aud.update_traces(textposition="outside")
        fig_aud.update_layout(height=350, showlegend=False, coloraxis_showscale=False,
                              margin=dict(l=10,r=40,t=20,b=20))
        st.plotly_chart(fig_aud, use_container_width=True)
        st.warning("⚠️ Despite Principle 7 calling for increased student understanding of aging, dedicated student-only programming is rare.")
    except Exception:
        st.warning("Upload Form_Data_Entry-Grid_view.csv to the repo to enable audience analysis.")

# ══════════════════════════════════════════════════════════════════════════
# PAGE 3 — REGIONAL EQUITY
# ══════════════════════════════════════════════════════════════════════════
elif page == "🗺️ Regional Equity":
    st.title("🗺️ Geographic Equity & Penetration Analysis")
    st.markdown("*Country coverage gaps and institutional adoption rates across AFU regions*")
    st.divider()

    tab1, tab2 = st.tabs(["Country Coverage Gap", "Penetration Rate by Country"])
    with tab1:
        st.subheader("Countries Represented vs. Total Countries Per Region")
        df_melt = df_regional.melt(id_vars="Region",
                                   value_vars=["Countries_in_AFU","Countries_Missing"],
                                   var_name="Type", value_name="Count")
        df_melt["Type"] = df_melt["Type"].map({"Countries_in_AFU":"In AFU GN","Countries_Missing":"Not in AFU GN"})
        fig_cov = px.bar(df_melt, x="Count", y="Region", color="Type", orientation="h",
                         color_discrete_map={"In AFU GN":"#2E6DA4","Not in AFU GN":"#D5E8F5"},
                         barmode="stack", text="Count")
        fig_cov.update_traces(textposition="inside")
        fig_cov.update_layout(height=400, xaxis_title="Number of Countries",
                              margin=dict(l=10,r=20,t=20,b=20),
                              legend=dict(orientation="h", y=-0.12))
        st.plotly_chart(fig_cov, use_container_width=True)
        st.info("💡 **Asia:** 48 countries, only 4 represented (8.3%). **Oceania:** 14 countries, only Australia represented (7.1% coverage).")
        df_display = df_regional[["Region","Countries_in_AFU","Total_Countries","Countries_Missing","Country_Coverage_Pct"]].copy()
        df_display.columns = ["Region","In AFU GN","Total Countries","Not Represented","Coverage %"]
        st.dataframe(df_display, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("AFU Adoption as % of National University System")
        fig_pen = px.bar(df_country.sort_values("Penetration_Pct", ascending=False),
                         x="Country", y="Penetration_Pct", color="Region",
                         color_discrete_map=REGION_COLORS,
                         text=df_country.sort_values("Penetration_Pct", ascending=False)["Penetration_Pct"].apply(lambda x: f"{x}%"),
                         hover_data={"AFU_Members": True, "Total_Universities": True})
        fig_pen.update_traces(textposition="outside", textfont_size=10)
        fig_pen.update_layout(height=500, xaxis_tickangle=-45,
                              yaxis_title="Penetration Rate (%)", xaxis_title="",
                              margin=dict(l=10,r=10,t=20,b=140))
        st.plotly_chart(fig_pen, use_container_width=True)
        st.info("💡 **Ireland (34.6%)** highest penetration. **China (0.03%)** lowest.")
        st.subheader("AFU Members vs. National University System Size")
        fig_sc = px.scatter(df_country, x="Total_Universities", y="AFU_Members",
                            color="Region", size="Penetration_Pct", hover_name="Country",
                            color_discrete_map=REGION_COLORS, log_x=True, size_max=30,
                            labels={"Total_Universities":"Total Universities (log scale)",
                                    "AFU_Members":"AFU Member Institutions"})
        fig_sc.update_layout(height=420, margin=dict(l=10,r=10,t=20,b=20))
        st.plotly_chart(fig_sc, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════
# PAGE 4 — BEST PRACTICES EXPLORER
# ══════════════════════════════════════════════════════════════════════════
elif page == "📋 Best Practices Explorer":
    st.title("📋 Best Practices Explorer")
    st.markdown("*All 25 submissions from the AFU GN Best Practices Database*")
    st.divider()
    try:
        df_bp = load_best_practices()
        pcol    = [c for c in df_bp.columns if "Principle(s)" in c][0]
        ucol    = [c for c in df_bp.columns if "Submitting University" in c][0]
        tcol    = [c for c in df_bp.columns if "Title" in c][0]
        typecol = [c for c in df_bp.columns if "Type of Activity" in c][0]

        def extract_principles(val):
            if pd.isna(val): return []
            nums = re.findall(r'Principle\s*(\d+)', str(val))
            return sorted(set(int(n) for n in nums))

        df_bp["Principles"] = df_bp[pcol].apply(extract_principles)
        df_bp["Principles_str"] = df_bp["Principles"].apply(lambda x: ", ".join(f"P{p}" for p in x))

        col1, col2 = st.columns(2)
        with col1:
            principle_filter = st.multiselect("Filter by Principle",
                options=list(range(1,11)), format_func=lambda x: f"Principle {x}", default=[])
        with col2:
            uni_filter = st.multiselect("Filter by University",
                options=sorted(df_bp[ucol].dropna().unique()), default=[])

        df_filtered = df_bp.copy()
        if principle_filter:
            df_filtered = df_filtered[df_filtered["Principles"].apply(
                lambda ps: any(p in ps for p in principle_filter))]
        if uni_filter:
            df_filtered = df_filtered[df_filtered[ucol].isin(uni_filter)]

        st.markdown(f"**Showing {len(df_filtered)} of 25 submissions**")
        c1, c2, c3 = st.columns(3)
        c1.metric("Ongoing Activities", int((df_filtered[typecol].str.contains("Ongoing", na=False)).sum()))
        c2.metric("One-Time Activities", int((df_filtered[typecol].str.contains("One-Time", na=False)).sum()))
        c3.metric("Unique Universities", int(df_filtered[ucol].nunique()))
        st.divider()

        if len(df_filtered) > 0:
            filtered_counter = Counter()
            for ps in df_filtered["Principles"]:
                for p in ps:
                    filtered_counter[p] += 1
            df_filt_p = pd.DataFrame([(f"P{p}", filtered_counter.get(p,0)) for p in range(1,11)],
                                     columns=["Principle","Count"])
            fig_fp = px.bar(df_filt_p, x="Principle", y="Count",
                            color="Count", color_continuous_scale="Blues",
                            text="Count", title="Principle Frequency in Selected Submissions")
            fig_fp.update_traces(textposition="outside")
            fig_fp.update_layout(height=300, showlegend=False,
                                 coloraxis_showscale=False, margin=dict(l=10,r=10,t=40,b=20))
            st.plotly_chart(fig_fp, use_container_width=True)

        purpose_col = [c for c in df_bp.columns if "primary purpose" in c.lower()][0]
        outcome_col = [c for c in df_bp.columns if "outcomes" in c.lower()][0]
        unique_col  = [c for c in df_bp.columns if "unique" in c.lower()][0]
        duration_col= [c for c in df_bp.columns if "How long" in c][0]

        for _, row in df_filtered.iterrows():
            with st.expander(f"📌 {row[tcol]} — *{row[ucol]}*"):
                c1, c2 = st.columns([2,1])
                with c1:
                    st.markdown(f"**Purpose:** {row.get(purpose_col,'N/A')}")
                    st.markdown(f"**Outcomes:** {row.get(outcome_col,'N/A')}")
                    st.markdown(f"**What makes it unique:** {row.get(unique_col,'N/A')}")
                with c2:
                    st.markdown(f"**Principles:** {row['Principles_str']}")
                    st.markdown(f"**Type:** {row.get(typecol,'N/A')}")
                    st.markdown(f"**Duration:** {row.get(duration_col,'N/A')}")

    except FileNotFoundError:
        st.error("⚠️ Form_Data_Entry-Grid_view.csv not found.")
    except Exception as e:
        st.error(f"Error: {e}")

# ══════════════════════════════════════════════════════════════════════════
# PAGE 5 — IMPACT MAP (GeoPulse Style)
# ══════════════════════════════════════════════════════════════════════════
elif page == "🌐 Impact Map":

    # Minimal top header
    st.markdown("""
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:4px;">
        <span style="color:#4FC3F7; font-size:1.05rem; font-weight:800; letter-spacing:0.05em;">🌐 AFU GLOBAL NETWORK — IMPACT MAP</span>
        <span style="color:#546E7A; font-size:0.78rem;">| Select a region below the map, then a country from the list</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Region selector state ──────────────────────────────────────────────
    regions_list = ["All Regions", "North America", "Europe", "Asia", "Oceania", "South America"]
    if "selected_region" not in st.session_state:
        st.session_state.selected_region = "All Regions"
    if "selected_country" not in st.session_state:
        st.session_state.selected_country = None

    sel_region = st.session_state.selected_region
    sel_country = st.session_state.selected_country

    # ── Filter data ────────────────────────────────────────────────────────
    if sel_country:
        map_df = df_country.copy()
        map_df["dot_opacity"] = map_df["Country"].apply(lambda x: 1.0 if x == sel_country else 0.15)
        map_df["dot_size"] = map_df["AFU_Members"].apply(lambda x: max(6, min(35, x/2.8)))
    elif sel_region != "All Regions":
        map_df = df_country.copy()
        map_df["dot_opacity"] = map_df["Region"].apply(lambda x: 1.0 if x == sel_region else 0.15)
        map_df["dot_size"] = map_df["AFU_Members"].apply(lambda x: max(6, min(35, x/2.8)))
    else:
        map_df = df_country.copy()
        map_df["dot_opacity"] = 1.0
        map_df["dot_size"] = map_df["AFU_Members"].apply(lambda x: max(6, min(35, x/2.8)))

    # ── Map ────────────────────────────────────────────────────────────────
    fig_impact = go.Figure()

    for region in df_country["Region"].unique():
        rdf = map_df[map_df["Region"] == region]
        color = REGION_COLORS.get(region, "#888888")
        opacity = float(rdf["dot_opacity"].mean()) if len(rdf) > 0 else 1.0

        # Glow effect — outer ring
        fig_impact.add_trace(go.Scattergeo(
            lat=rdf["Latitude"], lon=rdf["Longitude"],
            mode="markers", showlegend=False,
            marker=dict(
                size=rdf["dot_size"] * 1.8,
                color=color,
                opacity=opacity * 0.25,
                line=dict(width=0),
            ),
            hoverinfo="skip",
        ))

        # Main dot
        fig_impact.add_trace(go.Scattergeo(
            lat=rdf["Latitude"], lon=rdf["Longitude"],
            mode="markers+text",
            name=region,
            marker=dict(
                size=rdf["dot_size"],
                color=color,
                opacity=opacity,
                line=dict(width=1.5, color="white"),
            ),
            text=rdf["AFU_Members"].astype(str),
            textfont=dict(size=8, color="white", family="Arial Black"),
            textposition="middle center",
            customdata=rdf[["Country","AFU_Members","Penetration_Pct","Total_Universities"]].values,
            hovertemplate="<b>%{customdata[0]}</b><br>AFU Members: %{customdata[1]}<br>Penetration: %{customdata[2]}%<br>Total Universities: %{customdata[3]}<extra></extra>",
        ))

    fig_impact.update_layout(
        height=430,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="#050d1a",
        plot_bgcolor="#050d1a",
        geo=dict(
            showframe=False,
            showcoastlines=True, coastlinecolor="#0d2137",
            showland=True, landcolor="#0a1628",
            showocean=True, oceancolor="#050d1a",
            showlakes=False,
            showcountries=True, countrycolor="#0d2137",
            countrywidth=0.4,
            bgcolor="#050d1a",
            projection_type="natural earth",
            lataxis=dict(range=[-55, 80]),
            lonaxis=dict(range=[-170, 180]),
        ),
        legend=dict(
            orientation="h", y=1.02, x=0.5, xanchor="center",
            font=dict(color="#90A4AE", size=10),
            bgcolor="rgba(0,0,0,0)",
            itemsizing="constant",
        ),
        font=dict(color="#90A4AE"),
    )

    # ── Layout: map + right stats panel ───────────────────────────────────
    map_col, stats_col = st.columns([3.2, 1])

    with map_col:
        st.plotly_chart(fig_impact, use_container_width=True, config={"displayModeBar": False})

        # ── Region tabs at bottom (GeoPulse style) ────────────────────────
        region_counts = {
            "All Regions": 156,
            "North America": 117,
            "Europe": 22,
            "Asia": 7,
            "Oceania": 2,
            "South America": 5,
        }
        tab_colors = {
            "All Regions": "#4FC3F7",
            "North America": "#E63946",
            "Europe": "#2196F3",
            "Asia": "#FF9800",
            "Oceania": "#9C27B0",
            "South America": "#00BCD4",
        }

        st.markdown('<div style="display:flex; gap:6px; flex-wrap:wrap; margin-top:-12px;">', unsafe_allow_html=True)
        cols = st.columns(len(regions_list))
        for i, region in enumerate(regions_list):
            with cols[i]:
                color = tab_colors.get(region, "#888")
                count = region_counts.get(region, 0)
                is_active = sel_region == region
                bg = f"background:{color}22; border:1.5px solid {color};"
                txt_color = color
                if is_active:
                    bg = f"background:{color}44; border:2px solid {color};"
                label = f"{region} {count}"
                if st.button(f"{region} {count}", key=f"tab_{region}", use_container_width=True):
                    st.session_state.selected_region = region
                    st.session_state.selected_country = None
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Country list for selected region
        if sel_region != "All Regions":
            region_countries = df_country[df_country["Region"] == sel_region].sort_values("AFU_Members", ascending=False)
            st.markdown(f"""
            <div style="display:flex; gap:8px; flex-wrap:wrap; margin-top:8px; padding:8px;
                        background:#0a1628; border-radius:6px; border:1px solid #0d2137;">
                <span style="color:#546E7A; font-size:0.72rem; width:100%; margin-bottom:4px;">
                    COUNTRIES IN {sel_region.upper()}
                </span>
            """, unsafe_allow_html=True)
            btn_cols = st.columns(min(len(region_countries), 4))
            for i, (_, row) in enumerate(region_countries.iterrows()):
                with btn_cols[i % min(len(region_countries), 4)]:
                    color = REGION_COLORS.get(sel_region, "#888")
                    is_sel = sel_country == row["Country"]
                    prefix = "▶ " if is_sel else ""
                    if st.button(f"{prefix}{row['Country']} ({int(row['AFU_Members'])})",
                                key=f"cty2_{row['Country']}", use_container_width=True):
                        if st.session_state.selected_country == row["Country"]:
                            st.session_state.selected_country = None
                        else:
                            st.session_state.selected_country = row["Country"]
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    with stats_col:
        st.markdown("""
        <style>
        .gp-card {
            background:#0a1628;
            border:1px solid #0d2137;
            border-radius:6px;
            padding:10px 12px;
            margin:4px 0;
            text-align:center;
        }
        .gp-num { font-size:1.7rem; font-weight:800; color:#4FC3F7; }
        .gp-lbl { font-size:0.68rem; color:#546E7A; text-transform:uppercase; letter-spacing:0.08em; }
        .gp-title { background:#0d2137; color:#4FC3F7; text-align:center; padding:6px;
                    border-radius:4px; font-weight:700; font-size:0.8rem;
                    letter-spacing:0.1em; margin-bottom:6px; }
        .inst-item { color:#B0BEC5; font-size:0.7rem; padding:3px 0 3px 8px;
                     border-left:2px solid #1565C0; margin:2px 0; }
        </style>
        """, unsafe_allow_html=True)

        if sel_country:
            cdata = df_country[df_country["Country"] == sel_country].iloc[0]
            institutions = INSTITUTIONS.get(sel_country, [])
            pen_color = "#00E676" if cdata["Penetration_Pct"] > 5 else "#FF9800" if cdata["Penetration_Pct"] > 1 else "#EF5350"

            st.markdown(f'<div class="gp-title">{sel_country.upper()}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="gp-card"><div class="gp-num" style="color:{REGION_COLORS.get(cdata["Region"],"#4FC3F7")}">{int(cdata["AFU_Members"])}</div><div class="gp-lbl">AFU Members</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="gp-card"><div class="gp-num" style="color:{pen_color}">{cdata["Penetration_Pct"]}%</div><div class="gp-lbl">Penetration Rate</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="gp-card"><div class="gp-num" style="font-size:1.1rem;">{int(cdata["Total_Universities"]):,}</div><div class="gp-lbl">Total Universities</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="gp-card"><div class="gp-num" style="font-size:0.9rem; color:#90A4AE;">{cdata["Region"]}</div><div class="gp-lbl">Region</div></div>', unsafe_allow_html=True)

            if institutions:
                st.markdown(f'<div style="color:#546E7A; font-size:0.7rem; margin:8px 0 4px; font-weight:700;">INSTITUTIONS ({len(institutions)})</div>', unsafe_allow_html=True)
                inst_html = "".join([f'<div class="inst-item">• {inst}</div>' for inst in institutions])
                st.markdown(f'<div style="max-height:280px; overflow-y:auto; background:#050d1a; border-radius:4px; padding:6px;">{inst_html}</div>', unsafe_allow_html=True)

        elif sel_region != "All Regions":
            rdata = df_regional[df_regional["Region"] == sel_region]
            rcountries = df_country[df_country["Region"] == sel_region]
            total_inst = int(rdata["AFU_Institutions"].values[0]) if len(rdata) > 0 else 0
            countries_in = int(rdata["Countries_in_AFU"].values[0]) if len(rdata) > 0 else 0
            total_c = int(rdata["Total_Countries"].values[0]) if len(rdata) > 0 else 0
            coverage = round(countries_in/total_c*100, 1) if total_c > 0 else 0

            st.markdown(f'<div class="gp-title">{sel_region.upper()}</div>', unsafe_allow_html=True)
            color = REGION_COLORS.get(sel_region, "#4FC3F7")
            st.markdown(f'<div class="gp-card"><div class="gp-num" style="color:{color}">{total_inst}</div><div class="gp-lbl">Institutions</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="gp-card"><div class="gp-num">{countries_in} / {total_c}</div><div class="gp-lbl">Countries Represented</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="gp-card"><div class="gp-num">{coverage}%</div><div class="gp-lbl">Country Coverage</div></div>', unsafe_allow_html=True)

            st.markdown('<div style="color:#546E7A; font-size:0.7rem; margin:8px 0 4px; font-weight:700;">COUNTRIES</div>', unsafe_allow_html=True)
            for _, row in rcountries.sort_values("AFU_Members", ascending=False).iterrows():
                pen = row["Penetration_Pct"]
                pen_color = "#00E676" if pen > 5 else "#FF9800" if pen > 1 else "#EF5350"
                st.markdown(f'<div style="background:#0a1628; border:1px solid #0d2137; border-radius:4px; padding:6px 8px; margin:3px 0; display:flex; justify-content:space-between;"><span style="color:#B0BEC5; font-size:0.75rem;">● {row["Country"]}</span><span style="color:{pen_color}; font-size:0.72rem;">{int(row["AFU_Members"])} ({pen}%)</span></div>', unsafe_allow_html=True)

        else:
            st.markdown('<div class="gp-title">GLOBAL OVERVIEW</div>', unsafe_allow_html=True)
            stats = [("156","Institutions","#4FC3F7"),("20","Countries","#4FC3F7"),
                     ("5","Regions","#4FC3F7"),("11%","Submission Rate","#FF9800"),
                     ("77%","N.America Share","#EF5350"),("16%","P5 & P7 Rate","#EF5350")]
            for val, lbl, col in stats:
                st.markdown(f'<div class="gp-card"><div class="gp-num" style="color:{col}">{val}</div><div class="gp-lbl">{lbl}</div></div>', unsafe_allow_html=True)
