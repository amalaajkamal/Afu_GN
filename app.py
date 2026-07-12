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
        ("United States","North America",105,37.09,-95.71),
        ("Canada","North America",12,56.13,-106.35),
        ("Ireland","Europe",9,53.41,-8.24),
        ("United Kingdom","Europe",2,55.37,-3.43),
        ("Portugal","Europe",2,39.39,-8.22),
        ("Spain","Europe",2,40.46,-3.74),
        ("Croatia","Europe",1,45.10,15.20),
        ("Czech Republic","Europe",1,49.81,15.47),
        ("Hungary","Europe",1,47.16,19.50),
        ("Israel","Europe",1,31.04,34.85),
        ("Slovakia","Europe",1,48.66,19.69),
        ("Slovenia","Europe",1,46.15,14.99),
        ("Switzerland","Europe",1,46.81,8.22),
        ("South Korea","Asia",3,35.90,127.76),
        ("Turkey","Asia",1,39.92,32.85),
        ("China","Asia",1,35.86,104.19),
        ("Philippines","Asia",1,12.87,121.77),
        ("Hong Kong SAR","Asia",1,22.39,114.10),
        ("Australia","Oceania",2,-25.27,133.77),
        ("Brazil","South America",3,-14.23,-51.92),
        ("Chile","South America",2,-35.67,-71.54),
    ], columns=["Country","Region","AFU_Members","Latitude","Longitude"])

@st.cache_data
def load_regional_data():
    return pd.DataFrame([
        ("North America",2,23,117),
        ("Europe",13,44,22),
        ("Asia",5,48,7),
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
    "Canada": ["University of Calgary","Kwantlen Polytechnic University","University of British Columbia","UBC Okanagan","University of the Fraser Valley","Niagara College","McMaster University","Toronto Metropolitan University","Trent University","Ontario Tech University (UOIT)","University of Windsor","University of Manitoba"],
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
    "South Korea": ["Chosun University","Paichai University","Yonsei University"],
    "China": ["Open University of China (Seniors University of China)"],
    "Philippines": ["University of the Philippines"],
    "Hong Kong SAR": ["Chinese University of Hong Kong"],
    "Turkey": ["Istanbul Nişantaşı University"],
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
df_regional = load_regional_data()
df_regional["Countries_Missing"] = df_regional["Total_Countries"] - df_regional["Countries_in_AFU"]
df_regional["Country_Coverage_Pct"] = (df_regional["Countries_in_AFU"] / df_regional["Total_Countries"] * 100).round(1)
df_principles = load_principles_data()

# ══════════════════════════════════════════════════════════════════════════
# PAGE 1 — GLOBAL OVERVIEW
# ══════════════════════════════════════════════════════════════════════════
if page == "🌍 Global Overview":

    st.markdown("""
    <div style="background:#050d1a; padding:8px 0 4px 0;">
        <span style="color:#4FC3F7; font-size:1.15rem; font-weight:800; letter-spacing:0.06em;">
            🌍 AFU GLOBAL NETWORK — IMPLEMENTATION GAP ANALYSIS
        </span>
        <span style="color:#37474F; font-size:0.8rem; margin-left:12px;">
            Geographic & Thematic Analysis • June 2026
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="display:flex; gap:8px; margin:6px 0;">
        <div style="background:#0a1628; border:1px solid #0d2137; border-radius:6px; padding:8px 16px; flex:1; text-align:center; border-top:2px solid #4FC3F7;">
            <div style="color:#4FC3F7; font-size:1.5rem; font-weight:800;">153</div>
            <div style="color:#546E7A; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.08em;">Member Institutions</div>
        </div>
        <div style="background:#0a1628; border:1px solid #0d2137; border-radius:6px; padding:8px 16px; flex:1; text-align:center; border-top:2px solid #E63946;">
            <div style="color:#E63946; font-size:1.5rem; font-weight:800;">77%</div>
            <div style="color:#546E7A; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.08em;">North America Share</div>
        </div>
        <div style="background:#0a1628; border:1px solid #0d2137; border-radius:6px; padding:8px 16px; flex:1; text-align:center; border-top:2px solid #27AE60;">
            <div style="color:#27AE60; font-size:1.5rem; font-weight:800;">21</div>
            <div style="color:#546E7A; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.08em;">Countries</div>
        </div>
        <div style="background:#0a1628; border:1px solid #0d2137; border-radius:6px; padding:8px 16px; flex:1; text-align:center; border-top:2px solid #FF9800;">
            <div style="color:#FF9800; font-size:1.5rem; font-weight:800;">25</div>
            <div style="color:#546E7A; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.08em;">Best Practices</div>
        </div>
        <div style="background:#0a1628; border:1px solid #0d2137; border-radius:6px; padding:8px 16px; flex:1; text-align:center; border-top:2px solid #EF5350;">
            <div style="color:#EF5350; font-size:1.5rem; font-weight:800;">16%</div>
            <div style="color:#546E7A; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.08em;">P5 & P7 Rate</div>
        </div>
        <div style="background:#0a1628; border:1px solid #0d2137; border-radius:6px; padding:8px 16px; flex:1; text-align:center; border-top:2px solid #9C27B0;">
            <div style="color:#9C27B0; font-size:1.5rem; font-weight:800;">11%</div>
            <div style="color:#546E7A; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.08em;">Submission Rate</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if "ov_region" not in st.session_state:
        st.session_state.ov_region = "Global View"

    region_tabs = {
        "Global View":   (153, "#4FC3F7"),
        "North America": (117, "#E63946"),
        "Europe":        (22,  "#2196F3"),
        "Asia":          (7,   "#FF9800"),
        "South America": (5,   "#00BCD4"),
        "Oceania":       (2,   "#9C27B0"),
    }

    sel = st.session_state.ov_region

    if sel == "Global View":
        map_df = df_country.copy()
        map_df["opacity"] = 1.0
    else:
        map_df = df_country.copy()
        map_df["opacity"] = map_df["Region"].apply(lambda x: 1.0 if x == sel else 0.12)

    fig_ov = go.Figure()

    for region in df_country["Region"].unique():
        rdf = map_df[map_df["Region"] == region]
        color = REGION_COLORS.get(region, "#888")
        opacity = float(rdf["opacity"].mean()) if len(rdf) > 0 else 1.0

        fig_ov.add_trace(go.Scattergeo(
            lat=rdf["Latitude"], lon=rdf["Longitude"],
            mode="markers", showlegend=False,
            marker=dict(size=rdf["AFU_Members"].apply(lambda x: max(10, min(55, x/2.2))),
                        color=color, opacity=opacity*0.2, line=dict(width=0)),
            hoverinfo="skip",
        ))

        fig_ov.add_trace(go.Scattergeo(
            lat=rdf["Latitude"], lon=rdf["Longitude"],
            mode="markers+text", name=region,
            marker=dict(size=rdf["AFU_Members"].apply(lambda x: max(8, min(45, x/2.5))),
                        color=color, opacity=opacity,
                        line=dict(width=1.5, color="rgba(255,255,255,0.6)")),
            text=rdf["AFU_Members"].astype(str),
            textfont=dict(size=7, color="white", family="Arial Black"),
            textposition="middle center",
            customdata=rdf[["Country","AFU_Members"]].values,
            hovertemplate="<b>%{customdata[0]}</b><br>AFU Members: %{customdata[1]}<extra></extra>",
        ))

    region_bounds = {
        "Global View":   {"lat": [-55, 80],  "lon": [-170, 180]},
        "North America": {"lat": [15, 75],   "lon": [-170, -50]},
        "Europe":        {"lat": [35, 72],   "lon": [-15, 45]},
        "Asia":          {"lat": [-10, 55],  "lon": [70, 150]},
        "South America": {"lat": [-60, 15],  "lon": [-85, -30]},
        "Oceania":       {"lat": [-50, 5],   "lon": [110, 180]},
    }
    bounds = region_bounds.get(sel, region_bounds["Global View"])

    # Dark theme colors per region
    region_themes = {
        "Global View":   {"land": "#1a1a2e", "ocean": "#050d1a", "coast": "#2a2a4a", "country": "#2a2a4a", "bg": "#050d1a"},
        "North America": {"land": "#0f3460", "ocean": "#050d1a", "coast": "#E63946", "country": "#533483", "bg": "#050d1a"},
        "Europe":        {"land": "#16213e", "ocean": "#050d1a", "coast": "#2196F3", "country": "#1a3a6e", "bg": "#050d1a"},
        "Asia":          {"land": "#2d1b00", "ocean": "#050d1a", "coast": "#FF9800", "country": "#4a2e00", "bg": "#050d1a"},
        "South America": {"land": "#001a2e", "ocean": "#050d1a", "coast": "#00BCD4", "country": "#003a4e", "bg": "#050d1a"},
        "Oceania":       {"land": "#1a0a2e", "ocean": "#050d1a", "coast": "#9C27B0", "country": "#2e0a4e", "bg": "#050d1a"},
    }
    theme = region_themes.get(sel, region_themes["Global View"])

    fig_ov.update_layout(
        height=460, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor=theme["bg"], plot_bgcolor=theme["bg"],
        geo=dict(
            showframe=False,
            showcoastlines=True, coastlinecolor=theme["coast"],
            showland=True, landcolor=theme["land"],
            showocean=True, oceancolor=theme["ocean"],
            showlakes=True, lakecolor=theme["ocean"],
            showcountries=True, countrycolor=theme["country"], countrywidth=0.6,
            bgcolor=theme["bg"], projection_type="natural earth",
            lataxis=dict(range=bounds["lat"]),
            lonaxis=dict(range=bounds["lon"]),
        ),
        legend=dict(orientation="h", y=1.01, x=0.5, xanchor="center",
                    font=dict(color="#90A4AE", size=10), bgcolor="rgba(0,0,0,0)"),
        font=dict(color="#546E7A"),
    )

    # ── Main layout: map left, charts right ───────────────────────────────
    map_col, chart_col = st.columns([2.8, 1.2])

    with map_col:
        st.plotly_chart(fig_ov, use_container_width=True, config={"displayModeBar": False})

        # Region tabs below map
        tab_cols = st.columns(len(region_tabs))
        for i, (region, (count, color)) in enumerate(region_tabs.items()):
            with tab_cols[i]:
                is_active = st.session_state.ov_region == region
                if st.button(
                    f"{'🔵 ' if region=='Global View' else ''}{region}   {count}",
                    key=f"ov_tab_{region}",
                    use_container_width=True
                ):
                    st.session_state.ov_region = region
                    st.rerun()

    with chart_col:
        # Build highlighted donut — selected region full opacity, others faded
        df_reg_highlight = df_regional.copy()
        if sel != "Global View":
            pull_vals = [0.1 if r == sel else 0 for r in df_reg_highlight["Region"]]
            opacity_vals = [1.0 if r == sel else 0.25 for r in df_reg_highlight["Region"]]
            colors = [REGION_COLORS.get(r, "#888") if r == sel 
                      else f"rgba(100,100,100,0.25)" for r in df_reg_highlight["Region"]]
        else:
            pull_vals = [0] * len(df_reg_highlight)
            opacity_vals = [1.0] * len(df_reg_highlight)
            colors = [REGION_COLORS.get(r, "#888") for r in df_reg_highlight["Region"]]

        st.markdown('<div style="color:#4FC3F7; font-size:0.75rem; font-weight:700; letter-spacing:0.08em; margin-bottom:2px;">REGIONAL SHARE</div>', unsafe_allow_html=True)
        fig_donut = go.Figure(go.Pie(
            labels=df_reg_highlight["Region"],
            values=df_reg_highlight["AFU_Institutions"],
            hole=0.5,
            pull=pull_vals,
            marker=dict(colors=colors, line=dict(color="#050d1a", width=2)),
            textinfo="percent+label",
            textfont=dict(size=9, color="white"),
            hovertemplate="<b>%{label}</b><br>Institutions: %{value}<br>Share: %{percent}<extra></extra>",
        ))
        fig_donut.update_layout(
            height=220, showlegend=False,
            paper_bgcolor="#050d1a", plot_bgcolor="#050d1a",
            margin=dict(l=5, r=5, t=5, b=5),
            font=dict(color="#90A4AE"),
        )
        st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})

        # Build highlighted bar — selected region bright, others faded
        st.markdown('<div style="color:#4FC3F7; font-size:0.75rem; font-weight:700; letter-spacing:0.08em; margin-bottom:2px;">INSTITUTIONS PER REGION</div>', unsafe_allow_html=True)
        df_bar = df_regional.sort_values("AFU_Institutions").copy()
        if sel != "Global View":
            bar_colors = [REGION_COLORS.get(r, "#888") if r == sel 
                         else "rgba(80,80,80,0.3)" for r in df_bar["Region"]]
        else:
            bar_colors = [REGION_COLORS.get(r, "#888") for r in df_bar["Region"]]

        fig_bar = go.Figure(go.Bar(
            x=df_bar["AFU_Institutions"],
            y=df_bar["Region"],
            orientation="h",
            marker=dict(color=bar_colors, line=dict(width=0)),
            text=df_bar["AFU_Institutions"],
            textposition="outside",
            textfont=dict(color="#90A4AE", size=10),
            hovertemplate="<b>%{y}</b><br>Institutions: %{x}<extra></extra>",
        ))
        fig_bar.update_layout(
            height=230, showlegend=False,
            paper_bgcolor="#050d1a", plot_bgcolor="#050d1a",
            xaxis=dict(title="", color="#37474F", gridcolor="#0d2137", showgrid=True),
            yaxis=dict(title="", color="#90A4AE"),
            font=dict(color="#90A4AE"),
            margin=dict(l=5, r=40, t=5, b=5),
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

# ══════════════════════════════════════════════════════════════════════════
# PAGE 2 — PRINCIPLE GAP ANALYSIS
# ══════════════════════════════════════════════════════════════════════════
elif page == "📐 Principle Gap Analysis":

    st.markdown("""
    <div style="background:#050d1a; padding:6px 0 2px 0;">
        <span style="color:#4FC3F7; font-size:1.1rem; font-weight:800; letter-spacing:0.06em;">
            📐 AFU PRINCIPLE IMPLEMENTATION GAP ANALYSIS
        </span>
        <span style="color:#37474F; font-size:0.78rem; margin-left:12px;">
            Based on 25 Best Practice submissions from 17 institutions
        </span>
    </div>
    """, unsafe_allow_html=True)

    # KPI row
    well = df_principles[df_principles["Gap_Flag"]=="Well Implemented"].shape[0]
    mod  = df_principles[df_principles["Gap_Flag"]=="Moderately Implemented"].shape[0]
    unde = df_principles[df_principles["Gap_Flag"]=="Underimplemented"].shape[0]

    st.markdown(f"""
    <div style="display:flex; gap:8px; margin:6px 0;">
        <div style="background:#0a1628; border:1px solid #0d2137; border-radius:6px; padding:6px 12px; flex:1; text-align:center; border-top:2px solid #27AE60;">
            <div style="color:#27AE60; font-size:1.4rem; font-weight:800;">{well}</div>
            <div style="color:#546E7A; font-size:0.65rem; text-transform:uppercase;">Well Implemented</div>
        </div>
        <div style="background:#0a1628; border:1px solid #0d2137; border-radius:6px; padding:6px 12px; flex:1; text-align:center; border-top:2px solid #F39C12;">
            <div style="color:#F39C12; font-size:1.4rem; font-weight:800;">{mod}</div>
            <div style="color:#546E7A; font-size:0.65rem; text-transform:uppercase;">Moderately Implemented</div>
        </div>
        <div style="background:#0a1628; border:1px solid #0d2137; border-radius:6px; padding:6px 12px; flex:1; text-align:center; border-top:2px solid #E74C3C;">
            <div style="color:#E74C3C; font-size:1.4rem; font-weight:800;">{unde}</div>
            <div style="color:#546E7A; font-size:0.65rem; text-transform:uppercase;">Underimplemented</div>
        </div>
        <div style="background:#0a1628; border:1px solid #0d2137; border-radius:6px; padding:6px 12px; flex:2; text-align:center; border-top:2px solid #EF5350;">
            <div style="color:#EF5350; font-size:1.1rem; font-weight:800;">P5 & P7 — Only 16%</div>
            <div style="color:#546E7A; font-size:0.65rem; text-transform:uppercase;">Most Critical Gap — Online Access & Longevity Dividend</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Principle bar chart — full width
    st.markdown('<div style="color:#4FC3F7; font-size:0.75rem; font-weight:700; letter-spacing:0.08em; margin-bottom:2px;">PRINCIPLE CITATION FREQUENCY (% of 25 submissions)</div>', unsafe_allow_html=True)
    fig_p = px.bar(df_principles.sort_values("Pct"),
                   x="Pct", y="Short_Label", color="Gap_Flag",
                   color_discrete_map=GAP_COLORS, orientation="h", text="Pct",
                   labels={"Pct": "", "Short_Label": ""})
    fig_p.update_traces(texttemplate="%{text}%", textposition="outside",
                        textfont=dict(size=10))
    fig_p.add_vline(x=50, line_dash="dot", line_color="#37474F",
                    annotation_text="50%", annotation_position="top right",
                    annotation_font=dict(color="#546E7A", size=9))
    fig_p.update_layout(
        height=370,
        paper_bgcolor="#050d1a", plot_bgcolor="#050d1a",
        xaxis=dict(range=[0,88], color="#37474F", gridcolor="#0d2137", title=""),
        yaxis=dict(color="#90A4AE", title="", tickfont=dict(size=9.5)),
        legend_title="", legend=dict(orientation="h", y=-0.14,
                                     font=dict(color="#90A4AE", size=9)),
        margin=dict(l=5, r=50, t=5, b=30),
        font=dict(color="#90A4AE"),
    )
    st.plotly_chart(fig_p, use_container_width=True, config={"displayModeBar": False})

    st.markdown('<div style="color:#EF5350; font-size:0.78rem; padding:6px 10px; background:#1a0a0a; border-left:3px solid #EF5350; border-radius:0 4px 4px 0; margin:4px 0;">⚠️ P5 (Online access) and P7 (Longevity dividend) cited in only 16% of submissions — the critical implementation gap across the network.</div>', unsafe_allow_html=True)

    # Audience chart — below, full width
    st.markdown('<div style="color:#4FC3F7; font-size:0.75rem; font-weight:700; letter-spacing:0.08em; margin:8px 0 2px;">WHO DO ACTIVITIES TARGET?</div>', unsafe_allow_html=True)
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
        fig_aud.update_traces(textposition="outside", textfont=dict(size=10))
        fig_aud.update_layout(
            height=280, showlegend=False, coloraxis_showscale=False,
            paper_bgcolor="#050d1a", plot_bgcolor="#050d1a",
            xaxis=dict(color="#37474F", gridcolor="#0d2137", title=""),
            yaxis=dict(color="#90A4AE", title="", tickfont=dict(size=10)),
            margin=dict(l=5, r=40, t=5, b=10),
            font=dict(color="#90A4AE"),
        )
        st.plotly_chart(fig_aud, use_container_width=True, config={"displayModeBar": False})
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
# PAGE 5 — IMPACT MAP (City Cancer Challenge Style)
# ══════════════════════════════════════════════════════════════════════════
elif page == "🌐 Impact Map":

    st.markdown("""
    <div style="background:#0d1b2a; padding:6px 16px; border-radius:6px; margin-bottom:8px;">
        <span style="color:#00d4ff; font-size:1.1rem; font-weight:800;">🌐 AFU Global Network</span>
        <span style="color:#8899bb; font-size:0.85rem; margin-left:12px;">Impact Map — Select a Region</span>
    </div>
    """, unsafe_allow_html=True)

    if "selected_region" not in st.session_state:
        st.session_state.selected_region = None
    if "selected_country" not in st.session_state:
        st.session_state.selected_country = None

    sel_region = st.session_state.selected_region
    sel_country = st.session_state.selected_country

    # ── Horizontal region buttons above map ───────────────────────────────
    all_regions = ["All Regions"] + sorted(df_country["Region"].unique().tolist())
    reg_cols = st.columns(len(all_regions))
    for i, region in enumerate(all_regions):
        with reg_cols[i]:
            count = df_regional["AFU_Institutions"].sum() if region == "All Regions" else (df_regional[df_regional["Region"]==region]["AFU_Institutions"].values[0] if region in df_regional["Region"].values else 0)
            label = f"🌐 All ({count})" if region == "All Regions" else f"{region} ({count})"
            if st.button(label, key=f"reg3_{region}", use_container_width=True):
                st.session_state.selected_region = None if region == "All Regions" else region
                st.session_state.selected_country = None
                st.rerun()

    # ── Map data ───────────────────────────────────────────────────────────
    if sel_country:
        map_df = df_country.copy()
        map_df["opacity"] = map_df["Country"].apply(lambda x: 1.0 if x == sel_country else 0.2)
    elif sel_region:
        map_df = df_country.copy()
        map_df["opacity"] = map_df["Region"].apply(lambda x: 1.0 if x == sel_region else 0.2)
    else:
        map_df = df_country.copy()
        map_df["opacity"] = 1.0

    region_iso = {
        "North America": ["USA","CAN","MEX","GTM","BLZ","HND","SLV","NIC","CRI","PAN","CUB","JAM","HTI","DOM","TTO","BRB"],
        "Europe": ["IRL","GBR","PRT","ESP","HRV","CZE","HUN","ISR","SVK","SVN","CHE","FRA","DEU","ITA","NLD","BEL","AUT","POL","SWE","NOR","DNK","FIN","GRC","ROU","BGR","SRB","UKR","ALB","MKD","BIH","MNE","LTU","LVA","EST","LUX","MLT","CYP","ISL"],
        "Asia": ["KOR","CHN","PHL","HKG","TUR","IND","JPN","IDN","MYS","THA","VNM","MMR","KHM","SGP","BGD","LKA","NPL","PAK","AFG","IRN","IRQ","SAU","ARE","QAT","KWT","BHR","OMN","YEM","SYR","LBN","JOR","ARM","AZE","GEO","KAZ","UZB","MNG"],
        "Oceania": ["AUS","NZL","PNG","FJI","SLB","VUT","WSM","TON"],
        "South America": ["BRA","CHL","ARG","COL","PER","VEN","ECU","BOL","PRY","URY","GUY","SUR"],
    }
    region_highlight_colors = {
        "North America":"#E63946","Europe":"#2196F3",
        "Asia":"#FF9800","Oceania":"#9C27B0","South America":"#00BCD4",
    }

    # ── Layout: left panel + map ───────────────────────────────────────────
    if sel_region or sel_country:
        left_col, map_col = st.columns([1, 3])
    else:
        left_col = None
        map_col_full = st.container()

    # Build map figure
    fig_impact = go.Figure()

    if sel_region and sel_region in region_iso:
        sel_isos = region_iso[sel_region]
        hi_color = region_highlight_colors.get(sel_region, "#FFFFFF")
        fig_impact.add_trace(go.Choropleth(
            locations=sel_isos, z=[1]*len(sel_isos),
            colorscale=[[0,"rgba(255,255,255,0.04)"],[1,"rgba(255,255,255,0.04)"]],
            showscale=False, marker_line_color=hi_color, marker_line_width=1.2,
            hoverinfo="skip", showlegend=False, zmin=0, zmax=1,
        ))

    for region in df_country["Region"].unique():
        rdf = map_df[map_df["Region"]==region]
        color = REGION_COLORS.get(region, "#888888")
        opacity = float(rdf["opacity"].mean()) if len(rdf) > 0 else 1.0
        fig_impact.add_trace(go.Scattergeo(
            lat=rdf["Latitude"], lon=rdf["Longitude"],
            mode="markers", name=region,
            marker=dict(size=rdf["AFU_Members"].apply(lambda x: max(8, min(40, x/2.5))),
                        color=color, opacity=opacity, line=dict(width=1.5, color="white")),
            text=rdf["Country"],
            customdata=rdf[["AFU_Members"]].values,
            hovertemplate="<b>%{text}</b><br>AFU Members: %{customdata[0]}<extra></extra>",
        ))

    fig_impact.update_layout(
        height=420, margin=dict(l=0,r=0,t=0,b=0),
        paper_bgcolor="#0d1b2a", plot_bgcolor="#0d1b2a",
        showlegend=False,
        geo=dict(showframe=False, showcoastlines=True, coastlinecolor="#2e4a8a",
                 showland=True, landcolor="#1a2744", showocean=True, oceancolor="#0d1b2a",
                 showcountries=True, countrycolor="#2e4a8a", countrywidth=0.5,
                 bgcolor="#0d1b2a", projection_type="natural earth"),
        font=dict(color="#8899bb"),
    )

    # ── Render layout ──────────────────────────────────────────────────────
    if sel_region or sel_country:
        with left_col:
            color = REGION_COLORS.get(sel_region or df_country[df_country["Country"]==sel_country]["Region"].values[0], "#4FC3F7")

            if sel_region and not sel_country:
                rdata = df_regional[df_regional["Region"]==sel_region]
                rcountries = df_country[df_country["Region"]==sel_region]
                total_inst = int(rdata["AFU_Institutions"].values[0]) if len(rdata) > 0 else 0
                countries_in = int(rdata["Countries_in_AFU"].values[0]) if len(rdata) > 0 else 0
                total_c = int(rdata["Total_Countries"].values[0]) if len(rdata) > 0 else 0
                coverage = round(countries_in/total_c*100,1) if total_c > 0 else 0

                # Region title
                st.markdown(f'<div style="color:{color}; font-size:0.9rem; font-weight:800; margin-bottom:10px; letter-spacing:0.06em;">{sel_region.upper()}</div>', unsafe_allow_html=True)

                # Country list — name LEFT, count RIGHT
                st.markdown(f'<div style="color:{color}; font-size:0.72rem; font-weight:700; margin-bottom:6px;">COUNTRIES WITH AFU MEMBERS</div>', unsafe_allow_html=True)
                for _, row in rcountries.sort_values("AFU_Members", ascending=False).iterrows():
                    st.markdown(f"""
                    <div style="display:flex; justify-content:space-between; align-items:center;
                                background:#1a2744; border-left:3px solid {color};
                                padding:6px 10px; margin:3px 0; border-radius:0 6px 6px 0;">
                        <span style="color:#cce4ff; font-size:0.78rem;">● {row["Country"]}</span>
                        <span style="color:{color}; font-weight:700; font-size:0.78rem;">{int(row["AFU_Members"])}</span>
                    </div>""", unsafe_allow_html=True)

                st.markdown("")
                country_options = ["Select country..."] + rcountries.sort_values("AFU_Members", ascending=False)["Country"].tolist()
                chosen = st.selectbox("", country_options, key="csel2", label_visibility="collapsed")
                if chosen != "Select country...":
                    st.session_state.selected_country = chosen
                    st.rerun()
                if st.button("↩ Global View", key="back_r", use_container_width=True):
                    st.session_state.selected_region = None
                    st.rerun()

            elif sel_country:
                cdata = df_country[df_country["Country"]==sel_country].iloc[0]
                color = REGION_COLORS.get(cdata["Region"], "#4FC3F7")
                st.markdown(f'<div style="color:{color}; font-size:0.85rem; font-weight:800; margin-bottom:8px;">{sel_country.upper()}</div>', unsafe_allow_html=True)
                st.markdown("---")
                if st.button("↩ Back to Region", key="back_c", use_container_width=True):
                    st.session_state.selected_country = None
                    st.rerun()
                if st.button("↩ Global View", key="back_g2", use_container_width=True):
                    st.session_state.selected_region = None
                    st.session_state.selected_country = None
                    st.rerun()

        with map_col:
            st.plotly_chart(fig_impact, use_container_width=True, config={"displayModeBar": False})
            # Metrics below map
            if sel_region and not sel_country:
                rdata2 = df_regional[df_regional["Region"]==sel_region]
                total_inst2 = int(rdata2["AFU_Institutions"].values[0]) if len(rdata2) > 0 else 0
                countries_in2 = int(rdata2["Countries_in_AFU"].values[0]) if len(rdata2) > 0 else 0
                total_c2 = int(rdata2["Total_Countries"].values[0]) if len(rdata2) > 0 else 0
                coverage2 = round(countries_in2/total_c2*100,1) if total_c2 > 0 else 0
                color2 = REGION_COLORS.get(sel_region, "#4FC3F7")
                st.markdown(f"""
                <div style="display:flex; gap:8px; margin-top:6px;">
                    <div style="background:#0d1b2a; border:1px solid {color2}44; border-radius:8px; padding:10px; flex:1; text-align:center;">
                        <div style="color:{color2}; font-size:1.4rem; font-weight:800;">{total_inst2}</div>
                        <div style="color:#8899bb; font-size:0.68rem; text-transform:uppercase;">Institutions</div>
                    </div>
                    <div style="background:#0d1b2a; border:1px solid {color2}44; border-radius:8px; padding:10px; flex:1; text-align:center;">
                        <div style="color:{color2}; font-size:1.4rem; font-weight:800;">{countries_in2}/{total_c2}</div>
                        <div style="color:#8899bb; font-size:0.68rem; text-transform:uppercase;">Countries in AFU</div>
                    </div>
                    <div style="background:#0d1b2a; border:1px solid {color2}44; border-radius:8px; padding:10px; flex:1; text-align:center;">
                        <div style="color:{color2}; font-size:1.4rem; font-weight:800;">{coverage2}%</div>
                        <div style="color:#8899bb; font-size:0.68rem; text-transform:uppercase;">Country Coverage</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            elif sel_country:
                cdata3 = df_country[df_country["Country"]==sel_country].iloc[0]
                color3 = REGION_COLORS.get(cdata3["Region"], "#4FC3F7")
                institutions3 = INSTITUTIONS.get(sel_country, [])
                # Metrics row below map
                st.markdown(f"""
                <div style="display:flex; gap:8px; margin-top:6px;">
                    <div style="background:#0d1b2a; border:1px solid {color3}44; border-radius:8px; padding:10px; flex:1; text-align:center;">
                        <div style="color:{color3}; font-size:1.4rem; font-weight:800;">{int(cdata3["AFU_Members"])}</div>
                        <div style="color:#8899bb; font-size:0.68rem; text-transform:uppercase;">AFU Members</div>
                    </div>
                    <div style="background:#0d1b2a; border:1px solid {color3}44; border-radius:8px; padding:10px; flex:2; text-align:center;">
                        <div style="color:{color3}; font-size:1.1rem; font-weight:800;">{cdata3["Region"]}</div>
                        <div style="color:#8899bb; font-size:0.68rem; text-transform:uppercase;">Region</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                # Institutions list below metrics
                st.markdown(f'<div style="color:{color3}; font-size:0.75rem; font-weight:700; margin:10px 0 6px;">INSTITUTIONS ({len(institutions3)})</div>', unsafe_allow_html=True)
                inst_html = "".join([
                    f'<div style="display:flex; justify-content:flex-start; align-items:center; background:#1a2744; border-left:3px solid {color3}; padding:5px 10px; margin:3px 0; border-radius:0 6px 6px 0; font-size:0.75rem; color:#cce4ff;">🎓 {inst}</div>'
                    for inst in institutions3
                ])
                st.markdown(f'<div style="max-height:200px; overflow-y:auto;">{inst_html}</div>', unsafe_allow_html=True)

    else:
        with map_col_full:
            st.plotly_chart(fig_impact, use_container_width=True, config={"displayModeBar": False})
            # Global stats below map
            st.markdown("""
            <div style="display:flex; gap:8px; margin-top:6px;">
                <div style="background:#0d1b2a; border:1px solid #2e4a8a; border-radius:8px; padding:10px; flex:1; text-align:center;">
                    <div style="color:#00d4ff; font-size:1.4rem; font-weight:800;">153</div>
                    <div style="color:#8899bb; font-size:0.68rem; text-transform:uppercase;">Institutions</div>
                </div>
                <div style="background:#0d1b2a; border:1px solid #2e4a8a; border-radius:8px; padding:10px; flex:1; text-align:center;">
                    <div style="color:#27AE60; font-size:1.4rem; font-weight:800;">21</div>
                    <div style="color:#8899bb; font-size:0.68rem; text-transform:uppercase;">Countries</div>
                </div>
                <div style="background:#0d1b2a; border:1px solid #2e4a8a; border-radius:8px; padding:10px; flex:1; text-align:center;">
                    <div style="color:#FF9800; font-size:1.4rem; font-weight:800;">5</div>
                    <div style="color:#8899bb; font-size:0.68rem; text-transform:uppercase;">Regions</div>
                </div>
                <div style="background:#0d1b2a; border:1px solid #2e4a8a; border-radius:8px; padding:10px; flex:1; text-align:center;">
                    <div style="color:#9C27B0; font-size:1.4rem; font-weight:800;">11%</div>
                    <div style="color:#8899bb; font-size:0.68rem; text-transform:uppercase;">Best Practice Rate</div>
                </div>
                <div style="background:#0d1b2a; border:1px solid #2e4a8a; border-radius:8px; padding:10px; flex:1; text-align:center;">
                    <div style="color:#E63946; font-size:1.4rem; font-weight:800;">77%</div>
                    <div style="color:#8899bb; font-size:0.68rem; text-transform:uppercase;">North America Share</div>
                </div>
                <div style="background:#0d1b2a; border:1px solid #2e4a8a; border-radius:8px; padding:10px; flex:1; text-align:center;">
                    <div style="color:#EF5350; font-size:1.4rem; font-weight:800;">16%</div>
                    <div style="color:#8899bb; font-size:0.68rem; text-transform:uppercase;">P5 & P7 Rate</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
