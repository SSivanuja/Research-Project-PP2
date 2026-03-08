"""
Extract individual deeds from a DOCX document and save as separate TXT files.
"""

from pathlib import Path
import re


def read_docx(file_path: Path) -> str:
    """Read text from a DOCX file."""
    try:
        from docx import Document
    except ImportError:
        raise SystemExit("Please install python-docx: pip install python-docx")
    
    doc = Document(str(file_path))
    paragraphs = [p.text for p in doc.paragraphs]
    return '\n'.join(paragraphs)


def split_deeds(text: str):
    """
    Split document into individual deeds.
    Looks for deed markers like "Deed 1 -", "DEED 2-", etc.
    """
    # Pattern to match deed headers
    pattern = r'(?:^|\n)\s*(?:\*\*)?(?:Deed|DEED|deed)\s+(\d+)\s*[-–—]\s*'
    
    # Find all deed positions
    matches = list(re.finditer(pattern, text, re.MULTILINE))
    
    if not matches:
        print("⚠ No deed markers found. Trying alternative patterns...")
        # Try alternative pattern
        pattern = r'(?:^|\n)\s*(?:DEED OF|Deed of|deed of)\s+(TRANSFER|GIFT|MORTGAGE|WILL)'
        matches = list(re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE))
    
    if not matches:
        print("❌ Could not find deed separators")
        return []
    
    deeds = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        
        deed_text = text[start:end].strip()
        
        # Skip very short sections
        if len(deed_text) < 200:
            continue
        
        # Extract deed number from match
        deed_num = match.group(1) if match.lastindex and match.lastindex >= 1 else str(i + 1)
        
        deeds.append((deed_num, deed_text))
    
    return deeds


def clean_text(text: str) -> str:
    """Clean up text formatting."""
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def extract_deeds_to_txt(
    docx_file: str = "30 generated data sets for six types deeds.docx",
    output_dir: str = "./deeds/unprocessed"
):
    """
    Main function to extract deeds and save as TXT files.
    
    Args:
        docx_file: Path to input DOCX file
        output_dir: Directory to save individual deed TXT files
    """
    docx_path = Path(docx_file)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("="*80)
    print("DEED EXTRACTOR - DOCX TO TXT")
    print("="*80)
    print(f"Input:  {docx_path}")
    print(f"Output: {output_path}")
    print("-"*80)
    
    # Check if file exists
    if not docx_path.exists():
        print(f"❌ File not found: {docx_path}")
        return
    
    # Read DOCX
    print("\nReading DOCX file...")
    try:
        full_text = read_docx(docx_path)
        print(f"✓ Read {len(full_text):,} characters")
    except Exception as e:
        print(f"❌ Error reading DOCX: {e}")
        return
    
    # Split into deeds
    print("\nSplitting into individual deeds...")
    deeds = split_deeds(full_text)
    
    if not deeds:
        print("❌ No deeds found")
        return
    
    print(f"✓ Found {len(deeds)} deeds")
    
    # Save each deed
    print("\nSaving deed files...")
    print("-"*80)
    
    for deed_num, deed_text in deeds:
        # Clean text
        deed_text = clean_text(deed_text)
        
        # Create filename
        output_file = output_path / f"DEED_{int(deed_num):03d}.txt"
        
        # Save
        output_file.write_text(deed_text, encoding='utf-8')
        
        # Show preview
        preview = deed_text[:80].replace('\n', ' ')
        print(f"✓ {output_file.name:15s} ({len(deed_text):6,} chars) - {preview}...")
    
    print("\n" + "="*80)
    print("EXTRACTION COMPLETE")
    print("="*80)
    print(f"✓ Created {len(deeds)} deed files in: {output_path}")
    print(f"\nNext step:")
    print(f"  python deed_ner_inference.py {output_dir} ./deeds/processed")


if __name__ == "__main__":
    import sys
    
    # Get parameters from command line or use defaults
    docx_file = sys.argv[1] if len(sys.argv) > 1 else "30 generated data sets for six types deeds.docx"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./deeds/unprocessed"
    
    # Run extraction
    extract_deeds_to_txt(docx_file, output_dir)
    
    print("\n" + "="*80)
    print("USAGE:")
    print("="*80)
    print("""
# Default (looks for "30 generated data sets for six types deeds.docx"):
python extract_deeds.py

# Custom input file:
python extract_deeds.py "my_deeds.docx"

# Custom input and output:
python extract_deeds.py "my_deeds.docx" ./output_folder
    """)