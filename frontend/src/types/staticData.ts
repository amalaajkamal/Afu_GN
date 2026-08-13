export type GapFlag = "Well Implemented" | "Moderately Implemented" | "Underimplemented";

export interface Principle {
  principleNumber: number;
  shortLabel: string;
  mentions: number;
  pct: number;
  gapFlag: GapFlag;
}

export interface BestPractice {
  title: string;
  university: string;
  principles: number[];
  audience: string[];
  purpose: string;
  outcomes: string;
  unique: string;
  duration: string;
  type: string;
  challenges: string;
}

export interface Population65Entry {
  pop65: number;
  perMillionSeniors: number;
}

export type Population65Map = Record<string, Population65Entry>;

export interface StaticCountry {
  country: string;
  region: string;
  afuMembers: number;
  latitude: number;
  longitude: number;
}

export interface StaticRegion {
  region: string;
  countriesInAfu: number;
  totalCountries: number;
  afuInstitutions: number;
}

export interface StaticCountrySnapshot {
  countries: StaticCountry[];
  regions: StaticRegion[];
  institutionsByCountry: Record<string, string[]>;
}
