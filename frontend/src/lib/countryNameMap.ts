// The live scraper picks up whatever country name AFUGN's site literally uses
// (sometimes the formal/long form), which doesn't always match the shorter
// display names used in this dashboard's static lat/lon table. Ported from
// API_TO_STATIC_COUNTRY_NAME / STATIC_TO_API_COUNTRY_NAME in app.py.
export const API_TO_STATIC_COUNTRY_NAME: Record<string, string> = {
  "United States of America": "United States",
  "Hong Kong Special Administrative Region of the People's Republic of China": "Hong Kong SAR",
};

export const STATIC_TO_API_COUNTRY_NAME: Record<string, string> = Object.fromEntries(
  Object.entries(API_TO_STATIC_COUNTRY_NAME).map(([api, staticName]) => [staticName, api]),
);

export function toStaticCountryName(apiName: string): string {
  return API_TO_STATIC_COUNTRY_NAME[apiName] ?? apiName;
}

export function toApiCountryName(staticName: string): string {
  return STATIC_TO_API_COUNTRY_NAME[staticName] ?? staticName;
}
