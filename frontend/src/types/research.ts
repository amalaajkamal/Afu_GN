export interface Authorship {
  author_id: string | null;
  author_name: string | null;
  institution: string | null;
}

export interface Paper {
  id: string | null;
  title: string | null;
  publication_year: number | null;
  doi: string | null;
  cited_by_count: number;
  venue: string | null;
  oa_url: string | null;
  authorships: Authorship[];
}

export interface Researcher {
  id: string;
  name: string;
  institutions: string[];
  paper_count: number;
  total_citations: number;
}

export interface PapersResponse {
  count: number;
  results: Paper[];
}

export interface ResearchersResponse {
  count: number;
  results: Researcher[];
}

export interface ResearchMeta {
  total_papers: number;
  total_researchers: number;
  total_citations: number;
  fetched_at: number | null;
  cache_age_seconds: number | null;
}
