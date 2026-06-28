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
    st.markdown("## 🎓 AFU GN Dashboard")
    page = st.radio("Navigate", [
        "🌍 Global Overview",
        "📐 Principle Gap Analysis",
        "🗺️ Regional Equity",
        "📋 Best Practices Explorer",
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
    c1.metric("Member Institutions", "153")
    c2.metric("Countries Represented", "21")
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
        height=460, margin=dict(l=0, r=0, t=10, b=0),
        geo=dict(showframe=False, showcoastlines=True,
                 coastlinecolor="#CCCCCC", showland=True,
                 landcolor="#F0F0F0", showocean=True, oceancolor="#D6EAF8"),
        legend=dict(orientation="h", y=-0.05)
    )
    st.plotly_chart(fig_map, use_container_width=True)

    st.info("💡 **Key Finding:** North America accounts for **77% of all AFU member institutions** (117/153), with the USA alone representing **70%** (106/153). Africa has no official members despite Ghana actively submitting best practices.")

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

    fig_p = px.bar(
        df_principles.sort_values("Pct"),
        x="Pct", y="Short_Label",
        color="Gap_Flag", color_discrete_map=GAP_COLORS,
        orientation="h", text="Pct",
        labels={"Pct": "% of Submissions", "Short_Label": ""},
    )
    fig_p.update_traces(texttemplate="%{text}%", textposition="outside")
    fig_p.add_vline(x=50, line_dash="dot", line_color="gray",
                    annotation_text="50% threshold", annotation_position="top")
    fig_p.update_layout(height=480, xaxis=dict(range=[0,85]),
                        legend_title="Implementation Status",
                        margin=dict(l=10,r=60,t=20,b=20),
                        legend=dict(orientation="h", y=-0.12))
    st.plotly_chart(fig_p, use_container_width=True)

    st.info("💡 **Key Finding:** Principle 5 (Online access for older adults) and Principle 7 (Student understanding of the longevity dividend) are cited in only **16% of submissions** — the lowest of all 10 principles. These represent the most critical implementation gaps.")

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
        fig_aud.update_layout(height=350, showlegend=False,
                              coloraxis_showscale=False,
                              margin=dict(l=10,r=40,t=20,b=20))
        st.plotly_chart(fig_aud, use_container_width=True)
        st.warning("⚠️ Despite Principle 7 calling for increased *student* understanding of aging, dedicated student-only programming is rare, reinforcing the P7 implementation gap.")
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
        df_melt = df_regional.melt(
            id_vars="Region",
            value_vars=["Countries_in_AFU","Countries_Missing"],
            var_name="Type", value_name="Count"
        )
        df_melt["Type"] = df_melt["Type"].map({
            "Countries_in_AFU": "In AFU GN",
            "Countries_Missing": "Not in AFU GN"
        })
        fig_cov = px.bar(df_melt, x="Count", y="Region", color="Type",
                         orientation="h",
                         color_discrete_map={"In AFU GN":"#2E6DA4","Not in AFU GN":"#D5E8F5"},
                         barmode="stack", text="Count")
        fig_cov.update_traces(textposition="inside")
        fig_cov.update_layout(height=400, xaxis_title="Number of Countries",
                              margin=dict(l=10,r=20,t=20,b=20),
                              legend=dict(orientation="h", y=-0.12))
        st.plotly_chart(fig_cov, use_container_width=True)

        st.info("💡 **Africa:** 54 countries, 0 official members — yet Ghana actively participates in best practices without formal membership. **Asia:** 48 countries, only 4 represented (8.3%).")

        df_display = df_regional[["Region","Countries_in_AFU","Total_Countries","Countries_Missing","Country_Coverage_Pct"]].copy()
        df_display.columns = ["Region","In AFU GN","Total Countries","Not Represented","Coverage %"]
        st.dataframe(df_display, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("AFU Adoption as % of National University System")
        st.markdown("*How many of a country's universities have joined AFU GN?*")

        fig_pen = px.bar(
            df_country.sort_values("Penetration_Pct", ascending=False),
            x="Country", y="Penetration_Pct",
            color="Region", color_discrete_map=REGION_COLORS,
            text=df_country.sort_values("Penetration_Pct", ascending=False)["Penetration_Pct"].apply(lambda x: f"{x}%"),
            hover_data={"AFU_Members": True, "Total_Universities": True}
        )
        fig_pen.update_traces(textposition="outside", textfont_size=10)
        fig_pen.update_layout(height=500, xaxis_tickangle=-45,
                              yaxis_title="Penetration Rate (%)", xaxis_title="",
                              margin=dict(l=10,r=10,t=20,b=140))
        st.plotly_chart(fig_pen, use_container_width=True)

        st.info("💡 **Ireland (34.6%)** has the highest penetration — a founder effect since DCU established AFU in 2012. **China (0.03%)**, with 3,167 universities, has just one AFU member — the lowest penetration rate of any represented country.")

        st.subheader("AFU Members vs. National University System Size")
        fig_sc = px.scatter(df_country, x="Total_Universities", y="AFU_Members",
                            color="Region", size="Penetration_Pct",
                            hover_name="Country", color_discrete_map=REGION_COLORS,
                            log_x=True, size_max=30,
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
        st.error("⚠️ Form_Data_Entry-Grid_view.csv not found. Please upload it to the GitHub repository.")
    except Exception as e:
        st.error(f"Error loading best practices data: {e}")
