// Sample data for LegalVision demo

export interface Document {
  id: string;
  name: string;
  type: 'sale' | 'gift' | 'mortgage' | 'partition' | 'lease';
  uploadedAt: string;
  status: 'analyzed' | 'pending' | 'error';
  riskLevel: 'low' | 'medium' | 'high';
  riskCount: number;
  pages: number;
  size: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  citations?: string[];
}

export interface GraphNode {
  id: string;
  label: string;
  type: 'PERSON' | 'PROPERTY' | 'DOCUMENT' | 'ORGANIZATION' | 'LOCATION';
  data: Record<string, string>;
}

export interface GraphEdge {
  id: string;
  from: string;
  to: string;
  type: 'OWNS' | 'TRANSFERRED_TO' | 'LOCATED_IN' | 'REFERENCES' | 'MORTGAGED_TO';
  label: string;
}

export interface RiskItem {
  id: string;
  title: string;
  description: string;
  recommendation: string;
  priority: 'high' | 'medium' | 'low';
  category: 'compliance' | 'financial' | 'title' | 'party' | 'legal' | 'fraud';
  resolved: boolean;
}

export const sampleDocuments: Document[] = [
  {
    id: 'doc_001',
    name: 'Sale_Deed_Colombo_2024.pdf',
    type: 'sale',
    uploadedAt: '2024-03-15T10:30:00',
    status: 'analyzed',
    riskLevel: 'low',
    riskCount: 0,
    pages: 8,
    size: '2.3 MB'
  },
  {
    id: 'doc_002',
    name: 'Gift_Deed_Gampaha.pdf',
    type: 'gift',
    uploadedAt: '2024-03-14T14:20:00',
    status: 'analyzed',
    riskLevel: 'low',
    riskCount: 0,
    pages: 5,
    size: '1.8 MB'
  },
  {
    id: 'doc_003',
    name: 'Mortgage_Bond_Kandy.pdf',
    type: 'mortgage',
    uploadedAt: '2024-03-13T09:15:00',
    status: 'analyzed',
    riskLevel: 'medium',
    riskCount: 2,
    pages: 12,
    size: '3.1 MB'
  },
  {
    id: 'doc_004',
    name: 'Partition_Deed_Matara.pdf',
    type: 'partition',
    uploadedAt: '2024-03-12T16:45:00',
    status: 'analyzed',
    riskLevel: 'low',
    riskCount: 0,
    pages: 15,
    size: '4.2 MB'
  },
  {
    id: 'doc_005',
    name: 'Lease_Agreement_Jaffna.pdf',
    type: 'lease',
    uploadedAt: '2024-03-11T11:00:00',
    status: 'pending',
    riskLevel: 'low',
    riskCount: 0,
    pages: 6,
    size: '1.5 MB'
  }
];

export const sampleChatMessages: ChatMessage[] = [
  {
    id: 'msg_001',
    role: 'assistant',
    content: `Hello! I'm your Sri Lankan Property Law Assistant. I can help you with questions about:

• Property transfers & sale deeds
• Prescription & adverse possession
• Title registration (Bim Saviya)
• Partition of co-owned land
• Mortgages & leases

How can I assist you today?`,
    timestamp: '2024-03-15T10:00:00'
  }
];

export const sampleGraphNodes: GraphNode[] = [
  { id: '1', label: 'Kamal Silva', type: 'PERSON', data: { nic: '812345678V', address: '45, Galle Road, Colombo 03' } },
  { id: '2', label: 'Nimal Perera', type: 'PERSON', data: { nic: '901234567V', address: '78, Main Street, Nugegoda' } },
  { id: '3', label: 'Lot 1 & 2A, Plan 1234', type: 'PROPERTY', data: { extent: '0A-2R-15.5P', assessment: '123/A' } },
  { id: '4', label: 'Deed A 1234/2024', type: 'DOCUMENT', data: { type: 'Sale Transfer', date: '2024-03-15' } },
  { id: '5', label: 'Colombo', type: 'LOCATION', data: { district: 'Colombo', province: 'Western' } },
  { id: '6', label: 'Deed B 5678/2015', type: 'DOCUMENT', data: { type: 'Sale Transfer', date: '2015-06-20' } },
  { id: '7', label: 'Sunil Fernando', type: 'PERSON', data: { nic: '751234567V', address: '12, Temple Road, Gampaha' } },
  { id: '8', label: 'Bank of Ceylon', type: 'ORGANIZATION', data: { branch: 'Colombo Main', type: 'Bank' } },
];

export const sampleGraphEdges: GraphEdge[] = [
  { id: 'e1', from: '1', to: '3', type: 'OWNS', label: 'owned (until 2024)' },
  { id: 'e2', from: '1', to: '2', type: 'TRANSFERRED_TO', label: 'sold to' },
  { id: 'e3', from: '2', to: '3', type: 'OWNS', label: 'owns (current)' },
  { id: 'e4', from: '4', to: '3', type: 'REFERENCES', label: 'documents' },
  { id: 'e5', from: '3', to: '5', type: 'LOCATED_IN', label: 'located in' },
  { id: 'e6', from: '6', to: '4', type: 'REFERENCES', label: 'prior deed' },
  { id: 'e7', from: '7', to: '1', type: 'TRANSFERRED_TO', label: 'sold to (2015)' },
  { id: 'e8', from: '3', to: '8', type: 'MORTGAGED_TO', label: 'mortgaged (2018-2023)' },
];

export const sampleRiskItems: RiskItem[] = [
  {
    id: 'risk_001',
    title: 'Registration Deadline Risk',
    description: 'The deed was executed on March 15, 2024 but registration date is not confirmed. Under the Registration of Documents Ordinance, deeds must be registered within 3 months.',
    recommendation: 'Verify registration status immediately and ensure registration is completed before the deadline.',
    priority: 'high',
    category: 'compliance',
    resolved: false
  },
  {
    id: 'risk_002',
    title: 'Missing Witness Information',
    description: 'Only one witness signature clearly identified. The Prevention of Frauds Ordinance requires two witnesses for valid execution.',
    recommendation: 'Verify second witness details in the original document and ensure proper attestation.',
    priority: 'high',
    category: 'legal',
    resolved: false
  },
  {
    id: 'risk_003',
    title: 'Consideration Amount Verification',
    description: 'The stated consideration (LKR 5,500,000) appears below market value for properties in Colombo 03 area based on current valuations.',
    recommendation: 'Verify if stamp duty was calculated correctly and consider obtaining an independent valuation.',
    priority: 'medium',
    category: 'financial',
    resolved: false
  },
  {
    id: 'risk_004',
    title: 'Prior Deed Chain Note',
    description: 'Prior deeds B 5678/2015 and C 9012/2010 are referenced. Full chain verification recommended for complete title search.',
    recommendation: 'Conduct a comprehensive title search to verify the complete chain of ownership.',
    priority: 'low',
    category: 'title',
    resolved: false
  },
  {
    id: 'risk_005',
    title: 'Boundary Description Clarity',
    description: 'Western boundary described as "Canal reservation" requires confirmation of exact demarcation and any government restrictions.',
    recommendation: 'Verify boundary with Survey Department records and check for any canal reservation regulations.',
    priority: 'medium',
    category: 'legal',
    resolved: false
  },
  {
    id: 'risk_006',
    title: 'No Encumbrance Certificate',
    description: 'No encumbrance certificate referenced in the document. This is standard practice for property transfers.',
    recommendation: 'Obtain and verify a recent No Encumbrance Certificate from the Land Registry.',
    priority: 'medium',
    category: 'compliance',
    resolved: false
  }
];

export const extractedDeedData = {
  documentInfo: {
    type: 'Sale Transfer Deed',
    date: 'March 15, 2024',
    registry: 'Colombo',
    code: 'A 1234/2024',
    pages: 8,
    confidence: 94
  },
  parties: {
    vendor: {
      name: 'Kamal Bandara Silva',
      nic: '812345678V',
      address: '45, Galle Road, Colombo 03'
    },
    vendee: {
      name: 'Nimal Jayawardena Perera',
      nic: '901234567V',
      address: '78, Main Street, Nugegoda'
    }
  },
  property: {
    planNumber: '1234/2020',
    lotNumbers: '1, 2A',
    extent: '0A-2R-15.5P',
    assessmentNo: '123/A',
    boundaries: {
      north: 'Galle Road',
      east: 'Lot 3 of Plan 1234/2020',
      south: 'Land belonging to Siriwardena',
      west: 'Canal reservation'
    }
  },
  administrative: {
    district: 'Colombo',
    province: 'Western',
    dsDivision: 'Thimbirigasyaya',
    registry: 'Colombo Land Registry'
  },
  consideration: 'LKR 5,500,000',
  priorDeeds: ['B 5678/2015', 'C 9012/2010'],
  summary: `This is a Sale Transfer Deed executed on March 15, 2024, transferring property located in Colombo District from Kamal Bandara Silva to Nimal Jayawardena Perera for a consideration of LKR 5,500,000.

The property comprises Lots 1 and 2A of Plan No. 1234/2020, with an extent of 0A-2R-15.5P, bounded by Galle Road to the North and Canal reservation to the West.

Key Legal Points:
• Transfer complies with Prevention of Frauds Ordinance
• Prior deed chain verified (B 5678/2015, C 9012/2010)
• No encumbrances noted`
};

export const suggestedQuestions = [
  'How many years for prescriptive title?',
  'Can foreigners own land in Sri Lanka?',
  'What is Bim Saviya?',
  'Can co-owners compel partition?',
  'What are stamp duty rates?',
  'How to register a deed?'
];

export const dashboardStats = {
  documentsAnalyzed: 24,
  documentsChange: 12,
  queriesProcessed: 18,
  queriesChange: 8,
  entitiesExtracted: 156,
  entitiesChange: 23,
  risksFound: 3,
  risksChange: -5
};

export const weeklyData = [
  { day: 'Mon', documents: 3 },
  { day: 'Tue', documents: 5 },
  { day: 'Wed', documents: 4 },
  { day: 'Thu', documents: 6 },
  { day: 'Fri', documents: 3 },
  { day: 'Sat', documents: 2 },
  { day: 'Sun', documents: 1 },
];
