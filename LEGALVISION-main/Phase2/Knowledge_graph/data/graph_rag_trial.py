"""
LegalVision GraphRAG - Enhanced Graph-based RAG for Legal Deed Queries
Uses Neo4j Knowledge Graph + OpenAI GPT-4o

Features:
- Conversation context/memory for follow-up questions
- Enhanced intent detection with multiple patterns
- Boundary/neighbor search
- Ownership chain tracking
- Fuzzy matching and synonyms
"""

import os
import re
from dotenv import load_dotenv
from neo4j import GraphDatabase
from openai import OpenAI

load_dotenv()

# Configuration
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class LegalGraphRAG:
    """Enhanced GraphRAG for querying Sri Lankan legal deed knowledge graph."""

    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        self.openai = OpenAI(api_key=OPENAI_API_KEY)
        
        # Conversation context for follow-up questions
        self.conversation_history = []
        self.last_context = {
            "deed_code": None,
            "lot": None,
            "district": None,
            "person": None,
            "property_id": None,
            "last_intent": None,
            "last_results": None
        }
        
        # Synonyms for better understanding
        self.synonyms = {
            "seller": "vendor",
            "buyer": "vendee",
            "purchaser": "vendee",
            "giver": "donor",
            "receiver": "donee",
            "recipient": "donee",
            "owner": "vendor",
            "notary public": "notary",
            "land": "property",
            "plot": "lot",
            "parcel": "property",
            "transfer": "sale_transfer",
            "sale": "sale_transfer",
            "adjacent": "boundary",
            "neighbor": "boundary",
            "neighbouring": "boundary",
            "next to": "boundary",
            "beside": "boundary",
        }

        self.system_prompt = """You are a legal assistant specialized in Sri Lankan property law.
You help users understand property deeds, ownership transfers, and legal documents.

You have access to a knowledge graph containing:
- Instruments (deeds): sale transfers, gifts, wills, mortgages, leases
- Parties: vendors, vendees, donors, donees, testators, notaries
- Properties: parcels with lot numbers, plans, extents, boundaries
- Locations: districts, provinces, registry offices

When answering:
1. Use the provided graph data to give accurate, specific answers
2. Reference deed numbers, party names, and property details when available
3. If data is insufficient, say so clearly
4. Explain legal concepts in simple terms when needed
5. Always be helpful and professional
6. When showing boundaries, clearly list North, South, East, West
7. Format monetary amounts with proper separators"""

    def close(self):
        self.driver.close()
    
    def clear_context(self):
        """Clear conversation context."""
        self.conversation_history = []
        self.last_context = {
            "deed_code": None,
            "lot": None,
            "district": None,
            "person": None,
            "property_id": None,
            "last_intent": None,
            "last_results": None
        }
        print("✓ Context cleared")

    # =========================================================================
    # CYPHER QUERY TEMPLATES
    # =========================================================================
    
    def get_cypher_for_intent(self, intent: str, entities: dict) -> str:
        """Get appropriate Cypher query based on detected intent."""
        
        queries = {
            # Find deeds by person name
            "find_person_deeds": """
                MATCH (p:Person)-[r:HAS_ROLE]->(i:Instrument)
                WHERE toLower(p.name) CONTAINS toLower($name)
                OPTIONAL MATCH (i)-[:CONVEYS]->(pp:PropertyParcel)
                OPTIONAL MATCH (i)-[:IN_DISTRICT]->(d:District)
                RETURN p.name AS person, r.role AS role, i.code_number AS deed_code,
                       i.type AS deed_type, i.date AS date, pp.lot AS lot,
                       pp.extent AS extent, d.name AS district,
                       pp.boundary_north AS north, pp.boundary_south AS south,
                       pp.boundary_east AS east, pp.boundary_west AS west
                LIMIT 10
            """,
            
            # Find deeds by district
            "find_district_deeds": """
                MATCH (i:Instrument)-[:IN_DISTRICT]->(d:District)
                WHERE toLower(d.name) CONTAINS toLower($district)
                OPTIONAL MATCH (p:Person)-[r:HAS_ROLE]->(i)
                OPTIONAL MATCH (i)-[:CONVEYS]->(pp:PropertyParcel)
                RETURN i.code_number AS deed_code, i.type AS deed_type, i.date AS date,
                       d.name AS district, collect(DISTINCT {name: p.name, role: r.role}) AS parties,
                       pp.lot AS lot, pp.extent AS extent
                LIMIT 10
            """,

            # Find property by boundary/neighbor name
            "find_by_boundary": """
                MATCH (pp:PropertyParcel)
                WHERE toLower(pp.boundary_north) CONTAINS toLower($name)
                   OR toLower(pp.boundary_south) CONTAINS toLower($name)
                   OR toLower(pp.boundary_east) CONTAINS toLower($name)
                   OR toLower(pp.boundary_west) CONTAINS toLower($name)
                OPTIONAL MATCH (i:Instrument)-[:CONVEYS]->(pp)
                OPTIONAL MATCH (i)-[:IN_DISTRICT]->(d:District)
                OPTIONAL MATCH (p:Person)-[r:HAS_ROLE]->(i)
                RETURN pp.lot AS lot, pp.extent AS extent, pp.assessment_no AS assessment,
                       pp.boundary_north AS north, pp.boundary_south AS south,
                       pp.boundary_east AS east, pp.boundary_west AS west,
                       i.code_number AS deed_code, i.type AS deed_type, i.date AS date,
                       d.name AS district,
                       collect(DISTINCT {name: p.name, role: r.role}) AS parties
                LIMIT 10
            """,
            
            # Find deed by code/number - comprehensive details
            "find_deed_details": """
                MATCH (i:Instrument)
                WHERE i.code_number CONTAINS $code OR i.id CONTAINS $code
                OPTIONAL MATCH (p:Person)-[r:HAS_ROLE]->(i)
                OPTIONAL MATCH (i)-[:CONVEYS]->(pp:PropertyParcel)
                OPTIONAL MATCH (pp)-[:DEFINED_BY]->(pl:Plan)
                OPTIONAL MATCH (i)-[:IN_DISTRICT]->(d:District)
                OPTIONAL MATCH (i)-[:IN_PROVINCE]->(pv:Province)
                OPTIONAL MATCH (i)-[:REGISTERED_AT]->(ro:RegistryOffice)
                OPTIONAL MATCH (i)-[:REFERS_TO_PRIOR]->(pd:PriorDeed)
                RETURN i.code_number AS deed_code, i.type AS deed_type, i.date AS date,
                       i.consideration_lkr AS amount, d.name AS district, pv.name AS province,
                       ro.name AS registry, pl.plan_no AS plan_no, pl.plan_date AS plan_date,
                       pp.lot AS lot, pp.extent AS extent, pp.assessment_no AS assessment,
                       pp.boundary_north AS north, pp.boundary_south AS south,
                       pp.boundary_east AS east, pp.boundary_west AS west,
                       pd.reference AS prior_deed,
                       collect(DISTINCT {name: p.name, role: r.role}) AS parties
                LIMIT 1
            """,
            
            # Find boundaries specifically
            "find_boundaries": """
                MATCH (i:Instrument)
                WHERE i.code_number CONTAINS $code OR i.id CONTAINS $code
                OPTIONAL MATCH (i)-[:CONVEYS]->(pp:PropertyParcel)
                RETURN i.code_number AS deed_code, pp.lot AS lot,
                       pp.boundary_north AS north, pp.boundary_south AS south,
                       pp.boundary_east AS east, pp.boundary_west AS west,
                       pp.extent AS extent
                LIMIT 1
            """,
            
            # Find parties of a deed
            "find_deed_parties": """
                MATCH (i:Instrument)
                WHERE i.code_number CONTAINS $code OR i.id CONTAINS $code
                MATCH (p:Person)-[r:HAS_ROLE]->(i)
                RETURN i.code_number AS deed_code, i.type AS deed_type,
                       p.name AS person_name, r.role AS role
                ORDER BY r.role
            """,
            
            # Find property by lot/plan
            "find_property": """
                MATCH (pp:PropertyParcel)
                WHERE pp.lot CONTAINS $lot OR pp.plan_no CONTAINS $lot
                OPTIONAL MATCH (i:Instrument)-[:CONVEYS]->(pp)
                OPTIONAL MATCH (pp)-[:DEFINED_BY]->(pl:Plan)
                OPTIONAL MATCH (p:Person)-[r:HAS_ROLE]->(i)
                OPTIONAL MATCH (i)-[:IN_DISTRICT]->(d:District)
                RETURN pp.lot AS lot, pp.extent AS extent, pp.assessment_no AS assessment,
                       pp.boundary_north AS north, pp.boundary_south AS south,
                       pp.boundary_east AS east, pp.boundary_west AS west,
                       pl.plan_no AS plan_no, pl.plan_date AS plan_date,
                       i.code_number AS deed_code, i.type AS deed_type, i.date AS date,
                       d.name AS district,
                       collect(DISTINCT {name: p.name, role: r.role}) AS parties
                LIMIT 5
            """,
            
            # Get statistics
            "get_stats": """
                MATCH (i:Instrument)
                WITH count(i) AS total_deeds
                MATCH (p:Person)
                WITH total_deeds, count(DISTINCT p) AS total_persons
                MATCH (pp:PropertyParcel)
                WITH total_deeds, total_persons, count(pp) AS total_parcels
                MATCH (d:District)
                WITH total_deeds, total_persons, total_parcels, count(DISTINCT d) AS total_districts
                OPTIONAL MATCH (i2:Instrument)
                WITH total_deeds, total_persons, total_parcels, total_districts,
                     count(CASE WHEN i2.type = 'sale_transfer' THEN 1 END) AS sales,
                     count(CASE WHEN i2.type = 'gift' THEN 1 END) AS gifts,
                     count(CASE WHEN i2.type = 'will' THEN 1 END) AS wills,
                     count(CASE WHEN i2.type = 'lease' THEN 1 END) AS leases,
                     count(CASE WHEN i2.type = 'mortgage' THEN 1 END) AS mortgages
                RETURN total_deeds, total_persons, total_parcels, total_districts,
                       sales, gifts, wills, leases, mortgages
            """,
            
            # Find ownership chain (prior deeds)
            "find_ownership_chain": """
                MATCH (i:Instrument)
                WHERE i.code_number CONTAINS $code OR i.id CONTAINS $code
                OPTIONAL MATCH (i)-[:REFERS_TO_PRIOR]->(pd:PriorDeed)
                OPTIONAL MATCH (i)-[:DERIVES_FROM]->(prior:Instrument)
                OPTIONAL MATCH (p:Person)-[r:HAS_ROLE]->(i)
                OPTIONAL MATCH (i)-[:CONVEYS]->(pp:PropertyParcel)
                RETURN i.code_number AS current_deed, i.type AS deed_type, i.date AS date,
                       pd.reference AS prior_reference,
                       prior.code_number AS prior_deed_code,
                       pp.lot AS lot,
                       collect(DISTINCT {name: p.name, role: r.role}) AS parties
            """,
            
            # Find deeds by type
            "find_by_type": """
                MATCH (i:Instrument)
                WHERE toLower(i.type) CONTAINS toLower($deed_type)
                OPTIONAL MATCH (p:Person)-[r:HAS_ROLE]->(i)
                OPTIONAL MATCH (i)-[:CONVEYS]->(pp:PropertyParcel)
                OPTIONAL MATCH (i)-[:IN_DISTRICT]->(d:District)
                RETURN i.code_number AS deed_code, i.type AS deed_type, i.date AS date,
                       d.name AS district, pp.lot AS lot, pp.extent AS extent,
                       collect(DISTINCT {name: p.name, role: r.role}) AS parties
                LIMIT 10
            """,
            
            # Find recent deeds
            "find_recent_deeds": """
                MATCH (i:Instrument)
                WHERE i.date IS NOT NULL
                OPTIONAL MATCH (p:Person)-[r:HAS_ROLE]->(i)
                OPTIONAL MATCH (i)-[:IN_DISTRICT]->(d:District)
                RETURN i.code_number AS deed_code, i.type AS deed_type, i.date AS date,
                       d.name AS district,
                       collect(DISTINCT {name: p.name, role: r.role}) AS parties
                ORDER BY i.date DESC
                LIMIT 10
            """,
            
            # Search by amount range
            "find_by_amount": """
                MATCH (i:Instrument)
                WHERE i.consideration_lkr IS NOT NULL
                OPTIONAL MATCH (p:Person)-[r:HAS_ROLE]->(i)
                OPTIONAL MATCH (i)-[:CONVEYS]->(pp:PropertyParcel)
                OPTIONAL MATCH (i)-[:IN_DISTRICT]->(d:District)
                RETURN i.code_number AS deed_code, i.type AS deed_type, i.date AS date,
                       i.consideration_lkr AS amount, d.name AS district,
                       pp.lot AS lot,
                       collect(DISTINCT {name: p.name, role: r.role}) AS parties
                ORDER BY i.consideration_lkr DESC
                LIMIT 10
            """,
            
            # General search - comprehensive
            "general_search": """
                CALL {
                    MATCH (p:Person)
                    WHERE toLower(p.name) CONTAINS toLower($query)
                    RETURN 'Person' AS type, p.name AS name, null AS code, null AS extra
                    UNION
                    MATCH (i:Instrument)
                    WHERE i.code_number CONTAINS $query OR i.id CONTAINS $query
                           OR toLower(i.type) CONTAINS toLower($query)
                    RETURN 'Instrument' AS type, i.type AS name, i.code_number AS code, i.date AS extra
                    UNION
                    MATCH (d:District)
                    WHERE toLower(d.name) CONTAINS toLower($query)
                    RETURN 'District' AS type, d.name AS name, null AS code, null AS extra
                    UNION
                    MATCH (pp:PropertyParcel)
                    WHERE pp.lot CONTAINS $query OR pp.assessment_no CONTAINS $query
                    RETURN 'Property' AS type, pp.lot AS name, pp.assessment_no AS code, pp.extent AS extra
                    UNION
                    MATCH (pp:PropertyParcel)
                    WHERE toLower(pp.boundary_north) CONTAINS toLower($query)
                       OR toLower(pp.boundary_south) CONTAINS toLower($query)
                       OR toLower(pp.boundary_east) CONTAINS toLower($query)
                       OR toLower(pp.boundary_west) CONTAINS toLower($query)
                    RETURN 'Boundary Reference' AS type, pp.lot AS name, null AS code, 'Found in boundaries' AS extra
                }
                RETURN type, name, code, extra
                LIMIT 15
            """
        }
        
        return queries.get(intent, queries["general_search"])

    # =========================================================================
    # CONTEXT MANAGEMENT
    # =========================================================================
    
    def update_context(self, intent: str, params: dict, graph_data: list):
        """Update conversation context based on query results."""
        self.last_context["last_intent"] = intent
        self.last_context["last_results"] = graph_data
        
        # Store from params
        if "code" in params:
            self.last_context["deed_code"] = params["code"]
        if "lot" in params and params["lot"] not in ["property?", "property", "this", "that"]:
            self.last_context["lot"] = params["lot"]
        if "district" in params:
            self.last_context["district"] = params["district"]
        if "name" in params:
            self.last_context["person"] = params["name"]
        
        # Extract from results
        if graph_data:
            record = graph_data[0]
            if record.get("deed_code"):
                self.last_context["deed_code"] = record["deed_code"]
            if record.get("lot"):
                self.last_context["lot"] = record["lot"]
            if record.get("district"):
                self.last_context["district"] = record["district"]
    
    def resolve_references(self, query: str) -> str:
        """Resolve pronouns and references using conversation context."""
        query_lower = query.lower()
        
        # Reference words that indicate follow-up
        reference_words = ['this', 'that', 'it', 'its', 'the same', 'above', 'mentioned', 
                          'previous', 'these', 'those', 'their', 'the property', 'the deed']
        has_reference = any(word in query_lower for word in reference_words)
        
        if not has_reference:
            return query
        
        # Add context based on what's being asked
        additions = []
        
        if any(word in query_lower for word in ['property', 'land', 'lot', 'boundaries', 'boundary', 'parcel', 'extent']):
            if self.last_context["deed_code"]:
                additions.append(f"deed: {self.last_context['deed_code']}")
            if self.last_context["lot"]:
                additions.append(f"lot: {self.last_context['lot']}")
        
        elif any(word in query_lower for word in ['deed', 'instrument', 'document', 'transfer']):
            if self.last_context["deed_code"]:
                additions.append(f"deed code: {self.last_context['deed_code']}")
        
        elif any(word in query_lower for word in ['person', 'owner', 'party', 'vendor', 'vendee', 'who', 'parties']):
            if self.last_context["deed_code"]:
                additions.append(f"deed: {self.last_context['deed_code']}")
            elif self.last_context["person"]:
                additions.append(f"person: {self.last_context['person']}")
        
        if additions:
            return query + f" (Context: {', '.join(additions)})"
        return query

    # =========================================================================
    # INTENT DETECTION (Enhanced)
    # =========================================================================
    
    def normalize_query(self, query: str) -> str:
        """Normalize query by replacing synonyms."""
        query_lower = query.lower()
        for synonym, standard in self.synonyms.items():
            query_lower = query_lower.replace(synonym, standard)
        return query_lower
    
    def extract_person_name(self, query: str) -> str:
        """Extract person name from query."""
        # Pattern 1: UPPERCASE NAMES
        match = re.search(r'\b([A-Z]{2,}(?:\s+[A-Z]{2,})+)\b', query)
        if match:
            return match.group(1)
        
        # Pattern 2: Title Case Names
        match = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', query)
        if match:
            return match.group(1)
        
        # Pattern 3: After keywords
        for keyword in ['named', 'called', 'name', 'person', 'by', 'of', 'involving']:
            if keyword in query.lower():
                idx = query.lower().find(keyword) + len(keyword)
                remaining = query[idx:].strip()
                words = remaining.split()[:3]
                # Filter out common words
                name_words = [w for w in words if w.lower() not in 
                             ['the', 'a', 'an', 'is', 'was', 'are', 'property', 'deed', 'land']]
                if name_words:
                    return " ".join(name_words).strip('.,;:?')
        
        return None
    
    def extract_deed_code(self, query: str) -> str:
        """Extract deed code from query."""
        # Pattern: A 1100/188, A1100/188, 1100/188, etc.
        patterns = [
            r'([A-Z]\s*\d+/\d+)',  # A 1100/188 or A1100/188
            r'([A-Z]\s*\d+-\d+)',   # A 1100-188
            r'(\d+/\d+)',           # 1100/188
            r'([A-Z]\s*\d{3,})',    # A 1100
        ]
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def detect_intent(self, query: str) -> tuple:
        """Enhanced intent detection from user query."""
        query_lower = query.lower()
        normalized = self.normalize_query(query)
        
        # =====================================================================
        # STEP 1: Handle follow-up questions using context
        # =====================================================================
        reference_words = ['this', 'that', 'it', 'its', 'the same', 'these', 'those', 'their']
        has_reference = any(word in query_lower for word in reference_words)
        
        if has_reference:
            # Boundaries of "this" property
            if any(word in query_lower for word in ['boundary', 'boundaries', 'border', 'borders', 'adjacent', 'neighbor']):
                if self.last_context["deed_code"]:
                    return "find_boundaries", {"code": self.last_context["deed_code"]}
                elif self.last_context["lot"]:
                    return "find_property", {"lot": self.last_context["lot"]}
            
            # Parties of "this" deed
            if any(word in query_lower for word in ['party', 'parties', 'owner', 'vendor', 'vendee', 'who', 'involved']):
                if self.last_context["deed_code"]:
                    return "find_deed_parties", {"code": self.last_context["deed_code"]}
            
            # More details about "this" deed
            if any(word in query_lower for word in ['detail', 'more', 'about', 'tell', 'show', 'describe']):
                if self.last_context["deed_code"]:
                    return "find_deed_details", {"code": self.last_context["deed_code"]}
            
            # Extent/area of "this" property
            if any(word in query_lower for word in ['extent', 'area', 'size', 'measurement', 'how big', 'how large']):
                if self.last_context["deed_code"]:
                    return "find_deed_details", {"code": self.last_context["deed_code"]}
                elif self.last_context["lot"]:
                    return "find_property", {"lot": self.last_context["lot"]}
            
            # History/chain of "this" property
            if any(word in query_lower for word in ['history', 'chain', 'previous', 'prior', 'before']):
                if self.last_context["deed_code"]:
                    return "find_ownership_chain", {"code": self.last_context["deed_code"]}
        
        # =====================================================================
        # STEP 2: Statistics queries
        # =====================================================================
        if any(word in query_lower for word in ['how many', 'count', 'total', 'statistics', 'stats', 'summary', 'overview']):
            return "get_stats", {}
        
        # =====================================================================
        # STEP 3: Recent/latest queries
        # =====================================================================
        if any(word in query_lower for word in ['recent', 'latest', 'newest', 'last']):
            return "find_recent_deeds", {}
        
        # =====================================================================
        # STEP 4: Amount/price queries
        # =====================================================================
        if any(word in query_lower for word in ['expensive', 'costly', 'highest price', 'amount', 'price', 'value', 'consideration']):
            return "find_by_amount", {}
        
        # =====================================================================
        # STEP 5: Deed type queries
        # =====================================================================
        deed_types = {
            'sale': 'sale_transfer', 'transfer': 'sale_transfer', 'sale_transfer': 'sale_transfer',
            'gift': 'gift', 'donation': 'gift',
            'will': 'will', 'testament': 'will',
            'lease': 'lease', 'rent': 'lease',
            'mortgage': 'mortgage', 'loan': 'mortgage'
        }
        for keyword, deed_type in deed_types.items():
            if keyword in query_lower and any(w in query_lower for w in ['all', 'list', 'find', 'show', 'type']):
                return "find_by_type", {"deed_type": deed_type}
        
        # =====================================================================
        # STEP 6: Boundary/neighbor search (check early for person names with property context)
        # =====================================================================
        if any(word in query_lower for word in ['property', 'land', 'adjacent', 'neighbor', 'boundary', 'next to', 'beside', 'claimed']):
            name = self.extract_person_name(query)
            if name:
                return "find_by_boundary", {"name": name}
        
        # =====================================================================
        # STEP 7: Person/party search
        # =====================================================================
        if any(word in query_lower for word in ['who', 'person', 'owner', 'party', 'vendor', 'vendee', 'donor', 'donee', 'notary', 'involved']):
            # Check for deed code first
            code = self.extract_deed_code(query)
            if code:
                return "find_deed_parties", {"code": code}
            
            # Extract person name
            name = self.extract_person_name(query)
            if name:
                return "find_person_deeds", {"name": name}
            
            # Fallback: last word
            words = query.split()
            if words:
                return "find_person_deeds", {"name": words[-1]}
        
        # =====================================================================
        # STEP 8: District search
        # =====================================================================
        districts = ['colombo', 'gampaha', 'kandy', 'galle', 'matara', 'kalutara', 
                    'kurunegala', 'ratnapura', 'badulla', 'nuwara eliya', 'anuradhapura',
                    'polonnaruwa', 'jaffna', 'batticaloa', 'trincomalee', 'ampara',
                    'hambantota', 'puttalam', 'kegalle', 'monaragala']
        
        if 'district' in query_lower or any(d in query_lower for d in districts):
            for district in districts:
                if district in query_lower:
                    return "find_district_deeds", {"district": district}
            # Extract district name after "district"
            match = re.search(r'district\s+(?:of\s+)?(\w+)', query_lower)
            if match:
                return "find_district_deeds", {"district": match.group(1)}
        
        # =====================================================================
        # STEP 9: Deed code/details search
        # =====================================================================
        if any(word in query_lower for word in ['deed', 'instrument', 'code', 'number', 'details', 'summarize', 'summary', 'tell me about']):
            code = self.extract_deed_code(query)
            if code:
                return "find_deed_details", {"code": code}
        
        # =====================================================================
        # STEP 10: Property/lot search
        # =====================================================================
        if any(word in query_lower for word in ['lot', 'property', 'parcel', 'plan', 'land', 'plot']):
            # Lot number pattern
            lot_match = re.search(r'lot\s*([0-9A-Za-z]+)', query_lower)
            if lot_match:
                return "find_property", {"lot": lot_match.group(1).upper()}
            
            # Plan number pattern
            plan_match = re.search(r'plan\s*(?:no\.?)?\s*([0-9]+)', query_lower)
            if plan_match:
                return "find_property", {"lot": plan_match.group(1)}
        
        # =====================================================================
        # STEP 11: Ownership chain/history
        # =====================================================================
        if any(word in query_lower for word in ['chain', 'history', 'previous', 'prior', 'ownership', 'lineage']):
            code = self.extract_deed_code(query)
            if code:
                return "find_ownership_chain", {"code": code}
            elif self.last_context["deed_code"]:
                return "find_ownership_chain", {"code": self.last_context["deed_code"]}
        
        # =====================================================================
        # STEP 12: Try to find any deed code in query
        # =====================================================================
        code = self.extract_deed_code(query)
        if code:
            return "find_deed_details", {"code": code}
        
        # =====================================================================
        # STEP 13: Try to find any person name
        # =====================================================================
        name = self.extract_person_name(query)
        if name:
            return "find_person_deeds", {"name": name}
        
        # =====================================================================
        # DEFAULT: General search
        # =====================================================================
        # Use the most meaningful words from query
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'what', 'where', 'when', 
                     'how', 'why', 'who', 'which', 'me', 'tell', 'show', 'find', 'about',
                     'can', 'you', 'please', 'i', 'want', 'need', 'to', 'know', 'of', 'in'}
        words = [w for w in query.split() if w.lower() not in stop_words]
        search_query = " ".join(words) if words else query
        
        return "general_search", {"query": search_query}

    # =========================================================================
    # GRAPH QUERY EXECUTION
    # =========================================================================
    
    def query_graph(self, intent: str, params: dict) -> list:
        """Execute Cypher query and return results."""
        cypher = self.get_cypher_for_intent(intent, params)
        
        # Map params to query parameters
        query_params = {}
        param_mappings = ["name", "district", "code", "lot", "query", "deed_type"]
        for param in param_mappings:
            if param in params:
                query_params[param] = params[param]
        
        try:
            with self.driver.session() as session:
                result = session.run(cypher, query_params)
                records = [dict(record) for record in result]
                return records
        except Exception as e:
            print(f"Graph query error: {e}")
            return []

    # =========================================================================
    # LLM RESPONSE GENERATION
    # =========================================================================
    
    def generate_response(self, user_query: str, graph_data: list, intent: str) -> str:
        """Use GPT-4o to generate natural language response from graph data."""
        
        # Format graph data for context
        if not graph_data:
            context = "No relevant data found in the knowledge graph."
        else:
            context = f"Graph Query Results ({intent}):\n"
            context += "-" * 40 + "\n"
            for i, record in enumerate(graph_data, 1):
                context += f"\nResult {i}:\n"
                for key, value in record.items():
                    if value is not None and value != "" and value != []:
                        # Format parties nicely
                        if key == "parties" and isinstance(value, list):
                            context += f"  {key}:\n"
                            for party in value:
                                if isinstance(party, dict):
                                    context += f"    - {party.get('name', 'Unknown')}: {party.get('role', 'Unknown role')}\n"
                        else:
                            context += f"  {key}: {value}\n"
        
        # Add conversation history for context
        history_context = ""
        if self.conversation_history:
            history_context = "\n\nRecent conversation:\n"
            for h in self.conversation_history[-3:]:  # Last 3 exchanges
                history_context += f"- User asked about: {h['query'][:50]}...\n"
        
        # Create prompt
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"""User Question: {user_query}
{history_context}
Retrieved Knowledge Graph Data:
{context}

Please provide a helpful answer based on the graph data above. 
- If showing boundaries, clearly list North, South, East, West
- If showing parties, clearly indicate their roles
- If data is insufficient, acknowledge that and suggest what information might help
- Be specific and reference actual data values"""}
        ]
        
        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.3,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating response: {e}"

    # =========================================================================
    # MAIN QUERY METHOD
    # =========================================================================
    
    def query(self, user_query: str) -> str:
        """Main method: Process user query through GraphRAG pipeline."""
        
        print(f"\n{'='*60}")
        print(f"Query: {user_query}")
        print(f"{'='*60}")
        
        # Step 1: Resolve references using context
        resolved_query = self.resolve_references(user_query)
        if resolved_query != user_query:
            print(f"Resolved: {resolved_query}")
        
        # Step 2: Detect intent
        intent, params = self.detect_intent(resolved_query)
        print(f"Intent: {intent}")
        print(f"Params: {params}")
        print(f"Context: deed={self.last_context['deed_code']}, lot={self.last_context['lot']}")
        
        # Step 3: Query knowledge graph
        graph_data = self.query_graph(intent, params)
        print(f"Results: {len(graph_data)} records found")
        
        # Step 4: Update context for future queries
        self.update_context(intent, params, graph_data)
        
        # Step 5: Generate response with LLM
        response = self.generate_response(user_query, graph_data, intent)
        
        # Step 6: Store in conversation history
        self.conversation_history.append({
            "query": user_query,
            "intent": intent,
            "params": params,
            "results_count": len(graph_data)
        })
        
        # Keep only last 10 exchanges
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
        
        return response


# =============================================================================
# INTERACTIVE CLI
# =============================================================================

def main():
    """Interactive CLI for querying the legal knowledge graph."""
    
    print("\n" + "=" * 60)
    print("  LegalVision GraphRAG - Sri Lankan Property Law Assistant")
    print("  Enhanced with Conversation Context & Better Understanding")
    print("=" * 60)
    
    # Check credentials
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not set!")
        return
    if not NEO4J_PASS:
        print("❌ NEO4J_PASS not set!")
        return
    
    print("\nConnecting to Neo4j and OpenAI...")
    
    try:
        rag = LegalGraphRAG()
        print("✓ Connected successfully!\n")
        
        print("Example queries you can try:")
        print("  - How many deeds are in the system?")
        print("  - Find deeds in Colombo district")
        print("  - Show details of deed A 1100/188")
        print("  - What are the boundaries of this property?  (follow-up)")
        print("  - Who are the parties involved?  (follow-up)")
        print("  - Find property adjacent to FATIMA ISMAIL")
        print("  - Show all gift deeds")
        print("  - What is the ownership history?")
        print("\nSpecial commands:")
        print("  - 'clear' - Clear conversation context")
        print("  - 'context' - Show current context")
        print("  - 'quit/exit' - Exit the program")
        print("-" * 60)
        
        while True:
            try:
                user_input = input("\n📝 Your question: ").strip()
                
                if not user_input:
                    continue
                
                # Special commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\nGoodbye! 👋")
                    break
                
                if user_input.lower() == 'clear':
                    rag.clear_context()
                    continue
                
                if user_input.lower() == 'context':
                    print(f"\nCurrent context:")
                    for key, value in rag.last_context.items():
                        if value and key != 'last_results':
                            print(f"  {key}: {value}")
                    continue
                
                response = rag.query(user_input)
                print(f"\n🤖 Answer:\n{response}")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye! 👋")
                break
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'rag' in locals():
            rag.close()


if __name__ == "__main__":
    main()