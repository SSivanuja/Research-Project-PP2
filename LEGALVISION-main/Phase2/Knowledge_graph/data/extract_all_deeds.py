"""
Extract deeds from DOCX files and save as separate TXT files.
Handles both:
  1. Multi-deed documents (like "30 generated data sets for six types deeds.docx")
  2. Individual deed documents (like "Deed_of_Partition.docx", "Lease_Assignment.docx", etc.)

Usage:
    python extract_all_deeds.py <input_folder> [output_folder]
    
Examples:
    python extract_all_deeds.py ./my_deeds
    python extract_all_deeds.py ./my_deeds ./deeds/unprocessed
"""

from pathlib import Path
import re
import sys


def read_docx(file_path: Path) -> str:
    """Read text from a DOCX file."""
    try:
        from docx import Document
    except ImportError:
        raise SystemExit("Please install python-docx: pip install python-docx")
    
    doc = Document(str(file_path))
    paragraphs = [p.text for p in doc.paragraphs]
    return '\n'.join(paragraphs)


def is_multi_deed_file(text: str, filename: str) -> bool:
    """
    Determine if a file contains multiple deeds.
    Returns True if it has multiple "Deed X -" markers.
    """
    # Check filename hints
    multi_deed_keywords = ['generated', 'data sets', 'multiple', 'collection', 'batch']
    if any(kw in filename.lower() for kw in multi_deed_keywords):
        # Verify with content check
        pattern = r'(?:^|\n)\s*(?:\*\*)?(?:Deed|DEED|deed)\s+\d+\s*[-–—]'
        matches = re.findall(pattern, text, re.MULTILINE)
        return len(matches) > 1

    # Content-based detection
    pattern = r'(?:^|\n)\s*(?:\*\*)?(?:Deed|DEED|deed)\s+\d+\s*[-–—]'
    matches = re.findall(pattern, text, re.MULTILINE)
    return len(matches) > 1


def split_multi_deed_document(text: str):
    """
    Split a multi-deed document into individual deeds.
    Looks for deed markers like "Deed 1 -", "DEED 2-", etc.
    """
    pattern = r'(?:^|\n)\s*(?:\*\*)?(?:Deed|DEED|deed)\s+(\d+)\s*[-–—]\s*'
    matches = list(re.finditer(pattern, text, re.MULTILINE))
    
    if not matches:
        return []

    deeds = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        
        deed_text = text[start:end].strip()
 
        # Skip very short sections
        if len(deed_text) < 200:
            continue
        
        deed_num = match.group(1)
        deeds.append((deed_num, deed_text))
    
    return deeds


def extract_deed_type(text: str, filename: str) -> str:
    """
    Extract the deed type from either the content or filename.
    Returns a normalized deed type string.
    """
    # Common deed type patterns to look for in text
    deed_type_patterns = [
        (r'DEED\s+OF\s+(TRANSFER|GIFT|MORTGAGE|PARTITION|CANCELLATION|RECTIFICATION|ASSIGNMENT)', r'\1'),
        (r'(SALE|GIFT|LEASE|MORTGAGE)\s+DEED', r'\1'),
        (r'(AGREEMENT\s+TO\s+TRANSFER)', r'\1'),
        (r'(LEASE\s+DEED)', r'\1'),
        (r'(LEASE\s+ASSIGNMENT)', r'\1'),
        (r'(MORTGAGE\s+BOND)', r'\1'),
        (r'(DISCHARGE\s+OF\s+MORTGAGE)', r'\1'),
        (r'(RIGHT\s+OF\s+WAY)', r'\1'),
        (r'(NOTICE\s+OF\s+DEFAULT)', r'\1'),
        (r'(GIFT\s+PROPERTY\s+LEASE)', r'\1'),
    ]
    
    # Try to extract from content first
    for pattern, _ in deed_type_patterns:
        match = re.search(pattern, text[:2000], re.IGNORECASE)
        if match:
            return match.group(1).upper().replace(' ', '_')
    
    # Fall back to filename
    # Remove common prefixes/suffixes and clean up
    clean_name = filename.replace('.docx', '').replace('.DOCX', '')
    clean_name = re.sub(r'^_{1,2}', '', clean_name)  # Remove leading underscores
    clean_name = re.sub(r'_{1,2}\d*_?$', '', clean_name)  # Remove trailing underscores/numbers
    clean_name = re.sub(r'\(\d+\)$', '', clean_name)  # Remove (1), (2), etc.
    clean_name = clean_name.strip('_').strip()
    
    return clean_name.upper().replace(' ', '_')


def clean_text(text: str) -> str:
    """Clean up text formatting."""
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def generate_unique_filename(output_path: Path, base_name: str, extension: str = ".txt") -> Path:
    """Generate a unique filename by appending a number if file exists."""
    candidate = output_path / f"{base_name}{extension}"
    if not candidate.exists():
        return candidate
    
    counter = 1
    while True:
        candidate = output_path / f"{base_name}_{counter:03d}{extension}"
        if not candidate.exists():
            return candidate
        counter += 1


def extract_all_deeds(
    input_folder: str = "./unput",
    output_dir: str = "./deeds/unprocessed2"
):
    """
    Main function to extract all deeds from all DOCX files in a folder.
    
    Args:
        input_folder: Path to folder containing DOCX files
        output_dir: Directory to save individual deed TXT files
    """
    input_path = Path(input_folder)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("UNIVERSAL DEED EXTRACTOR - DOCX TO TXT")
    print("=" * 80)
    print(f"Input folder:  {input_path.absolute()}")
    print(f"Output folder: {output_path.absolute()}")
    print("-" * 80)
    
    # Find all DOCX files
    docx_files = list(input_path.glob("*.docx")) + list(input_path.glob("*.DOCX"))
    
    if not docx_files:
        print(f"❌ No DOCX files found in: {input_path}")
        return
    
    print(f"✓ Found {len(docx_files)} DOCX file(s)")
    print("-" * 80)
    
    total_deeds = 0
    deed_counter = 1  # Global counter for multi-deed files
    
    for docx_file in sorted(docx_files):
        print(f"\n📄 Processing: {docx_file.name}")
        
        try:
            text = read_docx(docx_file)
            print(f"   Read {len(text):,} characters")
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")
            continue
        
        if is_multi_deed_file(text, docx_file.name):
            # Handle multi-deed document
            print("   📚 Detected: Multi-deed document")
            deeds = split_multi_deed_document(text)
            
            if not deeds:
                print("   ⚠ Could not split deeds")
                continue
            
            print(f"   ✓ Found {len(deeds)} deeds")
            
            for deed_num, deed_text in deeds:
                deed_text = clean_text(deed_text)
                deed_type = extract_deed_type(deed_text, "")
                
                # Create filename: DEED_001_SALE.txt, DEED_002_GIFT.txt, etc.
                base_name = f"DEED_{deed_counter:03d}_{deed_type}" if deed_type else f"DEED_{deed_counter:03d}"
                output_file = generate_unique_filename(output_path, base_name)
                
                output_file.write_text(deed_text, encoding='utf-8')
                
                preview = deed_text[:60].replace('\n', ' ')
                print(f"   ✓ {output_file.name:40s} ({len(deed_text):6,} chars)")
                
                deed_counter += 1
                total_deeds += 1
        else:
            # Handle single-deed document
            print("   📄 Detected: Single-deed document")
            deed_text = clean_text(text)
            deed_type = extract_deed_type(deed_text, docx_file.name)
            
            # Create filename based on deed type
            base_name = f"DEED_{deed_type}" if deed_type else f"DEED_{docx_file.stem}"
            output_file = generate_unique_filename(output_path, base_name)
            
            output_file.write_text(deed_text, encoding='utf-8')
            
            print(f"   ✓ {output_file.name:40s} ({len(deed_text):6,} chars)")
            total_deeds += 1
    
    print("\n" + "=" * 80)
    print("EXTRACTION COMPLETE")
    print("=" * 80)
    print(f"✓ Processed {len(docx_files)} DOCX file(s)")
    print(f"✓ Created {total_deeds} deed TXT file(s) in: {output_path}")
    print(f"\nNext step:")
    print(f"  python deed_ner_inference.py {output_dir} ./deeds/processed2")


if __name__ == "__main__":
    # Get parameters from command line or use defaults
    input_folder = sys.argv[1] if len(sys.argv) > 1 else "./input"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./deeds/unprocessed2"
    
    # Run extraction
    extract_all_deeds(input_folder, output_dir)
    
    print("\n" + "=" * 80)
    print("USAGE:")
    print("=" * 80)
    print("""
# Process all DOCX files in current directory:
python extract_all_deeds.py

# Process all DOCX files in a specific folder:
python extract_all_deeds.py ./my_deeds_folder

# Specify both input folder and output folder:
python extract_all_deeds.py ./my_deeds_folder ./output_folder

# Example with your files:
# Put all your files in one folder, then run:
python extract_all_deeds.py ./all_my_deeds ./deeds/unprocessed
    """)