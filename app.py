import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events
import re
import os
import json
import time
from collections import Counter

import api_client

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
def load_static_country_data():
    return pd.DataFrame([
        ("United States","North America",105,37.09,-95.71),
        ("Canada","North America",12,56.13,-106.35),
        ("Mexico","North America",1,23.63,-102.55),
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
def load_static_regional_data():
    return pd.DataFrame([
        ("North America",3,23,118),
        ("Europe",13,44,22),
        ("Asia",5,48,7),
        ("Oceania",1,14,2),
        ("South America",2,12,5),
    ], columns=["Region","Countries_in_AFU","Total_Countries","AFU_Institutions"])


# The live scraper picks up whatever country name AFUGN's site literally uses
# (sometimes the formal/long form), which doesn't always match the shorter
# display names used in this dashboard's static lat/lon table. Map the known
# divergent API names to their static-table equivalents.
API_TO_STATIC_COUNTRY_NAME = {
    "United States of America": "United States",
    "Hong Kong Special Administrative Region of the People's Republic of China": "Hong Kong SAR",
}
STATIC_TO_API_COUNTRY_NAME = {v: k for k, v in API_TO_STATIC_COUNTRY_NAME.items()}


def load_live_country_country_counts():
    """Fetch per-country institution counts from the API, normalized to this
    dashboard's static country names. Returns (dict[country -> count], error)
    -- error is None on success."""
    payload, err = api_client.fetch_countries()
    if err:
        return None, err
    raw_counts = payload.get("countries", {})
    counts = {}
    for name, count in raw_counts.items():
        canonical = API_TO_STATIC_COUNTRY_NAME.get(name, name)
        counts[canonical] = counts.get(canonical, 0) + count
    return counts, None


def load_live_region_counts():
    payload, err = api_client.fetch_regions()
    if err:
        return None, err
    return payload.get("regions", {}), None


def load_live_countries_in_afu_by_region(regions):
    """For each region name, count distinct countries the API currently has
    at least one member in. Best-effort: a per-region fetch failure just
    leaves that region out of the result (caller falls back to static)."""
    result = {}
    for region in regions:
        payload, err = api_client.fetch_countries(region=region)
        if err:
            continue
        canonical_names = {API_TO_STATIC_COUNTRY_NAME.get(n, n) for n in payload.get("countries", {})}
        result[region] = len(canonical_names)
    return result


def merge_live_country_data(static_df, live_counts):
    """Overlay live per-country counts onto the static lat/lon table.
    Countries present live but missing static coordinates are reported back
    (not plotted) rather than dropped silently or crashing."""
    if not live_counts:
        return static_df.copy(), []

    df = static_df.copy()
    static_names = set(df["Country"])
    df["AFU_Members"] = df["Country"].map(live_counts).fillna(df["AFU_Members"]).astype(int)

    uncoordinated = sorted(name for name in live_counts if name not in static_names)
    return df, uncoordinated


def merge_live_regional_data(static_df, live_region_counts, live_countries_in_afu):
    """live_region_counts: dict[region -> institution count] from /members/regions.
    live_countries_in_afu: dict[region -> count of distinct countries], derived
    by calling /members/countries?region=<region> per region (the region-count
    endpoint alone doesn't break countries out by region)."""
    df = static_df.copy()
    if live_region_counts:
        df["AFU_Institutions"] = df["Region"].map(live_region_counts).fillna(df["AFU_Institutions"]).astype(int)
    if live_countries_in_afu:
        df["Countries_in_AFU"] = df["Region"].map(live_countries_in_afu).fillna(df["Countries_in_AFU"]).astype(int)
    return df

@st.cache_data
def load_principles_data():
    return pd.DataFrame([
        (1,"P1: Encourage participation\nof older adults",20,71.0,"Well Implemented"),
        (2,"P2: Personal & career\ndevelopment",9,32.0,"Moderately Implemented"),
        (3,"P3: Recognize educational\nneeds",8,29.0,"Moderately Implemented"),
        (4,"P4: Intergenerational\nlearning",15,54.0,"Well Implemented"),
        (5,"P5: Online access for\nolder adults",4,14.0,"Underimplemented"),
        (6,"P6: Research agenda\ninformed by aging",14,50.0,"Well Implemented"),
        (7,"P7: Student understanding\nof longevity",5,18.0,"Underimplemented"),
        (8,"P8: Health, wellness &\ncultural access",13,46.0,"Well Implemented"),
        (9,"P9: Engage retired\ncommunity",7,25.0,"Moderately Implemented"),
        (10,"P10: Dialogue with aging\norganizations",6,21.0,"Underimplemented"),
    ], columns=["Principle_Number","Short_Label","Mentions","Pct","Gap_Flag"])

@st.cache_data
def load_best_practices():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "Form_Data_Entry-Grid_view.csv")
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]
    return df

@st.cache_data
def load_india_geojson():
    # Official external boundary of India (per the Indian constitution/government,
    # includes the full Union Territories of Jammu & Kashmir and Ladakh), used to
    # overlay a correct outline on top of Plotly's default base map -- whose
    # bundled world atlas draws India's border incorrectly.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    geojson_path = os.path.join(base_dir, "india_outline.geojson")
    with open(geojson_path, encoding="utf-8") as f:
        return json.load(f)

# Static fallback institution list by country, used only when the live API
# is unreachable.
STATIC_INSTITUTIONS = {
    "United States": ["University of Minnesota","University of Massachusetts Boston","Arizona State University","Duke University","Rochester Institute of Technology","University of North Carolina Wilmington","University of Michigan","Middle Tennessee State University","University of South Florida","University of New Hampshire","University of Arizona","California State University San Bernardino","California State University Fullerton","California State University Long Beach","Dominican University of California","Fielding Graduate University","Los Angeles Pierce College","Palo Alto University","San Diego State University","Santa Monica College","UCLA","UC Berkeley","University of San Francisco","University of Southern California","University of the Pacific","Colorado State University","University of Colorado Denver","University of Colorado Anschutz","University of Colorado Colorado Springs","Central Connecticut State University","Goodwin University","Quinnipiac University","University of Bridgeport","University of Connecticut","University of Hartford","Florida Atlantic University","Florida State University","Eckerd College","St. Thomas University","Georgia State University","University of North Georgia","University of Hawaii at Manoa","Northeastern Illinois University","University of Illinois Urbana-Champaign","Concordia University Chicago","Purdue University","University of Indianapolis","Wichita State University","Frontier Nursing University","Northern Kentucky University","Western Kentucky University","Franciscan Missionaries of Our Lady University","University of Maine","University of New England","Towson University","University of Maryland Baltimore","University of Maryland Baltimore County","Lasell University","UMass Amherst","UMass Dartmouth","UMass Lowell","UMass Medical School","Springfield College","William James College","Eastern Michigan University","Michigan State University","Wayne State University","University of Minnesota Duluth","University of St Thomas","St Catherine University","St Cloud State University","Mississippi State University","University of Mississippi","Missouri State University","Washington University in St Louis","University of Montana","University of Nebraska at Omaha","Fairleigh Dickinson University","Stockton University","Hofstra University","Hunter College CUNY","Ithaca College","Purchase College SUNY","Cleveland State University","Miami University","University of Akron","University of Cincinnati","University of Central Oklahoma","Portland State University","Southern Oregon University","Western Oregon University","Drexel University","Pennsylvania State University","University of Rhode Island","East Tennessee State University","Tennessee State University","University of Texas at Austin","University of Utah","University of Vermont","Virginia Commonwealth University","Shepherd University","West Virginia University","University of Wisconsin La Crosse","University of Wisconsin Green Bay","University of Wisconsin Superior"],
    "Canada": ["University of Calgary","Kwantlen Polytechnic University","University of British Columbia","UBC Okanagan","University of the Fraser Valley","Niagara College","McMaster University","Toronto Metropolitan University","Trent University","Ontario Tech University (UOIT)","University of Windsor","University of Manitoba"],
    "Mexico": ["ITESO, Universidad Jesuita de Guadalajara"],
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


@st.cache_data(ttl=300, show_spinner=False)
def get_institutions_for_country(country):
    """Live institution list (name + url) for a country, falling back to the
    static name-only list if the API is unavailable or has nothing for it."""
    api_country_name = STATIC_TO_API_COUNTRY_NAME.get(country, country)
    payload, err = api_client.fetch_members(country=api_country_name)
    if not err and payload.get("results"):
        return [
            {
                "name": m["name"],
                "url": m.get("url"),
                "latitude": m.get("latitude"),
                "longitude": m.get("longitude"),
            }
            for m in payload["results"]
        ]
    return [{"name": name, "url": None, "latitude": None, "longitude": None} for name in STATIC_INSTITUTIONS.get(country, [])]


def institution_points(df_countries, jitter_deg=0.55):
    """Expand country-level rows into one point per institution. Institutions
    the API has real geocoded coordinates for (see geocode.py) are plotted at
    their actual location; any without one yet (geocoding miss, or the static
    fallback list when the API is unreachable) fall back to a jittered point
    around the country's centroid so the map still shows a marker for them."""
    rows = []
    for _, r in df_countries.iterrows():
        insts = get_institutions_for_country(r["Country"])
        n = int(r["AFU_Members"])
        for i in range(n):
            inst = insts[i] if i < len(insts) else {"name": f"{r['Country']} institution {i+1}"}
            lat, lon = inst.get("latitude"), inst.get("longitude")
            if lat is None or lon is None:
                rng = np.random.default_rng(abs(hash((r["Country"], i))) % (2**32))
                lat = r["Latitude"] + rng.uniform(-jitter_deg, jitter_deg)
                lon = r["Longitude"] + rng.uniform(-jitter_deg, jitter_deg)
            rows.append({
                "Institution": inst["name"],
                "Country": r["Country"],
                "Region": r["Region"],
                "Latitude": lat,
                "Longitude": lon,
            })
    return pd.DataFrame(rows, columns=["Institution", "Country", "Region", "Latitude", "Longitude"])

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

# ── Live API data ──────────────────────────────────────────────────────────
meta, meta_err = api_client.fetch_meta()
live_region_counts, _ = load_live_region_counts()
live_country_counts, _ = load_live_country_country_counts()
api_live = meta_err is None and meta is not None and meta.get("total_institutions", 0) > 0

if api_live:
    live_countries_in_afu = load_live_countries_in_afu_by_region(sorted(REGION_COLORS.keys()))
else:
    live_countries_in_afu = {}

df_country, uncoordinated_countries = merge_live_country_data(
    load_static_country_data(), live_country_counts if api_live else None
)
df_regional = merge_live_regional_data(
    load_static_regional_data(),
    live_region_counts if api_live else None,
    live_countries_in_afu,
)
df_regional["Countries_Missing"] = df_regional["Total_Countries"] - df_regional["Countries_in_AFU"]
df_regional["Country_Coverage_Pct"] = (df_regional["Countries_in_AFU"] / df_regional["Total_Countries"] * 100).round(1)

live_total_institutions = meta.get("total_institutions") if api_live else None
live_total_countries = len(live_country_counts) if api_live and live_country_counts else None

total_institutions_kpi = (
    live_total_institutions if live_total_institutions is not None
    else int(df_regional["AFU_Institutions"].sum())
)
countries_kpi = (
    live_total_countries if live_total_countries is not None
    else int(df_regional["Countries_in_AFU"].sum())
)
na_members_kpi = int(df_regional.loc[df_regional["Region"] == "North America", "AFU_Institutions"].sum())
na_share_pct_kpi = round(na_members_kpi / total_institutions_kpi * 100) if total_institutions_kpi else 0

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
    st.markdown("**Live API status**")
    if api_live:
        scraped_at = meta.get("scraped_at")
        age_str = "unknown"
        if scraped_at:
            age_min = int((time.time() - scraped_at) / 60)
            age_str = f"{age_min} min ago" if age_min < 120 else f"{age_min // 60} hr ago"
        st.success(f"🟢 Connected — {meta.get('total_institutions', 0)} institutions, updated {age_str}")
        if st.button("🔄 Refresh live data", use_container_width=True):
            _, refresh_err = api_client.trigger_refresh()
            if refresh_err:
                st.error(f"Refresh failed: {refresh_err}")
            else:
                api_client.clear_cache()
                st.rerun()
        if uncoordinated_countries:
            with st.expander(f"⚠️ {len(uncoordinated_countries)} countries have no plotted coordinates yet"):
                st.write(", ".join(uncoordinated_countries))
    else:
        st.warning("🔴 Live API unavailable — showing static snapshot")
        st.caption(f"({meta_err or 'no data'}) Start it with:\n`uvicorn api:app --reload --port 8000`")
    st.markdown("---")
    st.markdown("**Data Sources**")
    st.markdown(
        "- AFU-API live service" + (" (connected)" if api_live else " (offline, static snapshot)")
        + "\n- AFU Best Practices Database\n- World Bank SP.POP.65UP.TO (2025)\n- UN Population Division WPP 2025"
    )
    st.markdown("---")
    st.caption("Paper: *Implementation Gap Analysis of the AFU Global Network*\nGenerations at Work, DCU, Oct 2026")
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

    st.markdown(f"""
    <div style="display:flex; gap:8px; margin:6px 0;">
        <div style="background:#0a1628; border:1px solid #0d2137; border-radius:6px; padding:8px 16px; flex:1; text-align:center; border-top:2px solid #4FC3F7;">
            <div style="color:#4FC3F7; font-size:1.5rem; font-weight:800;">{total_institutions_kpi}</div>
            <div style="color:#546E7A; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.08em;">Member Institutions</div>
        </div>
        <div style="background:#0a1628; border:1px solid #0d2137; border-radius:6px; padding:8px 16px; flex:1; text-align:center; border-top:2px solid #E63946;">
            <div style="color:#E63946; font-size:1.5rem; font-weight:800;">{na_share_pct_kpi}%</div>
            <div style="color:#546E7A; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.08em;">North America Share</div>
        </div>
        <div style="background:#0a1628; border:1px solid #0d2137; border-radius:6px; padding:8px 16px; flex:1; text-align:center; border-top:2px solid #27AE60;">
            <div style="color:#27AE60; font-size:1.5rem; font-weight:800;">{countries_kpi}</div>
            <div style="color:#546E7A; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.08em;">Countries</div>
        </div>
        <div style="background:#0a1628; border:1px solid #0d2137; border-radius:6px; padding:8px 16px; flex:1; text-align:center; border-top:2px solid #FF9800;">
            <div style="color:#FF9800; font-size:1.5rem; font-weight:800;">28</div>
            <div style="color:#546E7A; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.08em;">Best Practices</div>
        </div>
        <div style="background:#0a1628; border:1px solid #0d2137; border-radius:6px; padding:8px 16px; flex:1; text-align:center; border-top:2px solid #EF5350;">
            <div style="color:#EF5350; font-size:1.5rem; font-weight:800;">14%/18%</div>
            <div style="color:#546E7A; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.08em;">P5 & P7 Rate</div>
        </div>
        <div style="background:#0a1628; border:1px solid #0d2137; border-radius:6px; padding:8px 16px; flex:1; text-align:center; border-top:2px solid #9C27B0;">
            <div style="color:#9C27B0; font-size:1.5rem; font-weight:800;">13%</div>
            <div style="color:#546E7A; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.08em;">Submission Rate</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if "ov_region" not in st.session_state:
        st.session_state.ov_region = "Global View"

    region_tabs = {
        "Global View":   (total_institutions_kpi, "#4FC3F7"),
        "North America": (int(df_regional.loc[df_regional["Region"]=="North America","AFU_Institutions"].sum()), "#E63946"),
        "Europe":        (int(df_regional.loc[df_regional["Region"]=="Europe","AFU_Institutions"].sum()),  "#2196F3"),
        "Asia":          (int(df_regional.loc[df_regional["Region"]=="Asia","AFU_Institutions"].sum()),   "#FF9800"),
        "South America": (int(df_regional.loc[df_regional["Region"]=="South America","AFU_Institutions"].sum()), "#00BCD4"),
        "Oceania":       (int(df_regional.loc[df_regional["Region"]=="Oceania","AFU_Institutions"].sum()), "#9C27B0"),
    }

    sel = st.session_state.ov_region

    if sel == "Global View":
        map_df = df_country.copy()
        map_df["opacity"] = 1.0
    else:
        map_df = df_country.copy()
        map_df["opacity"] = map_df["Region"].apply(lambda x: 1.0 if x == sel else 0.12)

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

    fig_ov = go.Figure()

    india_geojson = load_india_geojson()
    fig_ov.add_trace(go.Choropleth(
        geojson=india_geojson, locations=["India"], featureidkey="properties.name",
        z=[1], colorscale=[[0, theme["land"]], [1, theme["land"]]],
        showscale=False, marker_line_color=theme["country"], marker_line_width=0.6,
        hoverinfo="skip", showlegend=False, zmin=0, zmax=1,
    ))

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

    if sel == "Global View":
        pins = institution_points(df_country)
        pin_line_colors = pins["Region"].map(REGION_COLORS).fillna("#888").tolist()
    else:
        pins = institution_points(df_country[df_country["Region"] == sel])
        pin_line_colors = REGION_COLORS.get(sel, "#888")
    fig_ov.add_trace(go.Scattergeo(
        lat=pins["Latitude"], lon=pins["Longitude"],
        mode="markers", showlegend=False,
        marker=dict(size=4, color="#ffffff", opacity=0.9,
                    line=dict(width=1, color=pin_line_colors)),
        customdata=pins[["Institution", "Country"]].values,
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<extra></extra>",
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

        # Region tabs below map — compact pill buttons
        st.markdown("""
        <div class="ov-region-tabs-marker"></div>
        <style>
        div[data-testid="stVerticalBlock"]:has(> div .ov-region-tabs-marker)
                div[data-testid="stHorizontalBlock"] {
            gap: 0.4rem;
        }
        div[data-testid="stVerticalBlock"]:has(> div .ov-region-tabs-marker) button {
            padding: 0.15rem 0.3rem !important;
            min-height: 1.6rem !important;
            height: 1.6rem !important;
            font-size: 0.66rem !important;
            font-weight: 600 !important;
            border-radius: 999px !important;
            line-height: 1 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }
        div[data-testid="stVerticalBlock"]:has(> div .ov-region-tabs-marker) button p {
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }
        </style>
        """, unsafe_allow_html=True)
        region_abbrev = {
            "Global View": "All", "North America": "N.Amer", "Europe": "Europe",
            "Asia": "Asia", "South America": "S.Amer", "Oceania": "Oceania",
        }
        tab_cols = st.columns(len(region_tabs), gap="small")
        for i, (region, (count, color)) in enumerate(region_tabs.items()):
            with tab_cols[i]:
                is_active = st.session_state.ov_region == region
                short = region_abbrev.get(region, region)
                if st.button(
                    f"{short} {count}",
                    key=f"ov_tab_{region}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                    help=region,
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
            textposition="outside",
            textfont=dict(size=9, color="#90A4AE"),
            hovertemplate="<b>%{label}</b><br>Institutions: %{value}<br>Share: %{percent}<extra></extra>",
        ))
        fig_donut.update_layout(
            height=260, showlegend=False,
            paper_bgcolor="#050d1a", plot_bgcolor="#050d1a",
            margin=dict(l=45, r=45, t=30, b=30),
            uniformtext=dict(minsize=8, mode="hide"),
            font=dict(color="#90A4AE"),
        )
        # Plotly's own selection events don't fire for pie/donut slices, so
        # use plotly_events (listens for the raw plotly_click event) to make
        # tapping a slice zoom the map, same as the bar chart click does.
        donut_clicks = plotly_events(
            fig_donut, click_event=True, hover_event=False, select_event=False,
            override_height=260, override_width="100%", key="donut_region_select",
        )
        if donut_clicks:
            point_idx = donut_clicks[0].get("pointNumber")
            if point_idx is not None and 0 <= point_idx < len(df_reg_highlight):
                clicked_region = df_reg_highlight.iloc[point_idx]["Region"]
                if clicked_region != sel:
                    st.session_state.ov_region = clicked_region
                    st.rerun()

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
            cliponaxis=False,
            textfont=dict(color="#90A4AE", size=10),
            hovertemplate="<b>%{y}</b><br>Institutions: %{x}<extra></extra>",
        ))
        max_bar = float(df_bar["AFU_Institutions"].max()) if len(df_bar) else 0
        fig_bar.update_layout(
            height=230, showlegend=False,
            paper_bgcolor="#050d1a", plot_bgcolor="#050d1a",
            xaxis=dict(title="", color="#37474F", gridcolor="#0d2137", showgrid=True,
                       range=[0, max_bar * 1.2 if max_bar > 0 else 1]),
            yaxis=dict(title="", color="#90A4AE"),
            font=dict(color="#90A4AE"),
            margin=dict(l=5, r=40, t=5, b=5),
        )
        bar_event = st.plotly_chart(
            fig_bar, use_container_width=True, config={"displayModeBar": False},
            on_select="rerun", selection_mode="points", key="bar_region_select",
        )
        bar_points = bar_event.get("selection", {}).get("points", []) if bar_event else []
        if bar_points:
            clicked_region = bar_points[0].get("y")
            if clicked_region and clicked_region != sel:
                st.session_state.ov_region = clicked_region
                st.rerun()

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
            Based on 28 Best Practice submissions from 20 institutions
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
            <div style="color:#EF5350; font-size:1.1rem; font-weight:800;">P5 — Only 14% | P7 — Only 18%</div>
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

    st.markdown('<div style="color:#EF5350; font-size:0.78rem; padding:6px 10px; background:#1a0a0a; border-left:3px solid #EF5350; border-radius:0 4px 4px 0; margin:4px 0;">⚠️ P5 (Online access) cited in only 14% and P7 (Longevity dividend) in only 18% of submissions — the most underimplemented principles across the network.</div>', unsafe_allow_html=True)

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
    st.markdown("""
    <div style="background:#0d1b2a; padding:6px 16px; border-radius:6px; margin-bottom:8px;">
        <span style="color:#4FC3F7; font-size:1.1rem; font-weight:800; letter-spacing:0.06em;">🗺️ GEOGRAPHIC EQUITY & POPULATION-ADJUSTED ANALYSIS</span>
        <span style="color:#37474F; font-size:0.78rem; margin-left:12px;">Country coverage gaps and age-adjusted AFU density</span>
    </div>
    """, unsafe_allow_html=True)

    # Population 65+ data (World Bank SP.POP.65UP.TO, 2025)
    pop65_dict = {
        "United States": {"pop65": 62844750, "per_m": 1.671},
        "Canada": {"pop65": 8438778, "per_m": 1.422},
        "Ireland": {"pop65": 888912, "per_m": 10.125},
        "United Kingdom": {"pop65": 13690810, "per_m": 0.146},
        "Portugal": {"pop65": 2695018, "per_m": 0.742},
        "Spain": {"pop65": 10681480, "per_m": 0.187},
        "Croatia": {"pop65": 915154, "per_m": 1.093},
        "Czech Republic": {"pop65": 2305849, "per_m": 0.434},
        "Hungary": {"pop65": 2012974, "per_m": 0.497},
        "Israel": {"pop65": 1284748, "per_m": 0.778},
        "Slovakia": {"pop65": 1030590, "per_m": 0.970},
        "Slovenia": {"pop65": 473316, "per_m": 2.113},
        "Switzerland": {"pop65": 1857777, "per_m": 0.538},
        "South Korea": {"pop65": 10507688, "per_m": 0.286},
        "China": {"pop65": 209741958, "per_m": 0.005},
        "Philippines": {"pop65": 6684893, "per_m": 0.150},
        "Hong Kong SAR": {"pop65": 1774789, "per_m": 0.563},
        "Australia": {"pop65": 4996279, "per_m": 0.400},
        "Brazil": {"pop65": 24431586, "per_m": 0.123},
        "Chile": {"pop65": 2897512, "per_m": 0.690},
        "Turkey": {"pop65": 9078171, "per_m": 0.110},
        "Mexico": {"pop65": 9831957, "per_m": 0.102},
    }
    df_country["Pop_65_M"] = df_country["Country"].map(lambda x: round(pop65_dict.get(x, {}).get("pop65", 0)/1e6, 2))
    df_country["AFU_Per_Million_Seniors"] = df_country["Country"].map(lambda x: pop65_dict.get(x, {}).get("per_m", 0))

    # Side by side — no scrolling
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div style="color:#4FC3F7; font-size:0.75rem; font-weight:700; letter-spacing:0.08em; margin-bottom:4px;">COUNTRY COVERAGE GAP BY REGION</div>', unsafe_allow_html=True)
        df_melt = df_regional.melt(id_vars="Region",
                                   value_vars=["Countries_in_AFU","Countries_Missing"],
                                   var_name="Type", value_name="Count")
        df_melt["Type"] = df_melt["Type"].map({"Countries_in_AFU":"In AFU GN","Countries_Missing":"Not in AFU GN"})
        fig_cov = px.bar(df_melt, x="Count", y="Region", color="Type", orientation="h",
                         color_discrete_map={"In AFU GN":"#2E6DA4","Not in AFU GN":"#D5E8F5"},
                         barmode="stack", text="Count")
        fig_cov.update_traces(textposition="inside")
        fig_cov.update_layout(height=320, xaxis_title="Number of Countries",
                              margin=dict(l=10,r=20,t=10,b=20),
                              legend=dict(orientation="h", y=-0.18))
        st.plotly_chart(fig_cov, use_container_width=True, config={"displayModeBar": False})

        # Compact table
        df_display = df_regional[["Region","Countries_in_AFU","Total_Countries","Countries_Missing","Country_Coverage_Pct"]].copy()
        df_display.columns = ["Region","In AFU GN","Total","Not Rep.","Coverage %"]
        st.dataframe(df_display, use_container_width=True, hide_index=True, height=215)

    with col2:
        st.markdown('<div style="color:#4FC3F7; font-size:0.75rem; font-weight:700; letter-spacing:0.08em; margin-bottom:4px;">AFU DENSITY PER MILLION SENIORS (2025)</div>', unsafe_allow_html=True)

        df_density = df_country[df_country["AFU_Per_Million_Seniors"] > 0].sort_values("AFU_Per_Million_Seniors", ascending=False).copy()

        fig_den = px.bar(
            df_density,
            x="Country", y="AFU_Per_Million_Seniors",
            color="Region", color_discrete_map=REGION_COLORS,
            text=df_density["AFU_Per_Million_Seniors"].apply(lambda x: f"{x:.2f}"),
            hover_data={"AFU_Members": True, "Pop_65_M": True},
        )
        fig_den.update_traces(textposition="outside", textfont_size=7)
        fig_den.update_layout(
            height=320,
            xaxis_tickangle=-45,
            yaxis_title="AFU per Million Seniors",
            xaxis_title="",
            margin=dict(l=10,r=10,t=10,b=100),
            legend=dict(orientation="h", y=-0.35, font=dict(size=9)),
        )
        st.plotly_chart(fig_den, use_container_width=True, config={"displayModeBar": False})

        st.markdown('<div style="background:#0a1628; border-left:3px solid #EF5350; padding:8px 12px; border-radius:0 6px 6px 0; font-size:0.78rem; color:#cce4ff;">💡 <b>Ireland (10.13)</b> leads due to DCU founder effect. <b>China (0.005)</b> — 209.74M seniors — is most underserved: a <b>2,000-fold gap</b>.</div>', unsafe_allow_html=True)

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
        <span style="color:#8899bb; font-size:0.85rem; margin-left:12px;">Impact Map</span>
    </div>
    """, unsafe_allow_html=True)

    if "selected_region" not in st.session_state:
        st.session_state.selected_region = None
    if "selected_country" not in st.session_state:
        st.session_state.selected_country = None

    sel_region = st.session_state.selected_region
    sel_country = st.session_state.selected_country

    # ── Region buttons ABOVE map — always horizontal ───────────────────────
    all_regions = sorted(df_country["Region"].unique().tolist())
    reg_cols = st.columns(len(all_regions))
    for i, region in enumerate(all_regions):
        with reg_cols[i]:
            count = df_regional[df_regional["Region"]==region]["AFU_Institutions"].values[0] if region in df_regional["Region"].values else 0
            color = REGION_COLORS.get(region, "#888")
            is_active = sel_region == region
            if st.button(
                f"{'▶' if is_active else '●'} {region} ({count})",
                key=f"reg_top_{region}",
                use_container_width=True
            ):
                if st.session_state.selected_region == region:
                    st.session_state.selected_region = None
                    st.session_state.selected_country = None
                else:
                    st.session_state.selected_region = region
                    st.session_state.selected_country = None
                st.rerun()

    # ── Main layout ────────────────────────────────────────────────────────
    # Left: countries (only when region selected)
    # Center: map
    # Right: institutions (only when country selected)
    if sel_region and sel_country:
        left_col, map_col, right_col = st.columns([0.8, 2.2, 1.2])
    elif sel_region:
        left_col, map_col = st.columns([0.8, 3.4])
        right_col = None
    else:
        left_col = None
        right_col = None
        map_col = st.container()

    # ── LEFT: countries list ───────────────────────────────────────────────
    if sel_region and left_col:
        with left_col:
            color = REGION_COLORS.get(sel_region, "#888")
            st.markdown(f'<div style="color:{color}; font-size:0.7rem; font-weight:700; letter-spacing:0.06em; margin-bottom:4px;">COUNTRIES</div>', unsafe_allow_html=True)
            rcountries = df_country[df_country["Region"]==sel_region].sort_values("AFU_Members", ascending=False)
            for _, row in rcountries.iterrows():
                is_sel = sel_country == row["Country"]
                if st.button(
                    f"{'▶' if is_sel else '○'} {row['Country']}",
                    key=f"cty_left_{row['Country']}",
                    use_container_width=True
                ):
                    st.session_state.selected_country = None if is_sel else row["Country"]
                    st.rerun()

    # ── Build map figure ───────────────────────────────────────────────────
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
        "Asia": ["KOR","CHN","PHL","HKG","TUR","JPN","IDN","MYS","THA","VNM","MMR","KHM","SGP","BGD","LKA","NPL","PAK","AFG","IRN","IRQ","SAU","ARE","QAT","KWT","BHR","OMN","YEM","SYR","LBN","JOR","ARM","AZE","GEO","KAZ","UZB","MNG"],
        "Oceania": ["AUS","NZL","PNG","FJI","SLB","VUT","WSM","TON"],
        "South America": ["BRA","CHL","ARG","COL","PER","VEN","ECU","BOL","PRY","URY","GUY","SUR"],
    }
    region_highlight_colors = {
        "North America":"#E63946","Europe":"#2196F3",
        "Asia":"#FF9800","Oceania":"#9C27B0","South America":"#00BCD4",
    }

    fig_impact = go.Figure()

    india_geojson = load_india_geojson()
    fig_impact.add_trace(go.Choropleth(
        geojson=india_geojson, locations=["India"], featureidkey="properties.name",
        z=[1], colorscale=[[0, "#1a2744"], [1, "#1a2744"]],
        showscale=False, marker_line_color="#2e4a8a", marker_line_width=0.5,
        hoverinfo="skip", showlegend=False, zmin=0, zmax=1,
    ))

    if sel_region and sel_region in region_iso:
        sel_isos = region_iso[sel_region]
        hi_color = region_highlight_colors.get(sel_region, "#FFFFFF")
        fig_impact.add_trace(go.Choropleth(
            locations=sel_isos, z=[1]*len(sel_isos),
            colorscale=[[0,"rgba(255,255,255,0.04)"],[1,"rgba(255,255,255,0.04)"]],
            showscale=False, marker_line_color=hi_color, marker_line_width=1.2,
            hoverinfo="skip", showlegend=False, zmin=0, zmax=1,
        ))
        if sel_region == "Asia":
            # Pakistan/China above are highlighted using Plotly's default ISO-3
            # boundaries, which draw their disputed claims over Kashmir/Aksai
            # Chin -- redraw India's correct outline here with an OPAQUE mask
            # (not just a border) so that stray line can't show through, then
            # add the same highlight tint/border as the other Asia countries.
            fig_impact.add_trace(go.Choropleth(
                geojson=india_geojson, locations=["India"], featureidkey="properties.name",
                z=[1], colorscale=[[0, "#1a2744"], [1, "#1a2744"]],
                showscale=False, marker_line_color="#2e4a8a", marker_line_width=0.5,
                hoverinfo="skip", showlegend=False, zmin=0, zmax=1,
            ))
            fig_impact.add_trace(go.Choropleth(
                geojson=india_geojson, locations=["India"], featureidkey="properties.name",
                z=[1], colorscale=[[0,"rgba(255,255,255,0.04)"],[1,"rgba(255,255,255,0.04)"]],
                showscale=False, marker_line_color=hi_color, marker_line_width=1.2,
                hoverinfo="skip", showlegend=False, zmin=0, zmax=1,
            ))

    for region in df_country["Region"].unique():
        rdf = map_df[map_df["Region"]==region]
        color_r = REGION_COLORS.get(region, "#888888")
        opacity = float(rdf["opacity"].mean()) if len(rdf) > 0 else 1.0
        fig_impact.add_trace(go.Scattergeo(
            lat=rdf["Latitude"], lon=rdf["Longitude"],
            mode="markers", name=region,
            marker=dict(size=rdf["AFU_Members"].apply(lambda x: max(8, min(40, x/2.5))),
                        color=color_r, opacity=opacity, line=dict(width=1.5, color="white")),
            text=rdf["Country"],
            customdata=rdf[["AFU_Members"]].values,
            hovertemplate="<b>%{text}</b><br>AFU Members: %{customdata[0]}<extra></extra>",
        ))

    if sel_region:
        pin_df = df_country[df_country["Region"] == sel_region]
        if sel_country:
            pin_df = pin_df[pin_df["Country"] == sel_country]
        pins = institution_points(pin_df)
        pin_line_colors = region_highlight_colors.get(sel_region, "#4FC3F7")
    else:
        pins = institution_points(df_country)
        pin_line_colors = pins["Region"].map(region_highlight_colors).fillna("#4FC3F7").tolist()
    fig_impact.add_trace(go.Scattergeo(
        lat=pins["Latitude"], lon=pins["Longitude"],
        mode="markers", showlegend=False,
        marker=dict(size=4, color="#ffffff", opacity=0.9,
                    line=dict(width=1, color=pin_line_colors)),
        customdata=pins[["Institution", "Country"]].values,
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<extra></extra>",
        ))

    fig_impact.update_layout(
        height=400, margin=dict(l=0,r=0,t=0,b=0),
        paper_bgcolor="#0d1b2a", plot_bgcolor="#0d1b2a",
        showlegend=False,
        geo=dict(showframe=False, showcoastlines=True, coastlinecolor="#2e4a8a",
                 showland=True, landcolor="#1a2744", showocean=True, oceancolor="#0d1b2a",
                 showcountries=True, countrycolor="#2e4a8a", countrywidth=0.5,
                 bgcolor="#0d1b2a", projection_type="natural earth"),
        font=dict(color="#8899bb"),
    )

    # ── MAP column ─────────────────────────────────────────────────────────
    with map_col:
        st.plotly_chart(fig_impact, use_container_width=True, config={"displayModeBar": False})

        # Stats below map
        if sel_region and not sel_country:
            rdata = df_regional[df_regional["Region"]==sel_region]
            total_inst = int(rdata["AFU_Institutions"].values[0]) if len(rdata) > 0 else 0
            countries_in = int(rdata["Countries_in_AFU"].values[0]) if len(rdata) > 0 else 0
            total_c = int(rdata["Total_Countries"].values[0]) if len(rdata) > 0 else 0
            coverage = round(countries_in/total_c*100,1) if total_c > 0 else 0
            color = REGION_COLORS.get(sel_region, "#4FC3F7")
            st.markdown(f"""<div style="display:flex; gap:8px; margin-top:4px;">
                <div style="background:#0d1b2a; border:1px solid {color}44; border-radius:8px; padding:8px; flex:1; text-align:center;">
                    <div style="color:{color}; font-size:1.3rem; font-weight:800;">{total_inst}</div>
                    <div style="color:#8899bb; font-size:0.65rem; text-transform:uppercase;">Institutions</div>
                </div>
                <div style="background:#0d1b2a; border:1px solid {color}44; border-radius:8px; padding:8px; flex:1; text-align:center;">
                    <div style="color:{color}; font-size:1.3rem; font-weight:800;">{countries_in}/{total_c}</div>
                    <div style="color:#8899bb; font-size:0.65rem; text-transform:uppercase;">Countries in AFU</div>
                </div>
                <div style="background:#0d1b2a; border:1px solid {color}44; border-radius:8px; padding:8px; flex:1; text-align:center;">
                    <div style="color:{color}; font-size:1.3rem; font-weight:800;">{coverage}%</div>
                    <div style="color:#8899bb; font-size:0.65rem; text-transform:uppercase;">Coverage</div>
                </div>
            </div>""", unsafe_allow_html=True)
        elif sel_country:
            cdata = df_country[df_country["Country"]==sel_country].iloc[0]
            color = REGION_COLORS.get(cdata["Region"], "#4FC3F7")
            st.markdown(f"""<div style="display:flex; gap:8px; margin-top:4px;">
                <div style="background:#0d1b2a; border:1px solid {color}44; border-radius:8px; padding:8px; flex:1; text-align:center;">
                    <div style="color:{color}; font-size:1.3rem; font-weight:800;">{int(cdata["AFU_Members"])}</div>
                    <div style="color:#8899bb; font-size:0.65rem; text-transform:uppercase;">AFU Members</div>
                </div>
                <div style="background:#0d1b2a; border:1px solid {color}44; border-radius:8px; padding:8px; flex:2; text-align:center;">
                    <div style="color:{color}; font-size:1rem; font-weight:800;">{sel_country} — {cdata["Region"]}</div>
                    <div style="color:#8899bb; font-size:0.65rem; text-transform:uppercase;">Country / Region</div>
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div style="display:flex; gap:8px; margin-top:4px;">
                <div style="background:#0d1b2a; border:1px solid #2e4a8a; border-radius:8px; padding:8px; flex:1; text-align:center;">
                    <div style="color:#00d4ff; font-size:1.3rem; font-weight:800;">{total_institutions_kpi}</div>
                    <div style="color:#8899bb; font-size:0.65rem; text-transform:uppercase;">Institutions</div>
                </div>
                <div style="background:#0d1b2a; border:1px solid #2e4a8a; border-radius:8px; padding:8px; flex:1; text-align:center;">
                    <div style="color:#27AE60; font-size:1.3rem; font-weight:800;">{countries_kpi}</div>
                    <div style="color:#8899bb; font-size:0.65rem; text-transform:uppercase;">Countries</div>
                </div>
                <div style="background:#0d1b2a; border:1px solid #2e4a8a; border-radius:8px; padding:8px; flex:1; text-align:center;">
                    <div style="color:#FF9800; font-size:1.3rem; font-weight:800;">5</div>
                    <div style="color:#8899bb; font-size:0.65rem; text-transform:uppercase;">Regions</div>
                </div>
                <div style="background:#0d1b2a; border:1px solid #2e4a8a; border-radius:8px; padding:8px; flex:1; text-align:center;">
                    <div style="color:#E63946; font-size:1.3rem; font-weight:800;">{na_share_pct_kpi}%</div>
                    <div style="color:#8899bb; font-size:0.65rem; text-transform:uppercase;">N.America Share</div>
                </div>
                <div style="background:#0d1b2a; border:1px solid #2e4a8a; border-radius:8px; padding:8px; flex:1; text-align:center;">
                    <div style="color:#9C27B0; font-size:1.3rem; font-weight:800;">13%</div>
                    <div style="color:#8899bb; font-size:0.65rem; text-transform:uppercase;">Best Practice</div>
                </div>
            </div>""", unsafe_allow_html=True)

    # ── RIGHT: institutions ────────────────────────────────────────────────
    if sel_country and right_col:
        with right_col:
            cdata2 = df_country[df_country["Country"]==sel_country].iloc[0]
            color2 = REGION_COLORS.get(cdata2["Region"], "#4FC3F7")
            institutions2 = get_institutions_for_country(sel_country)
            st.markdown(f'<div style="color:{color2}; font-size:0.75rem; font-weight:700; margin-bottom:6px;">INSTITUTIONS ({len(institutions2)})</div>', unsafe_allow_html=True)
            for inst in institutions2:
                if inst["url"]:
                    label = (
                        f'🎓 <a href="{inst["url"]}" target="_blank" rel="noopener" '
                        f'style="color:#4FC3F7; text-decoration:underline;">{inst["name"]} 🔗</a>'
                    )
                else:
                    label = f'🎓 {inst["name"]}'
                st.markdown(f'<div style="background:#1a2744; border-left:3px solid {color2}; padding:5px 8px; margin:3px 0; border-radius:0 6px 6px 0; font-size:0.7rem; color:#cce4ff;">{label}</div>', unsafe_allow_html=True)
