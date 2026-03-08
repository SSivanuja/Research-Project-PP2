"""
Annotate Sri Lankan property deeds for NER training.
Reads TXT files from unprocessed folder and creates SpaCy training/test files.

Usage:
    python annotate_deeds_from_txt.py [input_folder] [output_folder]
    
Examples:
    python annotate_deeds_from_txt.py ./deeds/unprocessed2 ./deeds/annotated
    python annotate_deeds_from_txt.py  # Uses defaults

Outputs:
    - train.json  (SpaCy training format)
    - test.json   (SpaCy test format - same data for now)
"""

import re
import random
import json
from pathlib import Path
from typing import List, Tuple, Dict
import sys


class DeedEntityAnnotator:
    """
    Automatically annotate Sri Lankan property deeds for NER training.
    Extracts entities like parties, properties, dates, amounts, etc.
    """
    
    def __init__(self):
        self.entity_patterns = {
            # Party patterns
            'PARTY_VENDOR': [
                r'VENDOR[:\s]+([A-Z][A-Z\s.]+?)(?:\s+\(|of No)',
                r'(?:said|within-named)\s+(?:VENDOR|Donor)\s+([A-Z][A-Z\s.]+?)(?:\s+\(|of)',
                r'I,?\s+([A-Z][A-Z\s.]+?)\s+\(holder of',
                r'TRANSFEROR[:\s]+([A-Z][A-Z\s.]+?)(?:\s+\(|of No)',
                r'LESSOR[:\s]+([A-Z][A-Z\s.]+?)(?:\s+\(|of No)',
                r'MORTGAGOR[:\s]+([A-Z][A-Z\s.]+?)(?:\s+\(|of No)',
                r'DONOR[:\s]+([A-Z][A-Z\s.]+?)(?:\s+\(|of No)',
            ],
            'PARTY_VENDEE': [
                r'VENDEE[:\s]+([A-Z][A-Z\s.]+?)(?:\s+\(|of No)',
                r'(?:said|within-named)\s+(?:VENDEE|Donee|Purchaser)\s+([A-Z][A-Z\s.]+?)(?:\s+\(|of)',
                r'TRANSFEREE[:\s]+([A-Z][A-Z\s.]+?)(?:\s+\(|of No)',
                r'LESSEE[:\s]+([A-Z][A-Z\s.]+?)(?:\s+\(|of No)',
                r'MORTGAGEE[:\s]+([A-Z][A-Z\s.]+?)(?:\s+\(|of No)',
                r'DONEE[:\s]+([A-Z][A-Z\s.]+?)(?:\s+\(|of No)',
            ],
            'PARTY_NOTARY': [
                r'I,\s+([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+of\s+\w+\s+.*?Notary Public',
                r'attested by\s+([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),?\s+Notary',
                r'NOTARY PUBLIC[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            ],
            'PARTY_WITNESS': [
                r'presence of\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
                r'WITNESS(?:ES)?[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            ],
            
            # Property identifiers
            'PROPERTY_LOT': [
                r'Lot\s+([A-Z0-9]+)',
                r'lot\s+([0-9]+[A-Z]?)',
                r'marked\s+Lot\s+([0-9A-Z]+)',
            ],
            'PROPERTY_PLAN': [
                r'Plan No[.:]?\s*([0-9]+)',
                r'plan\s+No[.:]?\s*([0-9]+)',
                r'Survey Plan No[.:]?\s*([0-9A-Z/]+)',
            ],
            'PROPERTY_ADDRESS': [
                r'Assessment No[.:]?\s*([0-9/A-Za-z,-]+)',
                r'bearing\s+(?:assessment|Assessment)\s+No[.:]?\s*([0-9/A-Za-z,-]+)',
                r'premises No[.:]?\s*([0-9/A-Za-z,-]+)',
            ],
            
            # Administrative
            'REGISTRY_OFFICE': [
                r'(?:Land Registry|Land registry|registry)\s+(?:at|office)\s+([A-Z][a-z]+(?:-[A-Z][a-z]+)?)',
                r'Registered\s+at\s+the\s+([A-Z][a-z]+(?:-[A-Z][a-z]+)?)\s+Land\s+Registry',
            ],
            'REGISTRATION_NUMBER': [
                r'(?:registered under|under title|folio)\s+([A-Z]\s*[0-9]+/[0-9]+)',
                r'Registration No[.:]?\s*([A-Z0-9/]+)',
                r'Deed No[.:]?\s*([0-9]+)',
            ],
            'DISTRICT': [
                r'District of\s+([A-Z][a-z]+)',
                r'in the\s+([A-Z][a-z]+)\s+District',
            ],
            'PROVINCE': [
                r'(Western|Central|Southern|Northern|Eastern|North Western|North Central|Uva|Sabaragamuwa)\s+Province',
            ],
            'DIVISIONAL_SECRETARIAT': [
                r'Divisional Secretariat(?:\s+Division)?\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
                r'D\.?S\.?\s+Division\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            ],
            'GRAMA_NILADHARI': [
                r'Grama Niladhari Division\s+(?:of\s+)?([A-Z0-9/-]+)',
                r'G\.?N\.?\s+Division\s+([A-Z0-9/-]+)',
            ],
            
            # Legal references
            'DEED_TYPE': [
                r'DEED OF (TRANSFER|GIFT|MORTGAGE|PARTITION|CANCELLATION|RECTIFICATION)',
                r'(LEASE DEED|LEASE ASSIGNMENT|LAST WILL|MORTGAGE BOND|AGREEMENT TO (?:SELL|TRANSFER))',
                r'(DISCHARGE OF MORTGAGE|RIGHT OF WAY|NOTICE OF DEFAULT)',
                r'(GIFT PROPERTY LEASE)',
            ],
            'PRIOR_DEED': [
                r'Deed No[.:]?\s*([0-9]+)\s+dated\s+[0-9]{2}\.[0-9]{2}\.[0-9]{4}',
                r'under and by virtue of Deed No[.:]?\s*([0-9]+)',
                r'by virtue of\s+(?:Deed|deed)\s+No[.:]?\s*([0-9]+)',
            ],
            
            # Dates
            'DATE': [
                r'([0-9]{1,2}(?:st|nd|rd|th)?\s+(?:day of\s+)?(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+(?:Two Thousand (?:and\s+)?)?[0-9]{4})',
                r'dated\s+([0-9]{2}\.[0-9]{2}\.[0-9]{4})',
                r'dated\s+([0-9]{2}/[0-9]{2}/[0-9]{4})',
                r'on\s+([0-9]{2}\.[0-9]{2}\.[0-9]{4})',
            ],
            
            # Amounts
            'AMOUNT': [
                r'(?:Rupees|Rs\.?)\s+((?:[A-Z][a-z]+\s+)*(?:Million|Thousand|Hundred)(?:\s+(?:[A-Z][a-z]+\s+)*(?:Thousand|Hundred))*)',
                r'Rs\.?\s*([0-9]{1,3}(?:,?[0-9]{3})+)/?-?',
                r'consideration of\s+(?:Rupees|Rs\.?)\s*([0-9]{1,3}(?:,?[0-9]{3})+)',
            ],
            
            # Area measurements
            'AREA': [
                r'([0-9]+\s*(?:decimal|Decimal)?\s*[0-9]*\s*(?:perches|Perches))',
                r'\(A[0-9]+-?R[0-9]+-?P[0-9.]+\)',
                r'([0-9]+(?:\.[0-9]+)?)\s+(?:Square Feet|square feet|sq\.?\s*ft)',
                r'([0-9]+)\s+(?:Acres?|acres?)',
                r'([0-9]+)\s+(?:Roods?|roods?)',
            ],
            
            # NIC numbers
            'NIC': [
                r'NIC No\.?\s*([0-9]{9}[VXvx]|[0-9]{12})',
                r'National Identity Card No\.?\s*([0-9]{9}[VXvx]|[0-9]{12})',
                r'N\.?I\.?C\.?\s*[:\-]?\s*([0-9]{9}[VXvx]|[0-9]{12})',
            ],
            
            # Boundaries
            'BOUNDARY_NORTH': [
                r'North\s*[:\-]?\s*(?:by\s+)?([A-Za-z0-9\s,\.]+?)(?=\s*(?:South|East|West|;|\n|$))',
            ],
            'BOUNDARY_SOUTH': [
                r'South\s*[:\-]?\s*(?:by\s+)?([A-Za-z0-9\s,\.]+?)(?=\s*(?:North|East|West|;|\n|$))',
            ],
            'BOUNDARY_EAST': [
                r'East\s*[:\-]?\s*(?:by\s+)?([A-Za-z0-9\s,\.]+?)(?=\s*(?:North|South|West|;|\n|$))',
            ],
            'BOUNDARY_WEST': [
                r'West\s*[:\-]?\s*(?:by\s+)?([A-Za-z0-9\s,\.]+?)(?=\s*(?:North|South|East|;|\n|$))',
            ],
            
            # Lease specific
            'LEASE_TERM': [
                r'(?:term|period)\s+of\s+([0-9]+)\s+(?:years?|months?)',
                r'for\s+([0-9]+)\s+(?:years?|months?)',
            ],
            'RENT_AMOUNT': [
                r'(?:monthly|annual)\s+rent\s+of\s+(?:Rs\.?|Rupees)\s*([0-9,]+)',
                r'rent\s+(?:of\s+)?(?:Rs\.?|Rupees)\s*([0-9,]+)\s+per\s+(?:month|annum)',
            ],
            
            # Mortgage specific
            'LOAN_AMOUNT': [
                r'(?:loan|principal)\s+(?:sum|amount)\s+of\s+(?:Rs\.?|Rupees)\s*([0-9,]+)',
                r'(?:sum|amount)\s+of\s+(?:Rs\.?|Rupees)\s*([0-9,]+)\s+(?:as\s+)?(?:loan|mortgage)',
            ],
            'INTEREST_RATE': [
                r'interest\s+(?:rate\s+)?(?:of\s+)?([0-9]+(?:\.[0-9]+)?)\s*%',
                r'([0-9]+(?:\.[0-9]+)?)\s*%\s+(?:per\s+)?(?:annum|interest)',
            ],
        }
    
    def extract_entities(self, text: str) -> List[Tuple[int, int, str]]:
        """
        Extract all entities from text.
        Returns list of (start, end, label) tuples for SpaCy format.
        """
        entities = []
        
        for label, patterns in self.entity_patterns.items():
            for pattern in patterns:
                try:
                    for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                        # Get the captured group or full match
                        if match.groups():
                            start = match.start(1)
                            end = match.end(1)
                            matched_text = match.group(1)
                        else:
                            start = match.start()
                            end = match.end()
                            matched_text = match.group(0)
                        
                        # Skip empty or very short matches
                        matched_text = matched_text.strip()
                        if not matched_text or len(matched_text) < 2:
                            continue
                        
                        # Avoid overlapping entities (keep first match)
                        overlaps = False
                        for existing_start, existing_end, _ in entities:
                            if not (end <= existing_start or start >= existing_end):
                                overlaps = True
                                break
                        
                        if not overlaps:
                            entities.append((start, end, label))
                except re.error:
                    continue
        
        # Sort by start position
        entities.sort(key=lambda x: x[0])
        return entities
    
    def process_txt_folder(self, input_folder: str) -> List[Tuple[str, Dict]]:
        """
        Process all TXT files in a folder.
        Returns SpaCy format: [(text, {"entities": [(start, end, label)]}), ...]
        """
        input_path = Path(input_folder)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Folder not found: {input_folder}")
        
        # Find all TXT files
        txt_files = sorted(input_path.glob("*.txt")) + sorted(input_path.glob("*.TXT"))
        
        if not txt_files:
            raise ValueError(f"No TXT files found in: {input_folder}")
        
        print(f"Found {len(txt_files)} TXT file(s)")
        print("-" * 80)
        
        spacy_data = []
        total_entities = 0
        
        for txt_file in txt_files:
            try:
                # Read the text file
                text = txt_file.read_text(encoding='utf-8')
                
                # Extract entities
                entities = self.extract_entities(text)
                
                # Add to SpaCy format data
                spacy_data.append((text, {"entities": entities}))
                
                total_entities += len(entities)
                print(f"✓ {txt_file.stem:40s} → {len(entities):3d} entities")
                
            except Exception as e:
                print(f"✗ {txt_file.name}: Error - {e}")
                continue
        
        print("-" * 80)
        print(f"Total: {len(spacy_data)} deeds, {total_entities} entities")
        
        return spacy_data
    
    def get_entity_stats(self, spacy_data: List[Tuple[str, Dict]]) -> Dict:
        """Get statistics about extracted entities."""
        stats = {
            'total_deeds': len(spacy_data),
            'total_entities': 0,
            'entity_distribution': {},
        }
        
        for text, annotation in spacy_data:
            for start, end, label in annotation['entities']:
                stats['total_entities'] += 1
                stats['entity_distribution'][label] = \
                    stats['entity_distribution'].get(label, 0) + 1
        
        return stats


def main():
    print("=" * 80)
    print("SRI LANKAN DEED ENTITY ANNOTATOR")
    print("=" * 80)
    
    # Get parameters from command line or use defaults
    input_folder = sys.argv[1] if len(sys.argv) > 1 else "../data/deeds/unprocessed2"
    output_folder = sys.argv[2] if len(sys.argv) > 2 else "../data/deeds/annotated"
    
    print(f"\nInput folder:  {input_folder}")
    print(f"Output folder: {output_folder}")
    print("-" * 80)
    
    # Initialize annotator
    annotator = DeedEntityAnnotator()
    
    try:
        # Process all TXT files
        spacy_data = annotator.process_txt_folder(input_folder)
        
        if not spacy_data:
            print("\n❌ No deeds were annotated")
            return
        
        # Create output folder
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save train.json (100% of data)
        train_file = output_path / "train.json"
        with open(train_file, 'w', encoding='utf-8') as f:
            json.dump(spacy_data, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Saved training data: {train_file} ({len(spacy_data)} deeds)")

        # Save test.json (20% of data)
        test_size = max(1, int(len(spacy_data) * 0.2))
        test_data = random.sample(spacy_data, test_size)
        test_file = output_path / "test.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved test data:     {test_file} ({len(test_data)} deeds)")
        
        # Show statistics
        print("\n" + "=" * 80)
        print("STATISTICS")
        print("=" * 80)
        
        stats = annotator.get_entity_stats(spacy_data)
        
        print(f"\nTotal Deeds:    {stats['total_deeds']}")
        print(f"Total Entities: {stats['total_entities']}")
        print(f"Avg per Deed:   {stats['total_entities'] / stats['total_deeds']:.1f}")
        
        print(f"\nEntity Distribution:")
        for label, count in sorted(stats['entity_distribution'].items(), 
                                   key=lambda x: x[1], reverse=True):
            print(f"  {label:30s}: {count:4d}")
        
        print("\n" + "=" * 80)
        print("OUTPUT FILES")
        print("=" * 80)
        print(f"  {train_file}")
        print(f"  {test_file}")
        
        print("\n" + "=" * 80)
        print("SPACY FORMAT")
        print("=" * 80)
        print('  [(text, {"entities": [(start, end, label), ...]}), ...]')
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print(f"\nMake sure to run the extractor first:")
        print(f"  python extract_all_deeds.py <docx_folder> {input_folder}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
