#!/usr/bin/env node
// Copies/derives the frontend's static data files from the repo-root CSVs
// and geojson that app.py also reads from. This script only *reads* those
// source files and writes into frontend/public/data/ — it never modifies
// anything in the repo root. Re-run manually after the source CSVs change.
//
//   node scripts/sync-static-data.mjs
import { readFileSync, writeFileSync, copyFileSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { csvToObjects } from "./csv.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, "..", "..");
const OUT_DIR = join(__dirname, "..", "public", "data");

mkdirSync(OUT_DIR, { recursive: true });

function write(name, data) {
  writeFileSync(join(OUT_DIR, name), JSON.stringify(data, null, 2) + "\n", "utf-8");
  console.log(`  wrote ${name}`);
}

// ── 1. AFU principles table ────────────────────────────────────────────────
// Ported verbatim from load_principles_data() in app.py.
const PRINCIPLES = [
  [1, "P1: Encourage participation of older adults", 20, 71.0, "Well Implemented"],
  [2, "P2: Personal & career development", 9, 32.0, "Moderately Implemented"],
  [3, "P3: Recognize educational needs", 8, 29.0, "Moderately Implemented"],
  [4, "P4: Intergenerational learning", 15, 54.0, "Well Implemented"],
  [5, "P5: Online access for older adults", 4, 14.0, "Underimplemented"],
  [6, "P6: Research agenda informed by aging", 14, 50.0, "Well Implemented"],
  [7, "P7: Student understanding of longevity", 5, 18.0, "Underimplemented"],
  [8, "P8: Health, wellness & cultural access", 13, 46.0, "Well Implemented"],
  [9, "P9: Engage retired community", 7, 25.0, "Moderately Implemented"],
  [10, "P10: Dialogue with aging organizations", 6, 21.0, "Underimplemented"],
].map(([number, label, mentions, pct, gapFlag]) => ({
  principleNumber: number,
  shortLabel: label,
  mentions,
  pct,
  gapFlag,
}));

// ── 2. Population 65+ figures (World Bank SP.POP.65UP.TO, 2025) ───────────
// Ported verbatim from the pop65_dict literal in app.py's Regional Equity
// page — app.py does not compute this from populatio_65+_worldbank.csv at
// runtime either, it's a curated snapshot keyed to this dashboard's country
// names, so the safest "single source of truth" to copy is that literal.
const POPULATION_65 = {
  "United States": { pop65: 62844750, perMillionSeniors: 1.671 },
  Canada: { pop65: 8438778, perMillionSeniors: 1.422 },
  Ireland: { pop65: 888912, perMillionSeniors: 10.125 },
  "United Kingdom": { pop65: 13690810, perMillionSeniors: 0.146 },
  Portugal: { pop65: 2695018, perMillionSeniors: 0.742 },
  Spain: { pop65: 10681480, perMillionSeniors: 0.187 },
  Croatia: { pop65: 915154, perMillionSeniors: 1.093 },
  "Czech Republic": { pop65: 2305849, perMillionSeniors: 0.434 },
  Hungary: { pop65: 2012974, perMillionSeniors: 0.497 },
  Israel: { pop65: 1284748, perMillionSeniors: 0.778 },
  Slovakia: { pop65: 1030590, perMillionSeniors: 0.97 },
  Slovenia: { pop65: 473316, perMillionSeniors: 2.113 },
  Switzerland: { pop65: 1857777, perMillionSeniors: 0.538 },
  "South Korea": { pop65: 10507688, perMillionSeniors: 0.286 },
  China: { pop65: 209741958, perMillionSeniors: 0.005 },
  Philippines: { pop65: 6684893, perMillionSeniors: 0.15 },
  "Hong Kong SAR": { pop65: 1774789, perMillionSeniors: 0.563 },
  Australia: { pop65: 4996279, perMillionSeniors: 0.4 },
  Brazil: { pop65: 24431586, perMillionSeniors: 0.123 },
  Chile: { pop65: 2897512, perMillionSeniors: 0.69 },
  Turkey: { pop65: 9078171, perMillionSeniors: 0.11 },
  Mexico: { pop65: 9831957, perMillionSeniors: 0.102 },
};

// ── 3. Static country/regional snapshot + institution fallback list ───────
// Ported verbatim from load_static_country_data() / load_static_regional_data()
// / STATIC_INSTITUTIONS in app.py — used only when the live api.py is
// unreachable, exactly as in the existing Streamlit dashboard.
const STATIC_COUNTRIES = [
  ["United States", "North America", 105, 37.09, -95.71],
  ["Canada", "North America", 12, 56.13, -106.35],
  ["Mexico", "North America", 1, 23.63, -102.55],
  ["Ireland", "Europe", 9, 53.41, -8.24],
  ["United Kingdom", "Europe", 2, 55.37, -3.43],
  ["Portugal", "Europe", 2, 39.39, -8.22],
  ["Spain", "Europe", 2, 40.46, -3.74],
  ["Croatia", "Europe", 1, 45.1, 15.2],
  ["Czech Republic", "Europe", 1, 49.81, 15.47],
  ["Hungary", "Europe", 1, 47.16, 19.5],
  ["Israel", "Europe", 1, 31.04, 34.85],
  ["Slovakia", "Europe", 1, 48.66, 19.69],
  ["Slovenia", "Europe", 1, 46.15, 14.99],
  ["Switzerland", "Europe", 1, 46.81, 8.22],
  ["South Korea", "Asia", 3, 35.9, 127.76],
  ["Turkey", "Asia", 1, 39.92, 32.85],
  ["China", "Asia", 1, 35.86, 104.19],
  ["Philippines", "Asia", 1, 12.87, 121.77],
  ["Hong Kong SAR", "Asia", 1, 22.39, 114.1],
  ["Australia", "Oceania", 2, -25.27, 133.77],
  ["Brazil", "South America", 3, -14.23, -51.92],
  ["Chile", "South America", 2, -35.67, -71.54],
].map(([country, region, afuMembers, latitude, longitude]) => ({
  country,
  region,
  afuMembers,
  latitude,
  longitude,
}));

const STATIC_REGIONS = [
  ["North America", 3, 23, 118],
  ["Europe", 13, 44, 22],
  ["Asia", 5, 48, 7],
  ["Oceania", 1, 14, 2],
  ["South America", 2, 12, 5],
].map(([region, countriesInAfu, totalCountries, afuInstitutions]) => ({
  region,
  countriesInAfu,
  totalCountries,
  afuInstitutions,
}));

const STATIC_INSTITUTIONS = {
  "United States": ["University of Minnesota","University of Massachusetts Boston","Arizona State University","Duke University","Rochester Institute of Technology","University of North Carolina Wilmington","University of Michigan","Middle Tennessee State University","University of South Florida","University of New Hampshire","University of Arizona","California State University San Bernardino","California State University Fullerton","California State University Long Beach","Dominican University of California","Fielding Graduate University","Los Angeles Pierce College","Palo Alto University","San Diego State University","Santa Monica College","UCLA","UC Berkeley","University of San Francisco","University of Southern California","University of the Pacific","Colorado State University","University of Colorado Denver","University of Colorado Anschutz","University of Colorado Colorado Springs","Central Connecticut State University","Goodwin University","Quinnipiac University","University of Bridgeport","University of Connecticut","University of Hartford","Florida Atlantic University","Florida State University","Eckerd College","St. Thomas University","Georgia State University","University of North Georgia","University of Hawaii at Manoa","Northeastern Illinois University","University of Illinois Urbana-Champaign","Concordia University Chicago","Purdue University","University of Indianapolis","Wichita State University","Frontier Nursing University","Northern Kentucky University","Western Kentucky University","Franciscan Missionaries of Our Lady University","University of Maine","University of New England","Towson University","University of Maryland Baltimore","University of Maryland Baltimore County","Lasell University","UMass Amherst","UMass Dartmouth","UMass Lowell","UMass Medical School","Springfield College","William James College","Eastern Michigan University","Michigan State University","Wayne State University","University of Minnesota Duluth","University of St Thomas","St Catherine University","St Cloud State University","Mississippi State University","University of Mississippi","Missouri State University","Washington University in St Louis","University of Montana","University of Nebraska at Omaha","Fairleigh Dickinson University","Stockton University","Hofstra University","Hunter College CUNY","Ithaca College","Purchase College SUNY","Cleveland State University","Miami University","University of Akron","University of Cincinnati","University of Central Oklahoma","Portland State University","Southern Oregon University","Western Oregon University","Drexel University","Pennsylvania State University","University of Rhode Island","East Tennessee State University","Tennessee State University","University of Texas at Austin","University of Utah","University of Vermont","Virginia Commonwealth University","Shepherd University","West Virginia University","University of Wisconsin La Crosse","University of Wisconsin Green Bay","University of Wisconsin Superior"],
  Canada: ["University of Calgary","Kwantlen Polytechnic University","University of British Columbia","UBC Okanagan","University of the Fraser Valley","Niagara College","McMaster University","Toronto Metropolitan University","Trent University","Ontario Tech University (UOIT)","University of Windsor","University of Manitoba"],
  Mexico: ["ITESO, Universidad Jesuita de Guadalajara"],
  Ireland: ["Atlantic Technological University","Dublin City University","Mary Immaculate College","Munster Technological University","National College of Ireland","Royal College of Surgeons Ireland","Trinity College Dublin","University College Dublin","University of Limerick"],
  "United Kingdom": ["University of Strathclyde","Ulster University"],
  Portugal: ["ISEG — Lisbon School of Economics","Escola Superior de Saude de Santa Maria"],
  Spain: ["University of Murcia","Universitat Internacional de Catalunya"],
  Croatia: ["University of Rijeka"],
  "Czech Republic": ["Masaryk University"],
  Hungary: ["John von Neumann University"],
  Israel: ["University of Haifa"],
  Slovakia: ["Comenius University Bratislava"],
  Slovenia: ["University of Maribor"],
  Switzerland: ["University of Zurich"],
  "South Korea": ["Chosun University","Paichai University","Yonsei University"],
  China: ["Open University of China (Seniors University of China)"],
  Philippines: ["University of the Philippines"],
  "Hong Kong SAR": ["Chinese University of Hong Kong"],
  Turkey: ["Istanbul Nişantaşı University"],
  Australia: ["University of Queensland","University of the Sunshine Coast"],
  Brazil: ["Pontifical Catholic University of Campinas","Federal University of Technology Parana","Universidade Federal de Vicosa"],
  Chile: ["Instituto Profesional AIEP","University of Talca"],
};

// ── 4. Best Practices submissions, parsed from the repo's CSV ─────────────
function extractPrinciples(value) {
  if (!value) return [];
  const nums = [...value.matchAll(/Principle\s*(\d+)/g)].map((m) => Number(m[1]));
  return [...new Set(nums)].sort((a, b) => a - b);
}

function buildBestPractices() {
  const csvText = readFileSync(join(REPO_ROOT, "Form_Data_Entry-Grid_view.csv"), "utf-8");
  const rows = csvToObjects(csvText);

  const findCol = (headers, needle) =>
    headers.find((h) => h.toLowerCase().includes(needle.toLowerCase()));

  const headers = Object.keys(rows[0] ?? {});
  const cols = {
    title: findCol(headers, "Title") ?? "Title of Activity",
    principles: headers.find((h) => h.includes("Principle(s)")),
    audience: findCol(headers, "aimed at"),
    purpose: findCol(headers, "primary purpose"),
    outcomes: findCol(headers, "outcomes"),
    unique: findCol(headers, "unique"),
    duration: findCol(headers, "How long"),
    type: findCol(headers, "Type of Activity"),
    university: findCol(headers, "Submitting University"),
    challenges: findCol(headers, "challenges"),
  };

  return rows.map((row) => ({
    title: row[cols.title] || "",
    university: row[cols.university] || "",
    principles: extractPrinciples(row[cols.principles]),
    audience: (row[cols.audience] || "")
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean),
    purpose: row[cols.purpose] || "",
    outcomes: row[cols.outcomes] || "",
    unique: row[cols.unique] || "",
    duration: row[cols.duration] || "",
    type: row[cols.type] || "",
    challenges: row[cols.challenges] || "",
  }));
}

console.log("Syncing static data into frontend/public/data/ ...");
write("principles.json", PRINCIPLES);
write("population_65.json", POPULATION_65);
write("static_country_snapshot.json", {
  countries: STATIC_COUNTRIES,
  regions: STATIC_REGIONS,
  institutionsByCountry: STATIC_INSTITUTIONS,
});
write("best_practices.json", buildBestPractices());

copyFileSync(join(REPO_ROOT, "india_outline.geojson"), join(OUT_DIR, "india_outline.geojson"));
console.log("  copied india_outline.geojson");

console.log("Done.");
