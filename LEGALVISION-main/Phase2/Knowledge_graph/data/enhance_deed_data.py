"""
Enhance and fix processed deed JSON files.
- Fills missing fields with realistic Sri Lankan data
- Creates fake connectivity between properties via boundary references
- Generates proper deed codes, registry info, etc.

Usage:
    python enhance_deed_data.py [input_folder] [output_folder]
    
Examples:
    python enhance_deed_data.py ./deeds/processed ./deeds/enhanced
    python enhance_deed_data.py  # Uses defaults
"""

import json
import random
import string
from pathlib import Path
from typing import Dict, List, Optional
import sys


class DeedDataEnhancer:
    """Enhance deed JSON files with realistic Sri Lankan data."""
    
    def __init__(self):
        # Sri Lankan districts by province
        self.provinces_districts = {
            "Western": ["Colombo", "Gampaha", "Kalutara"],
            "Central": ["Kandy", "Matale", "Nuwara Eliya"],
            "Southern": ["Galle", "Matara", "Hambantota"],
            "Northern": ["Jaffna", "Kilinochchi", "Mannar", "Mullaitivu", "Vavuniya"],
            "Eastern": ["Batticaloa", "Ampara", "Trincomalee"],
            "North Western": ["Kurunegala", "Puttalam"],
            "North Central": ["Anuradhapura", "Polonnaruwa"],
            "Uva": ["Badulla", "Monaragala"],
            "Sabaragamuwa": ["Ratnapura", "Kegalle"]
        }
        
        # Flatten for easy access
        self.all_districts = []
        self.district_to_province = {}
        for province, districts in self.provinces_districts.items():
            for district in districts:
                self.all_districts.append(district)
                self.district_to_province[district] = province
        
        # Registry offices (usually same as district)
        self.registry_offices = self.all_districts.copy()
        
        # Common Sri Lankan names for boundaries
        self.sri_lankan_names = [
            "PERERA", "SILVA", "FERNANDO", "DE SILVA", "JAYAWARDENA",
            "WICKRAMASINGHE", "BANDARA", "RAJAPAKSA", "GUNASEKARA", "DISSANAYAKE",
            "RATHNAYAKE", "KARUNARATNE", "SENEVIRATNE", "SAMARAWEERA", "HERATH",
            "AMARASEKARA", "PATHIRANA", "NANAYAKKARA", "WEERASINGHE", "COORAY",
            "MENDIS", "FONSEKA", "GUNAWARDENA", "JAYASURIYA", "LIYANAGE",
            "RANASINGHE", "WIJESINGHE", "ABEYRATNE", "KUMARASINGHE", "RATNAYAKE",
            "MOHAMED", "ISMAIL", "FAROOK", "HANIFA", "RASHEED",
            "CHEN", "LEE", "WONG", "TAN", "SAMY", "PILLAI", "NAIR"
        ]
        
        # Common boundary descriptions
        self.boundary_templates = [
            "by land belonging to {name}",
            "by property of {name}",
            "by land claimed by {name}",
            "by {name}'s land",
            "by allotment of {name}",
        ]
        
        # Road/landmark names for boundaries
        self.roads_landmarks = [
            "Main Road", "Station Road", "Temple Road", "School Lane",
            "Hospital Road", "Market Street", "Church Road", "Mosque Lane",
            "Kandy Road", "Galle Road", "Colombo Road", "High Level Road",
            "Low Level Road", "Beach Road", "Hill Street", "Lake Road",
            "Railway Line", "Canal", "River", "Paddy Field", "Reservation",
            "Government Land", "Crown Land", "Public Road", "Cart Track",
            "Footpath", "Stream", "Ela (canal)", "Wewa (tank)"
        ]
        
        # Deed type prefixes for code generation
        self.deed_type_prefixes = {
            "sale_transfer": ["A", "B", "C", "D", "K", "M", "G"],
            "gift": ["G", "D", "A"],
            "will": ["W", "T", "L"],
            "lease": ["L", "R", "A"],
            "mortgage": ["M", "H", "B"],
            "unknown": ["X", "U", "A"]
        }
        
        # Track all deed codes for cross-referencing
        self.all_deed_codes = []
        self.deed_id_to_code = {}
        
        # Surveyor names
        self.surveyors = [
            "K.P. Jayawardena", "S.M. Fernando", "A.B. Perera", 
            "R.L. Silva", "M.N. Bandara", "P.Q. Rathnayake",
            "L.S. Gunasekara", "T.U. Wickramasinghe", "H.J. Dissanayake"
        ]
    
    def generate_deed_code(self, deed_type: str, district: str, year: str = None) -> str:
        """Generate a realistic Sri Lankan deed code."""
        prefix = random.choice(self.deed_type_prefixes.get(deed_type, ["A"]))
        
        # Get district initial
        district_initial = district[0].upper() if district else "C"
        
        # Generate numbers
        main_num = random.randint(100, 9999)
        sub_num = random.randint(1, 999)
        
        # Year suffix
        if not year:
            year = str(random.randint(2015, 2024))
        year_suffix = year[-2:] if len(year) >= 2 else "24"
        
        # Different formats
        formats = [
            f"{prefix} {main_num}/{sub_num}",
            f"{prefix}{main_num}/{year_suffix}",
            f"{district_initial} {main_num}/{sub_num}",
            f"{prefix} {main_num}-{year_suffix}",
        ]
        
        return random.choice(formats)
    
    def generate_plan_number(self) -> str:
        """Generate a realistic plan number."""
        return str(random.randint(100, 9999))
    
    def generate_lot_number(self) -> str:
        """Generate a realistic lot number."""
        formats = [
            str(random.randint(1, 50)),
            f"{random.randint(1, 20)}{random.choice(['A', 'B', 'C', 'D'])}",
            random.choice(['A', 'B', 'C', 'D', 'E']),
            f"Lot {random.randint(1, 30)}",
        ]
        return random.choice(formats)
    
    def generate_assessment_number(self) -> str:
        """Generate a realistic assessment number."""
        formats = [
            f"{random.randint(1, 999)}",
            f"{random.randint(1, 999)}/{random.randint(1, 9)}",
            f"{random.randint(1, 999)}-{random.choice(['A', 'B', 'C'])}",
            f"{random.randint(1, 99)}/{random.randint(1, 99)}/{random.choice(['A', 'B'])}",
        ]
        return random.choice(formats)
    
    def generate_extent(self) -> str:
        """Generate a realistic extent in perches/roods/acres."""
        perches = random.randint(5, 160)
        roods = perches // 40
        remaining_perches = perches % 40
        
        formats = [
            f"{perches} Perches",
            f"A:0 R:{roods} P:{remaining_perches}",
            f"{perches} decimal Perches",
            f"Zero Acres, {roods} Roods and {remaining_perches} Perches",
        ]
        return random.choice(formats)
    
    def generate_consideration(self, deed_type: str) -> float:
        """Generate a realistic consideration amount in LKR."""
        if deed_type == "gift":
            return None  # Gifts usually don't have consideration
        elif deed_type == "will":
            return None  # Wills don't have consideration
        elif deed_type == "lease":
            # Monthly/annual rent
            return float(random.choice([25000, 50000, 75000, 100000, 150000, 200000]))
        else:
            # Property values in LKR (realistic range)
            ranges = [
                (500000, 2000000),    # Small plots
                (2000000, 10000000),  # Medium properties
                (10000000, 50000000), # Large properties
                (50000000, 200000000) # Premium properties
            ]
            min_val, max_val = random.choice(ranges)
            return float(random.randint(min_val // 100000, max_val // 100000) * 100000)
    
    def generate_boundary(self, direction: str, other_deed_codes: List[str], 
                         used_codes: set) -> str:
        """Generate a realistic boundary description with deed references."""
        # 40% chance to reference another deed
        if other_deed_codes and random.random() < 0.4:
            available_codes = [c for c in other_deed_codes if c not in used_codes]
            if available_codes:
                code = random.choice(available_codes)
                used_codes.add(code)
                templates = [
                    f"by land transferred under Deed No. {code}",
                    f"by property conveyed in Deed {code}",
                    f"by allotment in Deed No. {code}",
                    f"by Lot in Deed {code}",
                ]
                return random.choice(templates)
        
        # 30% chance to use a road/landmark
        if random.random() < 0.3:
            landmark = random.choice(self.roads_landmarks)
            return f"by {landmark}"
        
        # Otherwise use a person name
        name = random.choice(self.sri_lankan_names)
        template = random.choice(self.boundary_templates)
        return template.format(name=name)
    
    def generate_boundaries(self, other_deed_codes: List[str]) -> Dict[str, str]:
        """Generate all four boundaries."""
        used_codes = set()
        return {
            "N": self.generate_boundary("N", other_deed_codes, used_codes),
            "E": self.generate_boundary("E", other_deed_codes, used_codes),
            "S": self.generate_boundary("S", other_deed_codes, used_codes),
            "W": self.generate_boundary("W", other_deed_codes, used_codes),
        }
    
    def generate_date(self, base_year: int = None) -> str:
        """Generate a realistic date."""
        if not base_year:
            base_year = random.randint(2010, 2024)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        
        formats = [
            f"{base_year}.{month:02d}.{day:02d}",
            f"{day:02d}/{month:02d}/{base_year}",
            f"{day:02d}.{month:02d}.{base_year}",
        ]
        return random.choice(formats)
    
    def generate_nic(self) -> str:
        """Generate a realistic Sri Lankan NIC number."""
        if random.random() < 0.7:
            # Old format: 9 digits + V/X
            return f"{random.randint(100000000, 999999999)}{random.choice(['V', 'X'])}"
        else:
            # New format: 12 digits
            return f"{random.randint(100000000000, 999999999999)}"
    
    def enhance_deed(self, deed: Dict, other_deed_codes: List[str]) -> Dict:
        """Enhance a single deed with missing data."""
        enhanced = deed.copy()
        
        # Determine district/province first (needed for other fields)
        if not enhanced.get("district") or enhanced["district"] == "null":
            enhanced["district"] = random.choice(self.all_districts)
        
        district = enhanced["district"]
        province = self.district_to_province.get(district, "Western")
        
        # Fill province
        if not enhanced.get("province") or enhanced["province"] == "null":
            enhanced["province"] = province
        
        # Fill jurisdiction (usually same as district)
        if not enhanced.get("jurisdiction") or enhanced["jurisdiction"] == "null":
            enhanced["jurisdiction"] = district
        
        # Fill registry office
        if not enhanced.get("registry_office") or enhanced["registry_office"] == "null":
            enhanced["registry_office"] = district
        
        # Extract year from date if available
        year = None
        if enhanced.get("date"):
            import re
            year_match = re.search(r'(20\d{2}|19\d{2})', str(enhanced["date"]))
            if year_match:
                year = year_match.group(1)
        
        # Fill deed code
        deed_type = enhanced.get("type", "unknown")
        if not enhanced.get("code_number") or enhanced["code_number"].startswith("UNKNOWN"):
            enhanced["code_number"] = self.generate_deed_code(deed_type, district, year)
        
        # Store for cross-referencing
        self.all_deed_codes.append(enhanced["code_number"])
        self.deed_id_to_code[enhanced["id"]] = enhanced["code_number"]
        
        # Fill date if missing
        if not enhanced.get("date"):
            enhanced["date"] = self.generate_date()
        
        # Fill plan info
        if "plan" not in enhanced:
            enhanced["plan"] = {}
        
        if not enhanced["plan"].get("plan_no"):
            enhanced["plan"]["plan_no"] = self.generate_plan_number()
        
        if not enhanced["plan"].get("plan_date"):
            enhanced["plan"]["plan_date"] = enhanced.get("date", self.generate_date())
        
        if not enhanced["plan"].get("surveyor"):
            enhanced["plan"]["surveyor"] = random.choice(self.surveyors)
        
        # Fill property info
        if "property" not in enhanced:
            enhanced["property"] = {}
        
        if not enhanced["property"].get("lot"):
            enhanced["property"]["lot"] = self.generate_lot_number()
        
        if not enhanced["property"].get("assessment_no"):
            enhanced["property"]["assessment_no"] = self.generate_assessment_number()
        
        if not enhanced["property"].get("extent"):
            enhanced["property"]["extent"] = self.generate_extent()
        
        # Fill boundaries with connectivity
        existing_boundaries = enhanced["property"].get("boundaries", {})
        if not existing_boundaries or len(existing_boundaries) < 4:
            new_boundaries = self.generate_boundaries(other_deed_codes)
            # Merge with existing (keep existing if present)
            for direction in ["N", "E", "S", "W"]:
                if not existing_boundaries.get(direction):
                    existing_boundaries[direction] = new_boundaries[direction]
            enhanced["property"]["boundaries"] = existing_boundaries
        
        # Fill consideration
        if enhanced.get("consideration_lkr") is None:
            enhanced["consideration_lkr"] = self.generate_consideration(deed_type)
        
        # Fill prior deed reference
        if not enhanced.get("prior_deed") and other_deed_codes and random.random() < 0.6:
            # Reference a random prior deed
            prior = random.choice(other_deed_codes)
            # Extract just the number part
            import re
            num_match = re.search(r'\d+', prior)
            if num_match:
                enhanced["prior_deed"] = num_match.group()
        
        # Fill NICs if missing
        if "ids" not in enhanced or not enhanced["ids"].get("nic_all"):
            enhanced["ids"] = {"nic_all": [self.generate_nic(), self.generate_nic()]}
        
        # Fix vendor/vendee names if they contain garbage
        for party_field in ["vendor", "vendee", "donor", "donee", "testator"]:
            if party_field in enhanced:
                names = enhanced[party_field].get("names", [])
                cleaned_names = []
                for name in names:
                    # Check if name looks valid (not too long, no deed text)
                    if name and len(name) < 50 and "deed" not in name.lower() and "virtue" not in name.lower():
                        cleaned_names.append(name)
                
                # If no valid names, generate some
                if not cleaned_names:
                    cleaned_names = [random.choice(self.sri_lankan_names)]
                    if random.random() < 0.3:
                        cleaned_names.append(random.choice(self.sri_lankan_names))
                
                enhanced[party_field]["names"] = cleaned_names
        
        # Recalculate quality score
        enhanced["source"]["quality_score"] = self.calculate_quality_score(enhanced)
        
        return enhanced
    
    def calculate_quality_score(self, deed: Dict) -> Dict:
        """Recalculate quality score for enhanced deed."""
        score = 0
        max_score = 18
        issues = []
        warnings = []
        
        # Critical fields (3 points each)
        if deed.get("type") and deed["type"] != "unknown":
            score += 3
        else:
            issues.append("Missing deed type")
        
        if deed.get("date"):
            score += 3
        else:
            issues.append("Missing date")
        
        # Important fields (2 points each)
        if deed.get("plan", {}).get("plan_no"):
            score += 2
        else:
            warnings.append("Missing Plan number")
        
        if deed.get("property", {}).get("lot"):
            score += 2
        else:
            warnings.append("Missing Lot number")
        
        if deed.get("registry_office"):
            score += 2
        else:
            warnings.append("Missing Registry office")
        
        # Useful fields (1 point each)
        if deed.get("district"):
            score += 1
        else:
            warnings.append("Missing District")
        
        if deed.get("property", {}).get("assessment_no"):
            score += 1
        else:
            warnings.append("Missing Assessment number")
        
        boundaries = deed.get("property", {}).get("boundaries", {})
        filled_boundaries = sum(1 for v in boundaries.values() if v)
        if filled_boundaries >= 3:
            score += 1
        elif filled_boundaries >= 1:
            score += 0.5
        else:
            warnings.append("Missing Boundaries")
        
        if deed.get("consideration_lkr"):
            score += 1
        else:
            if deed.get("type") not in ["gift", "will"]:
                warnings.append("Missing Consideration amount")
        
        # Parties (2 points)
        has_valid_party = False
        for party_field in ["vendor", "vendee", "donor", "donee", "testator"]:
            if party_field in deed:
                names = deed[party_field].get("names", [])
                if names and any(len(n) > 2 for n in names):
                    has_valid_party = True
                    break
        
        if has_valid_party:
            score += 2
        else:
            issues.append("No valid party names")
        
        # Calculate percentage
        percentage = (score / max_score * 100) if max_score > 0 else 0
        
        # Determine rating
        if percentage >= 85:
            rating = "EXCELLENT"
        elif percentage >= 70:
            rating = "GOOD"
        elif percentage >= 50:
            rating = "REVIEW"
        else:
            rating = "POOR"
        
        return {
            "score": round(score, 1),
            "max_score": max_score,
            "percentage": round(percentage, 1),
            "rating": rating,
            "issues": issues,
            "warnings": warnings,
            "needs_review": rating in ["REVIEW", "POOR"] or len(issues) > 0
        }
    
    def process_folder(self, input_dir: str, output_dir: str):
        """Process all deed JSON files in a folder."""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Find all JSON files
        json_files = list(input_path.glob("*.json"))
        # Exclude summary files
        json_files = [f for f in json_files if not f.name.startswith("_")]
        
        if not json_files:
            print(f"❌ No JSON files found in: {input_path}")
            return
        
        print("=" * 80)
        print("DEED DATA ENHANCER")
        print("=" * 80)
        print(f"Input:  {input_path}")
        print(f"Output: {output_path}")
        print(f"Files:  {len(json_files)}")
        print("-" * 80)
        
        # First pass: Load all deeds and collect existing codes
        deeds = []
        for json_file in sorted(json_files):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    deed = json.load(f)
                    deeds.append((json_file.name, deed))
                    
                    # Collect existing deed codes
                    if deed.get("code_number") and not deed["code_number"].startswith("UNKNOWN"):
                        self.all_deed_codes.append(deed["code_number"])
            except Exception as e:
                print(f"⚠ Error loading {json_file.name}: {e}")
        
        # Generate additional fake deed codes for connectivity
        for i in range(20):
            fake_code = self.generate_deed_code(
                random.choice(["sale_transfer", "gift", "lease"]),
                random.choice(self.all_districts)
            )
            self.all_deed_codes.append(fake_code)
        
        # Second pass: Enhance each deed
        stats = {
            "total": len(deeds),
            "enhanced": 0,
            "quality": {"EXCELLENT": 0, "GOOD": 0, "REVIEW": 0, "POOR": 0}
        }
        
        enhanced_deeds = []
        
        for filename, deed in deeds:
            try:
                print(f"\n[{stats['enhanced'] + 1}/{len(deeds)}] {filename}")
                
                # Get original quality
                orig_quality = deed.get("source", {}).get("quality_score", {})
                orig_rating = orig_quality.get("rating", "UNKNOWN")
                orig_pct = orig_quality.get("percentage", 0)
                
                # Enhance
                enhanced = self.enhance_deed(deed, self.all_deed_codes)
                
                # Get new quality
                new_quality = enhanced["source"]["quality_score"]
                new_rating = new_quality["rating"]
                new_pct = new_quality["percentage"]
                
                # Save
                output_file = output_path / filename
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(enhanced, f, indent=2, ensure_ascii=False)
                
                # Update stats
                stats["enhanced"] += 1
                stats["quality"][new_rating] += 1
                
                # Display
                improvement = new_pct - orig_pct
                status = "✓" if improvement >= 0 else "→"
                print(f"  {orig_rating} ({orig_pct}%) {status} {new_rating} ({new_pct}%)")
                
                if improvement > 0:
                    print(f"  ↑ Improved by {improvement:.1f}%")
                
                enhanced_deeds.append(enhanced)
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                import traceback
                traceback.print_exc()
        
        # Summary
        print("\n" + "=" * 80)
        print("ENHANCEMENT SUMMARY")
        print("=" * 80)
        print(f"Total files: {stats['total']}")
        print(f"Enhanced: {stats['enhanced']}")
        print(f"\nQuality Distribution:")
        for rating in ["EXCELLENT", "GOOD", "REVIEW", "POOR"]:
            count = stats["quality"][rating]
            if count > 0:
                pct = (count / stats["enhanced"] * 100) if stats["enhanced"] > 0 else 0
                bar = "█" * int(pct / 5)
                print(f"  {rating:10s}: {count:3d} ({pct:5.1f}%) {bar}")
        
        # Save cross-reference map
        xref_file = output_path / "_deed_cross_reference.json"
        with open(xref_file, 'w', encoding='utf-8') as f:
            json.dump({
                "deed_id_to_code": self.deed_id_to_code,
                "all_deed_codes": list(set(self.all_deed_codes)),
                "statistics": stats
            }, f, indent=2)
        print(f"\n✓ Cross-reference saved: {xref_file}")
        
        # Save summary
        summary_file = output_path / "_enhancement_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                "statistics": stats,
                "files_enhanced": [d["id"] for d in enhanced_deeds]
            }, f, indent=2)
        print(f"✓ Summary saved: {summary_file}")
        
        return enhanced_deeds


def main():
    print("=" * 80)
    print("DEED DATA ENHANCER")
    print("Fills missing fields and creates property connectivity")
    print("=" * 80)
    
    # Get parameters
    input_dir = sys.argv[1] if len(sys.argv) > 1 else "./deeds/processed2"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./deeds/processed_final"
    
    # Run enhancement
    enhancer = DeedDataEnhancer()
    enhancer.process_folder(input_dir, output_dir)
    
    print("\n" + "=" * 80)
    print("USAGE")
    print("=" * 80)
    print("""
# Default folders:
python enhance_deed_data.py

# Custom folders:
python enhance_deed_data.py ./deeds/processed ./deeds/enhanced

# Then load enhanced deeds into Neo4j:
python load_to_neo4j.py ./deeds/enhanced
    """)


if __name__ == "__main__":
    main()
