"""
LegalVision GraphRAG - Simple Graph-based RAG for Legal Deed Queries
Uses Neo4j Knowledge Graph + OpenAI GPT-4o via LangChain
"""

import os
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
    """Simple GraphRAG for querying Sri Lankan legal deed knowledge graph."""

    def __init__(self):
        # Initialize Neo4j
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        
        # Initialize OpenAI
        self.openai = OpenAI(api_key=OPENAI_API_KEY)
        
        # System prompt for the LLM
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
5. Always be helpful and professional"""

    def close(self):
        self.driver.close()

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
                       pp.extent AS extent, d.name AS district
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
            
            # Find deed by code/number
            "find_deed_details": """
                MATCH (i:Instrument)
                WHERE i.code_number CONTAINS $code OR i.id CONTAINS $code
                OPTIONAL MATCH (p:Person)-[r:HAS_ROLE]->(i)
                OPTIONAL MATCH (i)-[:CONVEYS]->(pp:PropertyParcel)
                OPTIONAL MATCH (pp)-[:DEFINED_BY]->(pl:Plan)
                OPTIONAL MATCH (i)-[:IN_DISTRICT]->(d:District)
                OPTIONAL MATCH (i)-[:IN_PROVINCE]->(pv:Province)
                OPTIONAL MATCH (i)-[:REGISTERED_AT]->(ro:RegistryOffice)
                RETURN i.code_number AS deed_code, i.type AS deed_type, i.date AS date,
                       i.consideration_lkr AS amount, d.name AS district, pv.name AS province,
                       ro.name AS registry, pl.plan_no AS plan_no,
                       pp.lot AS lot, pp.extent AS extent, pp.assessment_no AS assessment,
                       pp.boundary_north AS north, pp.boundary_south AS south,
                       pp.boundary_east AS east, pp.boundary_west AS west,
                       collect(DISTINCT {name: p.name, role: r.role}) AS parties
                LIMIT 1
            """,
            
            # Find property by lot/plan
            "find_property": """
                MATCH (pp:PropertyParcel)
                WHERE pp.lot CONTAINS $lot OR pp.plan_no CONTAINS $lot
                OPTIONAL MATCH (i:Instrument)-[:CONVEYS]->(pp)
                OPTIONAL MATCH (pp)-[:DEFINED_BY]->(pl:Plan)
                OPTIONAL MATCH (p:Person)-[r:HAS_ROLE]->(i)
                RETURN pp.lot AS lot, pp.extent AS extent, pp.assessment_no AS assessment,
                       pl.plan_no AS plan_no, pl.plan_date AS plan_date,
                       i.code_number AS deed_code, i.type AS deed_type, i.date AS date,
                       collect(DISTINCT {name: p.name, role: r.role}) AS parties
                LIMIT 5
            """,
            
            # Get statistics
            "get_stats": """
                MATCH (i:Instrument)
                WITH count(i) AS total_deeds
                MATCH (p:Person)
                WITH total_deeds, count(p) AS total_persons
                MATCH (pp:PropertyParcel)
                WITH total_deeds, total_persons, count(pp) AS total_parcels
                OPTIONAL MATCH (i2:Instrument)
                WITH total_deeds, total_persons, total_parcels,
                     count(CASE WHEN i2.type = 'sale_transfer' THEN 1 END) AS sales,
                     count(CASE WHEN i2.type = 'gift' THEN 1 END) AS gifts,
                     count(CASE WHEN i2.type = 'will' THEN 1 END) AS wills
                RETURN total_deeds, total_persons, total_parcels, sales, gifts, wills
            """,
            
            # Find ownership chain (prior deeds)
            "find_ownership_chain": """
                MATCH (i:Instrument)
                WHERE i.code_number CONTAINS $code OR i.id CONTAINS $code
                OPTIONAL MATCH (i)-[:REFERS_TO_PRIOR]->(pd:PriorDeed)
                OPTIONAL MATCH (i)-[:DERIVES_FROM]->(prior:Instrument)
                OPTIONAL MATCH (p:Person)-[r:HAS_ROLE]->(i)
                RETURN i.code_number AS current_deed, i.date AS date,
                       pd.reference AS prior_reference,
                       prior.code_number AS prior_deed_code,
                       collect(DISTINCT {name: p.name, role: r.role}) AS parties
            """,
            
            # General search
            "general_search": """
                CALL {
                    MATCH (p:Person)
                    WHERE toLower(p.name) CONTAINS toLower($query)
                    RETURN 'Person' AS type, p.name AS name, null AS code
                    UNION
                    MATCH (i:Instrument)
                    WHERE i.code_number CONTAINS $query OR i.id CONTAINS $query
                    RETURN 'Instrument' AS type, i.type AS name, i.code_number AS code
                    UNION
                    MATCH (d:District)
                    WHERE toLower(d.name) CONTAINS toLower($query)
                    RETURN 'District' AS type, d.name AS name, null AS code
                    UNION
                    MATCH (pp:PropertyParcel)
                    WHERE pp.lot CONTAINS $query OR pp.assessment_no CONTAINS $query
                    RETURN 'Property' AS type, pp.lot AS name, pp.assessment_no AS code
                }
                RETURN type, name, code
                LIMIT 10
            """
        }
        
        return queries.get(intent, queries["general_search"])

    # =========================================================================
    # INTENT DETECTION (Simple keyword-based)
    # =========================================================================
    
    def detect_intent(self, query: str) -> tuple:
        """Simple intent detection from user query."""
        query_lower = query.lower()
        
        # Statistics
        if any(word in query_lower for word in ['how many', 'count', 'total', 'statistics', 'stats']):
            return "get_stats", {}
        
        # Person search
        if any(word in query_lower for word in ['who', 'person', 'owner', 'party', 'vendor', 'vendee', 'donor', 'donee']):
            # Try to extract name (simple approach - words after key terms)
            for term in ['named', 'name', 'called', 'person']:
                if term in query_lower:
                    idx = query_lower.find(term)
                    name_part = query[idx:].split()[1:3]  # Get next 1-2 words
                    if name_part:
                        return "find_person_deeds", {"name": " ".join(name_part)}
            return "find_person_deeds", {"name": query.split()[-1]}
        
        # District search
        if any(word in query_lower for word in ['district', 'colombo', 'gampaha', 'kandy', 'galle', 'matara', 'kalutara']):
            for district in ['colombo', 'gampaha', 'kandy', 'galle', 'matara', 'kalutara', 'kurunegala', 'ratnapura']:
                if district in query_lower:
                    return "find_district_deeds", {"district": district}
            return "find_district_deeds", {"district": query.split()[-1]}
        
        # Deed code search
        if any(word in query_lower for word in ['deed', 'instrument', 'code', 'number', 'details']):
            # Look for patterns like "A 123/2024" or just numbers
            import re
            code_match = re.search(r'[A-Z]?\s*\d+[/\-]?\d*', query, re.IGNORECASE)
            if code_match:
                return "find_deed_details", {"code": code_match.group().strip()}
            return "find_deed_details", {"code": query.split()[-1]}
        
        # Property/lot search
        if any(word in query_lower for word in ['lot', 'property', 'parcel', 'plan', 'land']):
            import re
            lot_match = re.search(r'lot\s*(\w+)', query_lower)
            if lot_match:
                return "find_property", {"lot": lot_match.group(1)}
            return "find_property", {"lot": query.split()[-1]}
        
        # Ownership chain
        if any(word in query_lower for word in ['chain', 'history', 'previous', 'prior', 'ownership']):
            import re
            code_match = re.search(r'[A-Z]?\s*\d+[/\-]?\d*', query, re.IGNORECASE)
            if code_match:
                return "find_ownership_chain", {"code": code_match.group().strip()}
        
        # Default: general search
        return "general_search", {"query": query}

    # =========================================================================
    # GRAPH QUERY EXECUTION
    # =========================================================================
    
    def query_graph(self, intent: str, params: dict) -> list:
        """Execute Cypher query and return results."""
        cypher = self.get_cypher_for_intent(intent, params)
        
        # Map params to query parameters
        query_params = {}
        if "name" in params:
            query_params["name"] = params["name"]
        if "district" in params:
            query_params["district"] = params["district"]
        if "code" in params:
            query_params["code"] = params["code"]
        if "lot" in params:
            query_params["lot"] = params["lot"]
        if "query" in params:
            query_params["query"] = params["query"]
        
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
                    if value is not None:
                        context += f"  {key}: {value}\n"
        
        # Create prompt
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"""User Question: {user_query}

Retrieved Knowledge Graph Data:
{context}

Please provide a helpful answer based on the graph data above. If the data is empty or insufficient, 
acknowledge that and suggest what information might help."""}
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
        
        # Step 1: Detect intent
        intent, params = self.detect_intent(user_query)
        print(f"Intent: {intent}")
        print(f"Params: {params}")
        
        # Step 2: Query knowledge graph
        graph_data = self.query_graph(intent, params)
        print(f"Results: {len(graph_data)} records found")
        
        # Step 3: Generate response with LLM
        response = self.generate_response(user_query, graph_data, intent)
        
        return response


# =============================================================================
# INTERACTIVE CLI
# =============================================================================

def main():
    """Interactive CLI for querying the legal knowledge graph."""
    
    print("\n" + "=" * 60)
    print("  LegalVision GraphRAG - Sri Lankan Property Law Assistant")
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
        print("  - Who is the owner of lot 1A?")
        print("  - Show details of deed A 123/2024")
        print("  - Find all deeds involving person John")
        print("\nType 'quit' or 'exit' to stop.\n")
        
        while True:
            try:
                user_input = input("\n📝 Your question: ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\nGoodbye! 👋")
                    break
                
                response = rag.query(user_input)
                print(f"\n🤖 Answer:\n{response}")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye! 👋")
                break
                
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'rag' in locals():
            rag.close()


if __name__ == "__main__":
    main()