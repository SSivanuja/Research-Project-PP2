// LegalVision API Client
// Base URL is configurable - set VITE_API_BASE_URL in environment or it defaults to localhost

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function apiRequest<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API Error: ${response.status}`);
  }

  return response.json();
}

// ─── Types ───────────────────────────────────────────────────────────

export interface QueryRequest {
  query: string;
  session_id: string;
  include_reasoning?: boolean;
}

export interface ReasoningStep {
  step: number;
  text: string;
  legal_basis: string | null;
}

export interface IRACAnalysis {
  issue: string;
  rule: string;
  application: string;
  conclusion: string;
}

export interface QueryResponse {
  query: string;
  intent: string;
  query_type: string;
  answer: string;
  reasoning_steps: ReasoningStep[];
  irac_analysis: IRACAnalysis | null;
  sources: string[];
  related_statutes: string[];
  confidence: number;
  data: {
    results_count: number;
    session_id: string;
  };
}

export interface StatsResponse {
  total_deeds: number;
  total_persons: number;
  total_properties: number;
  total_districts: number;
  total_statutes: number;
  total_definitions: number;
  deed_breakdown: Record<string, number>;
}

export interface SearchResult {
  name: string;
  code: string | null;
  extra: string | null;
}

export interface SearchResponse {
  query: string;
  total_results: number;
  results_by_type: Record<string, SearchResult[]>;
}

export interface DeedParty {
  name: string;
  role: string;
  nic: string | null;
}

export interface DeedProperty {
  lot: string;
  extent: string;
  assessment_no: string;
  plan_no: string;
  plan_date: string;
  boundaries: {
    north: string;
    south: string;
    east: string;
    west: string;
  };
}

export interface DeedDetails {
  deed_code: string;
  deed_type: string;
  date: string;
  district: string;
  province: string;
  registry: string;
  amount: number;
  property: DeedProperty;
  parties: DeedParty[];
  prior_deed: string | null;
  governing_statutes: string[];
}

export interface DeedSearchResult {
  person?: string;
  role?: string;
  deed_code: string;
  deed_type: string;
  date: string;
  amount: number;
  lot?: string;
  extent?: string;
  district: string;
  parties?: DeedParty[];
  applicable_laws?: string[];
}

export interface OwnershipChainItem {
  deed: string;
  type: string;
  date: string;
  prior_reference: string | null;
  prior_deed: string | null;
  parties: { name: string; role: string }[];
}

export interface Statute {
  statute_name: string;
  short_name: string;
  act_number: string;
  year: number;
  category: string;
  description: string;
  applies_to: string[];
  section_count?: number;
  key_provisions?: string[];
  sections?: { section: string; title: string; content: string }[];
}

export interface DeedRequirement {
  deed_type: string;
  requirement_name: string;
  requirements: string[];
  stamp_duty: string;
  registration_fee: string;
  governing_statutes: string[];
}

export interface LegalDefinition {
  term: string;
  definition: string;
  source: string;
}

export interface LegalPrinciple {
  principle_name: string;
  english_meaning: string;
  description: string;
  application: string;
}

export interface ComplianceItem {
  requirement: string;
  status: 'met' | 'not_met';
  details: string | null;
}

export interface ComplianceResponse {
  deed_code: string;
  deed_type: string;
  is_compliant: boolean;
  compliance_score: number;
  items: ComplianceItem[];
  governing_statutes: string[];
  recommendations: string[];
}

export interface ValidationChecklist {
  deed_type: string;
  checklist: {
    item: string;
    category: string;
    mandatory: boolean;
  }[];
  governing_statutes: string[];
  notes: string[];
}

export interface LegalReasonRequest {
  question: string;
  deed_code?: string | null;
  deed_type?: string | null;
  include_irac?: boolean;
}

export interface LegalReasonResponse {
  question: string;
  deed_code: string | null;
  deed_type: string | null;
  answer: string;
  irac_analysis: IRACAnalysis | null;
  reasoning_steps: ReasoningStep[];
  referenced_statutes: string[];
  confidence: number;
}

export interface SessionContext {
  session_id: string;
  context: Record<string, string | null>;
  history_count: number;
  recent_queries: string[];
}

// ─── API Functions ───────────────────────────────────────────────────

// 1. Natural Language Query
export const postQuery = (data: QueryRequest) =>
  apiRequest<QueryResponse>('/api/v1/query', {
    method: 'POST',
    body: JSON.stringify(data),
  });

// 2. Get Statistics
export const getStats = () =>
  apiRequest<StatsResponse>('/api/v1/stats');

// 3. General Search
export const search = (q: string) =>
  apiRequest<SearchResponse>(`/api/v1/search?q=${encodeURIComponent(q)}`);

// 4. Get Deed Details
export const getDeedDetails = (deedCode: string) =>
  apiRequest<DeedDetails>(`/api/v1/deeds/${encodeURIComponent(deedCode)}`);

// 5. Get Deed Parties
export const getDeedParties = (deedCode: string) =>
  apiRequest<{ deed_code: string; parties: DeedParty[] }>(
    `/api/v1/deeds/${encodeURIComponent(deedCode)}/parties`
  );

// 6. Get Deed Boundaries
export const getDeedBoundaries = (deedCode: string) =>
  apiRequest<{ deed_code: string; lot: string; extent: string; boundaries: Record<string, string> }>(
    `/api/v1/deeds/${encodeURIComponent(deedCode)}/boundaries`
  );

// 7. Get Ownership History
export const getDeedHistory = (deedCode: string) =>
  apiRequest<{ deed_code: string; chain: OwnershipChainItem[] }>(
    `/api/v1/deeds/${encodeURIComponent(deedCode)}/history`
  );

// 8. Search Deeds by Person
export const getDeedsByPerson = (name: string, limit = 10) =>
  apiRequest<{ person: string; count: number; deeds: DeedSearchResult[] }>(
    `/api/v1/deeds/by-person/${encodeURIComponent(name)}?limit=${limit}`
  );

// 9. Search Deeds by District
export const getDeedsByDistrict = (district: string, limit = 10) =>
  apiRequest<{ district: string; count: number; deeds: DeedSearchResult[] }>(
    `/api/v1/deeds/by-district/${encodeURIComponent(district)}?limit=${limit}`
  );

// 10. Search Deeds by Type
export const getDeedsByType = (deedType: string, limit = 10) =>
  apiRequest<{ deed_type: string; count: number; deeds: DeedSearchResult[] }>(
    `/api/v1/deeds/by-type/${encodeURIComponent(deedType)}?limit=${limit}`
  );

// 11. List All Statutes
export const getStatutes = () =>
  apiRequest<Statute[]>('/api/v1/legal/statutes');

// 12. Search Statutes
export const searchStatutes = (q: string) =>
  apiRequest<{ query: string; count: number; statutes: Statute[] }>(
    `/api/v1/legal/statutes/search?q=${encodeURIComponent(q)}`
  );

// 13. Get Deed Requirements
export const getDeedRequirements = (deedType: string) =>
  apiRequest<{ deed_type: string; found: boolean; requirements: DeedRequirement[] }>(
    `/api/v1/legal/requirements/${encodeURIComponent(deedType)}`
  );

// 14. List Legal Definitions
export const getDefinitions = () =>
  apiRequest<LegalDefinition[]>('/api/v1/definitions/');

// 15. Search Definitions
export const searchDefinitions = (q: string) =>
  apiRequest<{ query: string; count: number; definitions: LegalDefinition[] }>(
    `/api/v1/definitions/search?q=${encodeURIComponent(q)}`
  );

// 16. List Legal Principles
export const getLegalPrinciples = () =>
  apiRequest<LegalPrinciple[]>('/api/v1/legal/principles');

// 17. Check Deed Compliance
export const checkCompliance = (deedCode: string) =>
  apiRequest<ComplianceResponse>('/api/v1/compliance/check', {
    method: 'POST',
    body: JSON.stringify({ deed_code: deedCode }),
  });

// 18. Get Validation Checklist
export const getValidationChecklist = (deedType: string) =>
  apiRequest<ValidationChecklist>(
    `/api/v1/compliance/validate/${encodeURIComponent(deedType)}`
  );

// 19. Legal Reasoning Query
export const postLegalReason = (data: LegalReasonRequest) =>
  apiRequest<LegalReasonResponse>('/api/v1/legal/reason', {
    method: 'POST',
    body: JSON.stringify(data),
  });

// 20. Session Context
export const getSessionContext = (sessionId: string) =>
  apiRequest<SessionContext>(`/api/v1/session/${encodeURIComponent(sessionId)}/context`);

export const clearSession = (sessionId: string) =>
  apiRequest<{ status: string }>(`/api/v1/session/${encodeURIComponent(sessionId)}/clear`, {
    method: 'POST',
  });

export { API_BASE_URL };
