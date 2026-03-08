#!/usr/bin/env python3
"""
Load Extra Legal Data to Neo4j with Proper Connections

This script loads:
- Statutes with full sections
- Legal definitions with source links
- Legal principles
- Deed requirements linked to governing statutes
- Land prices by district/area
- Land registry offices
- Creates all necessary relationships

Usage:
    python load_extra_laws_to_neo4j.py

Requires:
    - Neo4j running on bolt://localhost:7687
    - Data files in ./data/extra_laws/ (run download_legal_data.py first)
"""

import json
import os
from pathlib import Path
from neo4j import GraphDatabase
from typing import Dict, List, Any
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file
# =============================================================================
# CONFIGURATION
# =============================================================================

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASS = os.getenv("NEO4J_PASS")

DATA_DIR = Path("./extra_laws")

# =============================================================================
# NEO4J DRIVER
# =============================================================================

class Neo4jLoader:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.stats = {
            "statutes": 0,
            "sections": 0,
            "definitions": 0,
            "principles": 0,
            "requirements": 0,
            "provinces": 0,
            "districts": 0,
            "areas": 0,
            "registries": 0,
            "relationships": 0
        }
    
    def close(self):
        self.driver.close()
    
    def run_query(self, query: str, params: Dict = None):
        """Execute a Cypher query."""
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return list(result)
    
    # =========================================================================
    # SCHEMA CREATION
    # =========================================================================
    
    def create_indexes(self):
        """Create indexes for better performance."""
        print("\n📊 Creating indexes...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS FOR (s:Statute) ON (s.id)",
            "CREATE INDEX IF NOT EXISTS FOR (s:Statute) ON (s.short_name)",
            "CREATE INDEX IF NOT EXISTS FOR (s:Statute) ON (s.name)",
            "CREATE INDEX IF NOT EXISTS FOR (sec:Section) ON (sec.id)",
            "CREATE INDEX IF NOT EXISTS FOR (sec:Section) ON (sec.section_number)",
            "CREATE INDEX IF NOT EXISTS FOR (d:LegalDefinition) ON (d.term)",
            "CREATE INDEX IF NOT EXISTS FOR (p:LegalPrinciple) ON (p.name)",
            "CREATE INDEX IF NOT EXISTS FOR (r:DeedRequirement) ON (r.deed_type)",
            "CREATE INDEX IF NOT EXISTS FOR (prov:Province) ON (prov.name)",
            "CREATE INDEX IF NOT EXISTS FOR (dist:District) ON (dist.name)",
            "CREATE INDEX IF NOT EXISTS FOR (area:Area) ON (area.name)",
            "CREATE INDEX IF NOT EXISTS FOR (reg:RegistryOffice) ON (reg.name)",
            "CREATE INDEX IF NOT EXISTS FOR (lp:LandPrice) ON (lp.area_name)",
        ]
        
        for idx in indexes:
            try:
                self.run_query(idx)
            except Exception as e:
                pass  # Index may already exist
        
        print("  ✅ Indexes created")
    
    # =========================================================================
    # LOAD STATUTES
    # =========================================================================
    
    def load_statutes(self):
        """Load statutes from JSON files."""
        print("\n📜 Loading statutes...")
        
        statutes_file = DATA_DIR / 'statutes' / '_all_statutes.json'
        
        if not statutes_file.exists():
            print("  ❌ Statutes file not found. Run download_legal_data.py first.")
            return
        
        with open(statutes_file, 'r') as f:
            statutes = json.load(f)
        
        for statute in statutes:
            query = """
            MERGE (s:Statute {id: $id})
            SET s.name = $name,
                s.short_name = $short_name,
                s.act_number = $act_number,
                s.year = $year,
                s.category = $category,
                s.description = $description,
                s.key_provisions = $key_provisions,
                s.applies_to = $applies_to,
                s.url = $url,
                s.updated_at = datetime()
            RETURN s
            """
            
            self.run_query(query, {
                "id": statute.get("id"),
                "name": statute.get("name"),
                "short_name": statute.get("short_name"),
                "act_number": statute.get("act_number"),
                "year": statute.get("year"),
                "category": statute.get("category"),
                "description": statute.get("description"),
                "key_provisions": statute.get("key_provisions", []),
                "applies_to": statute.get("applies_to", []),
                "url": statute.get("url")
            })
            
            self.stats["statutes"] += 1
            print(f"  ✅ {statute.get('short_name')}: {statute.get('name')}")
        
        return self.stats["statutes"]
    
    # =========================================================================
    # LOAD SECTIONS
    # =========================================================================
    
    def load_sections(self):
        """Load statute sections and link to statutes."""
        print("\n📖 Loading statute sections...")
        
        sections_file = DATA_DIR / 'sections' / '_all_sections.json'
        
        if not sections_file.exists():
            print("  ❌ Sections file not found.")
            return
        
        with open(sections_file, 'r') as f:
            sections = json.load(f)
        
        for section in sections:
            # Create section node
            query = """
            MERGE (sec:Section {id: $id})
            SET sec.section_number = $section_number,
                sec.title = $title,
                sec.content = $content,
                sec.importance = $importance,
                sec.updated_at = datetime()
            RETURN sec
            """
            
            self.run_query(query, {
                "id": section.get("id"),
                "section_number": section.get("section_number"),
                "title": section.get("title"),
                "content": section.get("content"),
                "importance": section.get("importance")
            })
            
            # Link to statute
            link_query = """
            MATCH (sec:Section {id: $section_id})
            MATCH (s:Statute {id: $statute_id})
            MERGE (sec)-[r:PART_OF]->(s)
            SET r.created_at = datetime()
            RETURN r
            """
            
            self.run_query(link_query, {
                "section_id": section.get("id"),
                "statute_id": section.get("statute_id")
            })
            
            self.stats["sections"] += 1
            self.stats["relationships"] += 1
            print(f"  ✅ {section.get('section_number')}: {section.get('title')[:40]}...")
        
        return self.stats["sections"]
    
    # =========================================================================
    # LOAD DEFINITIONS
    # =========================================================================
    
    def load_definitions(self):
        """Load legal definitions and link to sources."""
        print("\n📚 Loading legal definitions...")
        
        defs_file = DATA_DIR / 'definitions' / 'legal_definitions.json'
        
        if not defs_file.exists():
            print("  ❌ Definitions file not found.")
            return
        
        with open(defs_file, 'r') as f:
            definitions = json.load(f)
        
        for defn in definitions:
            # Create definition node
            query = """
            MERGE (d:LegalDefinition {term: $term})
            SET d.definition = $definition,
                d.source = $source,
                d.updated_at = datetime()
            RETURN d
            """
            
            self.run_query(query, {
                "term": defn.get("term"),
                "definition": defn.get("definition"),
                "source": defn.get("source")
            })
            
            # Try to link to source statute
            source = defn.get("source", "")
            if "Ordinance" in source or "Act" in source:
                link_query = """
                MATCH (d:LegalDefinition {term: $term})
                MATCH (s:Statute)
                WHERE s.name CONTAINS $source_hint OR s.short_name = $source_hint
                MERGE (d)-[r:DEFINED_IN]->(s)
                SET r.created_at = datetime()
                RETURN r
                """
                
                # Extract key part of source name
                source_hint = source.replace("Ordinance", "").replace("Act", "").strip()
                
                result = self.run_query(link_query, {
                    "term": defn.get("term"),
                    "source_hint": source
                })
                
                if result:
                    self.stats["relationships"] += 1
            
            self.stats["definitions"] += 1
            print(f"  ✅ {defn.get('term')}")
        
        return self.stats["definitions"]
    
    # =========================================================================
    # LOAD PRINCIPLES
    # =========================================================================
    
    def load_principles(self):
        """Load legal principles."""
        print("\n⚖️ Loading legal principles...")
        
        principles_file = DATA_DIR / 'principles' / 'legal_principles.json'
        
        if not principles_file.exists():
            print("  ❌ Principles file not found.")
            return
        
        with open(principles_file, 'r') as f:
            principles = json.load(f)
        
        for principle in principles:
            query = """
            MERGE (p:LegalPrinciple {name: $name})
            SET p.english = $english,
                p.description = $description,
                p.application = $application,
                p.updated_at = datetime()
            RETURN p
            """
            
            self.run_query(query, {
                "name": principle.get("name"),
                "english": principle.get("english"),
                "description": principle.get("description"),
                "application": principle.get("application")
            })
            
            self.stats["principles"] += 1
            print(f"  ✅ {principle.get('name')}: {principle.get('english')}")
        
        return self.stats["principles"]
    
    # =========================================================================
    # LOAD DEED REQUIREMENTS
    # =========================================================================
    
    def load_requirements(self):
        """Load deed requirements and link to governing statutes."""
        print("\n📋 Loading deed requirements...")
        
        reqs_file = DATA_DIR / 'requirements' / 'deed_requirements.json'
        
        if not reqs_file.exists():
            print("  ❌ Requirements file not found.")
            return
        
        with open(reqs_file, 'r') as f:
            requirements = json.load(f)
        
        for req in requirements:
            # Create requirement node
            query = """
            MERGE (r:DeedRequirement {deed_type: $deed_type})
            SET r.name = $name,
                r.requirements = $requirements,
                r.stamp_duty = $stamp_duty,
                r.registration_fee = $registration_fee,
                r.time_limit = $time_limit,
                r.updated_at = datetime()
            RETURN r
            """
            
            self.run_query(query, {
                "deed_type": req.get("deed_type"),
                "name": req.get("name"),
                "requirements": req.get("requirements", []),
                "stamp_duty": req.get("stamp_duty"),
                "registration_fee": req.get("registration_fee"),
                "time_limit": req.get("time_limit")
            })
            
            # Link to governing statutes
            for statute_name in req.get("governing_statutes", []):
                link_query = """
                MATCH (r:DeedRequirement {deed_type: $deed_type})
                MATCH (s:Statute)
                WHERE s.name = $statute_name OR s.name CONTAINS $statute_name
                MERGE (r)-[rel:GOVERNED_BY]->(s)
                SET rel.created_at = datetime()
                RETURN rel
                """
                
                result = self.run_query(link_query, {
                    "deed_type": req.get("deed_type"),
                    "statute_name": statute_name
                })
                
                if result:
                    self.stats["relationships"] += 1
            
            self.stats["requirements"] += 1
            print(f"  ✅ {req.get('deed_type')}: {req.get('name')}")
        
        return self.stats["requirements"]
    
    # =========================================================================
    # LOAD LAND PRICES
    # =========================================================================
    
    def load_land_prices(self):
        """Load land prices by province/district/area."""
        print("\n💰 Loading land prices...")
        
        prices_file = DATA_DIR / 'prices' / 'land_prices_by_district.json'
        
        if not prices_file.exists():
            print("  ❌ Prices file not found.")
            return
        
        with open(prices_file, 'r') as f:
            prices = json.load(f)
        
        for province_name, districts in prices.items():
            # Create province node
            prov_query = """
            MERGE (p:Province {name: $name})
            SET p.updated_at = datetime()
            RETURN p
            """
            self.run_query(prov_query, {"name": province_name})
            self.stats["provinces"] += 1
            
            for district_name, district_data in districts.items():
                # Create district node
                dist_query = """
                MERGE (d:District {name: $name})
                SET d.province = $province,
                    d.updated_at = datetime()
                RETURN d
                """
                self.run_query(dist_query, {
                    "name": district_name,
                    "province": province_name
                })
                
                # Link district to province
                link_query = """
                MATCH (d:District {name: $district})
                MATCH (p:Province {name: $province})
                MERGE (d)-[r:IN_PROVINCE]->(p)
                RETURN r
                """
                self.run_query(link_query, {
                    "district": district_name,
                    "province": province_name
                })
                self.stats["relationships"] += 1
                self.stats["districts"] += 1
                
                # Load area prices
                areas = district_data.get("areas", {})
                for area_name, area_data in areas.items():
                    # Create area with price data
                    area_query = """
                    MERGE (a:Area {name: $name, district: $district})
                    SET a.avg_price_per_perch = $avg_price,
                        a.price_trend = $trend,
                        a.updated_at = datetime()
                    RETURN a
                    """
                    self.run_query(area_query, {
                        "name": area_name,
                        "district": district_name,
                        "avg_price": area_data.get("avg"),
                        "trend": area_data.get("trend")
                    })
                    
                    # Link area to district
                    area_link = """
                    MATCH (a:Area {name: $area, district: $district})
                    MATCH (d:District {name: $district})
                    MERGE (a)-[r:IN_DISTRICT]->(d)
                    RETURN r
                    """
                    self.run_query(area_link, {
                        "area": area_name,
                        "district": district_name
                    })
                    self.stats["relationships"] += 1
                    self.stats["areas"] += 1
                
                # Create zone price nodes
                for zone_type in ["city_center", "suburbs", "outer_areas", "coastal", "inland"]:
                    if zone_type in district_data:
                        zone_data = district_data[zone_type]
                        zone_query = """
                        MERGE (lp:LandPrice {district: $district, zone: $zone})
                        SET lp.min_price = $min_price,
                            lp.max_price = $max_price,
                            lp.avg_price = $avg_price,
                            lp.unit = $unit,
                            lp.updated_at = datetime()
                        RETURN lp
                        """
                        self.run_query(zone_query, {
                            "district": district_name,
                            "zone": zone_type,
                            "min_price": zone_data.get("min"),
                            "max_price": zone_data.get("max"),
                            "avg_price": zone_data.get("avg"),
                            "unit": zone_data.get("unit", "per_perch")
                        })
                        
                        # Link to district
                        zone_link = """
                        MATCH (lp:LandPrice {district: $district, zone: $zone})
                        MATCH (d:District {name: $district})
                        MERGE (lp)-[r:PRICE_IN]->(d)
                        RETURN r
                        """
                        self.run_query(zone_link, {
                            "district": district_name,
                            "zone": zone_type
                        })
                        self.stats["relationships"] += 1
            
            print(f"  ✅ {province_name}: {len(districts)} districts")
        
        return self.stats["areas"]
    
    # =========================================================================
    # LOAD REGISTRIES
    # =========================================================================
    
    def load_registries(self):
        """Load land registry office data."""
        print("\n🏛️ Loading land registry offices...")
        
        reg_file = DATA_DIR / 'registries' / 'land_registries.json'
        
        if not reg_file.exists():
            print("  ❌ Registries file not found.")
            return
        
        with open(reg_file, 'r') as f:
            registries = json.load(f)
        
        for registry in registries:
            # Create registry node
            query = """
            MERGE (r:RegistryOffice {name: $name})
            SET r.district = $district,
                r.address = $address,
                r.phone = $phone,
                r.updated_at = datetime()
            RETURN r
            """
            
            self.run_query(query, {
                "name": registry.get("name"),
                "district": registry.get("district"),
                "address": registry.get("address"),
                "phone": registry.get("phone")
            })
            
            # Link to district
            link_query = """
            MATCH (r:RegistryOffice {name: $registry_name})
            MATCH (d:District {name: $district})
            MERGE (r)-[rel:SERVES]->(d)
            RETURN rel
            """
            
            result = self.run_query(link_query, {
                "registry_name": registry.get("name"),
                "district": registry.get("district")
            })
            
            if result:
                self.stats["relationships"] += 1
            
            self.stats["registries"] += 1
            print(f"  ✅ {registry.get('name')}")
        
        return self.stats["registries"]
    
    # =========================================================================
    # CREATE CROSS-REFERENCES
    # =========================================================================
    
    def create_cross_references(self):
        """Create additional relationships between entities."""
        print("\n🔗 Creating cross-references...")
        
        # Link instruments to governing statutes based on type
        instrument_statute_query = """
        MATCH (i:Instrument)
        MATCH (s:Statute)
        WHERE i.type IN s.applies_to
        MERGE (i)-[r:GOVERNED_BY]->(s)
        RETURN count(r) as count
        """
        result = self.run_query(instrument_statute_query)
        if result:
            count = result[0]["count"]
            self.stats["relationships"] += count
            print(f"  ✅ Linked {count} instruments to governing statutes")
        
        # Link instruments to deed requirements
        instrument_req_query = """
        MATCH (i:Instrument)
        MATCH (req:DeedRequirement)
        WHERE i.type = req.deed_type
        MERGE (i)-[r:MUST_COMPLY_WITH]->(req)
        RETURN count(r) as count
        """
        result = self.run_query(instrument_req_query)
        if result:
            count = result[0]["count"]
            self.stats["relationships"] += count
            print(f"  ✅ Linked {count} instruments to requirements")
        
        # Link instruments to districts
        instrument_district_query = """
        MATCH (i:Instrument)-[:IN_DISTRICT]->(d:District)
        MATCH (p:Province)
        WHERE d.province = p.name
        MERGE (i)-[r:IN_PROVINCE]->(p)
        RETURN count(r) as count
        """
        result = self.run_query(instrument_district_query)
        if result:
            count = result[0]["count"]
            self.stats["relationships"] += count
            print(f"  ✅ Linked {count} instruments to provinces")
        
        # Link districts to registry offices
        dist_registry_query = """
        MATCH (d:District)
        MATCH (r:RegistryOffice)
        WHERE r.district = d.name
        MERGE (d)-[rel:HAS_REGISTRY]->(r)
        RETURN count(rel) as count
        """
        result = self.run_query(dist_registry_query)
        if result:
            count = result[0]["count"]
            self.stats["relationships"] += count
            print(f"  ✅ Linked {count} districts to registries")
        
        # Link areas to land prices
        area_price_query = """
        MATCH (a:Area)
        MATCH (lp:LandPrice)
        WHERE a.district = lp.district
        MERGE (a)-[r:HAS_ZONE_PRICE]->(lp)
        RETURN count(r) as count
        """
        result = self.run_query(area_price_query)
        if result:
            count = result[0]["count"]
            self.stats["relationships"] += count
            print(f"  ✅ Linked {count} areas to zone prices")
        
        # Link critical sections to principles
        section_principle_query = """
        MATCH (sec:Section)
        WHERE sec.importance = 'critical'
        MATCH (p:LegalPrinciple)
        WHERE sec.content CONTAINS p.english OR sec.content CONTAINS p.name
        MERGE (sec)-[r:EMBODIES]->(p)
        RETURN count(r) as count
        """
        result = self.run_query(section_principle_query)
        if result:
            count = result[0]["count"]
            self.stats["relationships"] += count
            print(f"  ✅ Linked {count} sections to principles")


def main():
    """Main function to load all data."""
    print("=" * 60)
    print("🏛️ Loading Sri Lankan Legal Data to Neo4j")
    print("=" * 60)
    
    # Check if data exists
    if not DATA_DIR.exists():
        print(f"❌ Data directory not found: {DATA_DIR}")
        print("Run download_legal_data.py first to download the data.")
        return
    
    # Initialize loader
    print(f"\n📡 Connecting to Neo4j at {NEO4J_URI}...")
    
    try:
        loader = Neo4jLoader(NEO4J_URI, NEO4J_USER, NEO4J_PASS)
        
        # Test connection
        loader.run_query("RETURN 1 as test")
        print("  ✅ Connected to Neo4j")
        
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        print("\nMake sure Neo4j is running and credentials are correct.")
        print("Set environment variables: NEO4J_URI, NEO4J_USER, NEO4J_PASS")
        return
    
    try:
        # Create indexes
        loader.create_indexes()
        
        # Load all data
        loader.load_statutes()
        loader.load_sections()
        loader.load_definitions()
        loader.load_principles()
        loader.load_requirements()
        loader.load_land_prices()
        loader.load_registries()
        
        # Create cross-references
        loader.create_cross_references()
        
        # Print summary
        print("\n" + "=" * 60)
        print("✅ DATA LOADING COMPLETE")
        print("=" * 60)
        print(f"""
Summary:
  📜 Statutes:       {loader.stats['statutes']}
  📖 Sections:       {loader.stats['sections']}
  📚 Definitions:    {loader.stats['definitions']}
  ⚖️ Principles:     {loader.stats['principles']}
  📋 Requirements:   {loader.stats['requirements']}
  🗺️ Provinces:      {loader.stats['provinces']}
  🏘️ Districts:      {loader.stats['districts']}
  📍 Areas:          {loader.stats['areas']}
  🏛️ Registries:     {loader.stats['registries']}
  🔗 Relationships:  {loader.stats['relationships']}

Your knowledge graph is now enhanced with:
  - Full Sri Lankan property law statutes
  - Detailed statute sections
  - Legal definitions and terminology
  - Legal principles (Nemo Dat, Caveat Emptor, etc.)
  - Deed requirements by type
  - Land prices by district and area
  - Land registry office information

Query examples:
  # Find stamp duty for sale deeds
  MATCH (r:DeedRequirement {{deed_type: 'sale_transfer'}}) RETURN r.stamp_duty

  # Get land prices in Colombo
  MATCH (a:Area)-[:IN_DISTRICT]->(d:District {{name: 'Colombo'}})
  RETURN a.name, a.avg_price_per_perch, a.price_trend
  ORDER BY a.avg_price_per_perch DESC

  # Find governing law for a deed
  MATCH (i:Instrument {{code_number: 'A 1100/188'}})-[:GOVERNED_BY]->(s:Statute)
  RETURN s.name, s.key_provisions
""")
        
    except Exception as e:
        print(f"\n❌ Error during loading: {e}")
        raise
    
    finally:
        loader.close()


if __name__ == "__main__":
    main()
