"""
Sri Lankan Property Law Data Downloader - Version 2 (Fixed URLs)
Downloads legal texts from various sources for LLM fine-tuning

Author: S. Sivanuja
Project: LegalVision - Explainable Legal Reasoning Module
"""

import os
import re
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from bs4 import BeautifulSoup

# Configuration
OUTPUT_DIR = Path("./data/sri_lankan_laws")
RAW_DIR = OUTPUT_DIR / "raw"
PROCESSED_DIR = OUTPUT_DIR / "processed"
METADATA_FILE = OUTPUT_DIR / "metadata.json"

# Create directories
for dir_path in [OUTPUT_DIR, RAW_DIR, PROCESSED_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Headers to mimic browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


class SriLankanLawDownloader:
    """Downloads Sri Lankan property law data from multiple sources."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.metadata = {"downloaded_at": datetime.now().isoformat(), "sources": [], "documents": []}
        self.stats = {"total": 0, "success": 0, "failed": 0}

    # =========================================================================
    # CORRECT URLs for SriLankaLaw.lk (Updated December 2025)
    # =========================================================================
    
    PROPERTY_LAW_URLS = {
        # Registration Laws
        "registration_of_documents_ordinance": {
            "title": "Registration of Documents Ordinance",
            "url": "https://www.srilankalaw.lk/revised-statutes/volume-vii/1013-registration-of-documents-ordinance.html",
            "category": "registration"
        },
        "registration_of_title_act": {
            "title": "Registration of Title Act No. 21 of 1998",
            "url": "https://www.srilankalaw.lk/revised-statutes/volume-vii/1019-registration-of-title-act.html",
            "category": "registration"
        },
        "registration_of_old_deeds_ordinance": {
            "title": "Registration of Old Deeds and Instruments Ordinance",
            "url": "https://www.srilankalaw.lk/revised-statutes/alphabetical-list-of-statutes/1017-registration-of-old-deeds-and-instruments-ordinance.html",
            "category": "registration"
        },
        
        # Land Development and State Lands
        "land_development_ordinance": {
            "title": "Land Development Ordinance",
            "url": "https://www.srilankalaw.lk/l/604-land-development-ordinance.html",
            "category": "land_development"
        },
        "land_settlement_ordinance": {
            "title": "Land Settlement Ordinance",
            "url": "https://www.srilankalaw.lk/revised-statutes/volume-v/610-land-settlement-ordinance.html",
            "category": "settlement"
        },
        "land_reform_law": {
            "title": "Land Reform Law",
            "url": "https://www.srilankalaw.lk/l/608-land-reform-law.html",
            "category": "land_reform"
        },
        "land_grants_special_provisions_act": {
            "title": "Land Grants (Special Provisions) Act",
            "url": "https://www.srilankalaw.lk/revised-statutes/alphabetical-list-of-statutes/605-land-grants-special-provisions-act.html",
            "category": "land_grants"
        },
        
        # Survey
        "survey_act": {
            "title": "Survey Act",
            "url": "https://www.srilankalaw.lk/revised-statutes/volume-vii/1259-survey-act.html",
            "category": "survey"
        },
        
        # Rent and Tenancy
        "rent_act": {
            "title": "Rent Act",
            "url": "https://www.srilankalaw.lk/revised-statutes/volume-vii/1032-rent-act.html",
            "category": "tenancy"
        },
        
        # Additional Property Laws
        "partition_act": {
            "title": "Partition Act",
            "url": "https://www.srilankalaw.lk/revised-statutes/volume-vi/882-partition-act.html",
            "category": "partition"
        },
        "prescription_ordinance": {
            "title": "Prescription Ordinance",
            "url": "https://www.srilankalaw.lk/revised-statutes/volume-vi/905-prescription-ordinance.html",
            "category": "prescription"
        },
        "mortgage_act": {
            "title": "Mortgage Act",
            "url": "https://www.srilankalaw.lk/revised-statutes/volume-vi/742-mortgage-act.html",
            "category": "mortgage"
        },
        "trust_ordinance": {
            "title": "Trust Ordinance",
            "url": "https://www.srilankalaw.lk/revised-statutes/volume-viii/1334-trust-ordinance.html",
            "category": "trusts"
        },
        "notaries_ordinance": {
            "title": "Notaries Ordinance",
            "url": "https://www.srilankalaw.lk/revised-statutes/volume-vi/776-notaries-ordinance.html",
            "category": "notaries"
        },
        "prevention_of_frauds_ordinance": {
            "title": "Prevention of Frauds Ordinance",
            "url": "https://www.srilankalaw.lk/revised-statutes/volume-vi/906-prevention-of-frauds-ordinance.html",
            "category": "fraud_prevention"
        },
        "civil_procedure_code": {
            "title": "Civil Procedure Code",
            "url": "https://www.srilankalaw.lk/revised-statutes/volume-ii/181-civil-procedure-code.html",
            "category": "procedure"
        },
        "evidence_ordinance": {
            "title": "Evidence Ordinance",
            "url": "https://www.srilankalaw.lk/revised-statutes/volume-iv/300-evidence-ordinance.html",
            "category": "evidence"
        },
        "state_lands_ordinance": {
            "title": "State Lands Ordinance",
            "url": "https://www.srilankalaw.lk/revised-statutes/volume-vii/1195-state-lands-ordinance.html",
            "category": "state_lands"
        },
        "land_acquisition_act": {
            "title": "Land Acquisition Act",
            "url": "https://www.srilankalaw.lk/revised-statutes/volume-v/598-land-acquisition-act.html",
            "category": "acquisition"
        },
        "apartment_ownership_law": {
            "title": "Apartment Ownership Law",
            "url": "https://www.srilankalaw.lk/revised-statutes/volume-i/66-apartment-ownership-law.html",
            "category": "apartment"
        },
        "condominium_management_authority_act": {
            "title": "Condominium Management Authority Act",
            "url": "https://www.srilankalaw.lk/revised-statutes/volume-ii/195-condominium-management-authority-act.html",
            "category": "condominium"
        },
    }

    def download_from_srilankalaw(self, key: str, info: Dict) -> Optional[Dict]:
        """Download a specific law from srilankalaw.lk"""
        print(f"\n  Downloading: {info['title']}")
        
        try:
            response = self.session.get(info['url'], timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple content selectors
            content = None
            selectors = [
                ('div', {'class': 'item-page'}),
                ('div', {'class': 'content'}),
                ('article', {}),
                ('div', {'id': 'content'}),
                ('main', {}),
            ]
            
            for tag, attrs in selectors:
                content = soup.find(tag, attrs) if attrs else soup.find(tag)
                if content:
                    break
            
            if content:
                for unwanted in content.find_all(['nav', 'script', 'style', 'header', 'footer', 'aside']):
                    unwanted.decompose()
                text = content.get_text(separator='\n', strip=True)
            else:
                body = soup.find('body')
                if body:
                    for unwanted in body.find_all(['nav', 'script', 'style', 'header', 'footer', 'aside']):
                        unwanted.decompose()
                    text = body.get_text(separator='\n', strip=True)
                else:
                    text = soup.get_text(separator='\n', strip=True)
            
            text = self.clean_legal_text(text)
            
            if len(text) < 500:
                print(f"    ⚠ Content too short ({len(text)} chars)")
            
            filename = f"{key}.txt"
            filepath = RAW_DIR / filename
            filepath.write_text(text, encoding='utf-8')
            
            doc_meta = {
                "id": key,
                "title": info['title'],
                "category": info['category'],
                "source_url": info['url'],
                "source": "srilankalaw.lk",
                "filename": filename,
                "char_count": len(text),
                "word_count": len(text.split()),
                "downloaded_at": datetime.now().isoformat(),
                "needs_review": len(text) < 1000
            }
            
            print(f"    ✓ Saved: {filename} ({len(text):,} chars)")
            self.stats["success"] += 1
            return doc_meta
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"    ✗ 404 Not Found")
            else:
                print(f"    ✗ HTTP Error: {e}")
            self.stats["failed"] += 1
            return None
        except Exception as e:
            print(f"    ✗ Error: {e}")
            self.stats["failed"] += 1
            return None

    def clean_legal_text(self, text: str) -> str:
        """Clean and normalize legal text."""
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        nav_patterns = [
            r'Home\s*›.*?\n',
            r'Revised Statutes\s*›.*?\n',
            r'Volume [IVX]+\s*›.*?\n',
            r'Subscribe Now.*?\n',
            r'Contact Us.*?\n',
            r'Bulletin-\d{4}.*?\n',
            r'Last Updated:.*?\n',
            r'©.*?rights reserved.*?\n',
            r'A\s+B\s+C\s+D\s+E\s+F\s+G.*?Z\s*\n',
        ]
        
        for pattern in nav_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        text = re.sub(r'(Volume [IVX]+\s*)+', '', text)
        
        return text.strip()

    def create_property_law_definitions(self) -> Dict:
        """Create a comprehensive glossary of Sri Lankan property law terms."""
        
        definitions = {
            "title": "Sri Lankan Property Law - Legal Definitions and Concepts",
            "terms": {
                "Deed": "A legal document that transfers ownership of property from one party to another. In Sri Lanka, deeds must be attested by a notary public and registered at the Land Registry.",
                "Folio": "A registered title entry in the Land Registry containing all relevant information about a property including ownership, encumbrances, and dealings.",
                "Encumbrance": "A claim or liability attached to property, such as a mortgage, lease, or easement, that may affect its transferability.",
                "Caveat": "A formal notice lodged with the Land Registry to prevent registration of dealings with the property until the caveator's claim is resolved.",
                "Lis Pendens": "A notice that litigation is pending which may affect the title to the land.",
                "Priority Notice": "A notice lodged to protect priority for a forthcoming instrument.",
                "Fee Simple": "The highest form of ownership in land, giving the owner complete control over the property subject only to governmental powers.",
                "Life Estate": "An interest in property that lasts only for the lifetime of a specified person.",
                "Dominium": "Absolute ownership under Roman-Dutch law, the highest form of right over property.",
                "Tenancy in Common": "A form of co-ownership where each owner holds a distinct share that can be transferred independently.",
                "Joint Tenancy": "A form of co-ownership where owners hold property together with right of survivorship.",
                "Partition": "The division of co-owned property among the co-owners, either by agreement or court order under the Partition Act.",
                "Conveyance": "The transfer of property ownership from one person to another by deed.",
                "Gift (Donation)": "A voluntary transfer of property without consideration, requiring acceptance by the donee.",
                "Mortgage": "A security interest in property given to secure repayment of a loan.",
                "Parate Execution": "Special right of banks to sell mortgaged property without court intervention.",
                "Lease": "A contract granting exclusive possession of property for a specified period in exchange for rent.",
                "Protected Tenant": "A tenant with security of tenure under the Rent Act.",
                "State Land": "Land owned by the government, governed by the State Lands Ordinance.",
                "Permit Land": "State land alienated under a permit with conditions.",
                "Survey Plan": "An official document prepared by a licensed surveyor showing property boundaries and measurements.",
                "Cadastral Map": "Official map showing property boundaries for title registration purposes.",
                "Rei Vindicatio": "A Roman-Dutch law action to recover possession of property.",
                "Interdict": "A court order preventing certain actions related to property.",
                "Land Registry": "The government office responsible for registering land transactions.",
                "Notary Public": "A licensed professional authorized to attest deeds and legal documents.",
                "Bim Saviya": "The Title Registration program in Sri Lanka under the Registration of Title Act.",
                "Thesawalamai": "Personal law applicable to Jaffna Tamils affecting property rights.",
                "Kandyan Law": "Personal law applicable to Kandyan Sinhalese affecting property and inheritance.",
                "First Class Title": "Title of Absolute Ownership under Registration of Title Act with state guarantee.",
                "Second Class Title": "Title requiring 10 years possession before conversion to First Class.",
                "Acquisitive Prescription": "Acquiring title through continuous adverse possession for statutory period.",
                "Perch": "A unit of land measurement equal to 25.29 square meters or 272.25 square feet.",
                "Rood": "A unit of land measurement equal to 40 perches.",
                "Acre": "A unit of land measurement equal to 4 roods or 160 perches.",
                "A-R-P": "Acres-Roods-Perches, the standard format for expressing land extent in Sri Lanka.",
            }
        }
        
        json_path = PROCESSED_DIR / "property_law_definitions.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(definitions, f, indent=2, ensure_ascii=False)
        
        text_content = f"# {definitions['title']}\n\n"
        for term, definition in definitions['terms'].items():
            text_content += f"## {term}\n{definition}\n\n"
        
        txt_path = RAW_DIR / "property_law_definitions.txt"
        txt_path.write_text(text_content, encoding='utf-8')
        
        print(f"  ✓ Created definitions file with {len(definitions['terms'])} terms")
        
        return {
            "id": "property_law_definitions",
            "title": definitions['title'],
            "category": "definitions",
            "source": "compiled",
            "filename": "property_law_definitions.txt",
            "term_count": len(definitions['terms']),
            "downloaded_at": datetime.now().isoformat()
        }

    def create_deed_templates(self) -> Dict:
        """Create sample deed templates for training."""
        
        templates = {
            "sale_deed": """DEED OF TRANSFER

I, [VENDOR NAME] (holder of National Identity Card No. [NIC]) of [ADDRESS] (hereinafter called the "VENDOR") being the owner of the land and premises described in the Schedule hereto, in consideration of the sum of Rupees [AMOUNT IN WORDS] (Rs. [AMOUNT]) paid to me by [VENDEE NAME] (holder of National Identity Card No. [NIC]) of [ADDRESS] (hereinafter called the "VENDEE"), the receipt whereof I do hereby acknowledge, do hereby grant, convey, transfer and assign unto the said VENDEE, his/her heirs, executors, administrators and assigns ALL THAT the land and premises described in the Schedule hereto together with all buildings, structures, plantations, rights, privileges, easements, and appurtenances thereunto belonging.

TO HAVE AND TO HOLD the said land and premises unto the said VENDEE absolutely and forever freed from all encumbrances.

SCHEDULE

ALL THAT divided and defined allotment of land marked Lot [LOT NUMBER] depicted in Plan No. [PLAN NUMBER] dated [PLAN DATE] made by [SURVEYOR NAME], Licensed Surveyor, situated at [LOCATION], within the [DIVISION] Divisional Secretary's Division, [DISTRICT] District, [PROVINCE] Province, bounded on the:

NORTH by: [BOUNDARY]
EAST by: [BOUNDARY]
SOUTH by: [BOUNDARY]
WEST by: [BOUNDARY]

And containing in extent [EXTENT] (A[]-R[]-P[]) as per the said Plan.""",

            "gift_deed": """DEED OF GIFT (DONATION)

I, [DONOR NAME] (holder of National Identity Card No. [NIC]) of [ADDRESS] (hereinafter called the "DONOR") being the absolute owner of the land described in the Schedule hereto, out of natural love and affection which I bear towards [DONEE NAME] (holder of National Identity Card No. [NIC]) of [ADDRESS] (hereinafter called the "DONEE"), who is my [RELATIONSHIP], do hereby give, grant, donate and transfer unto the said DONEE ALL THAT the land and premises described in the Schedule hereto.

TO HAVE AND TO HOLD the same unto the said DONEE absolutely and forever.

AND I, the DONEE, do hereby accept this donation with gratitude.

SCHEDULE
[PROPERTY DESCRIPTION]""",

            "mortgage_bond": """MORTGAGE BOND

KNOW ALL MEN BY THESE PRESENTS that I, [MORTGAGOR NAME] (holder of National Identity Card No. [NIC]) of [ADDRESS] being indebted to [MORTGAGEE NAME/BANK] in the sum of Rupees [AMOUNT] lent and advanced to me, do hereby mortgage by way of PRIMARY MORTGAGE all that the land described in the Schedule hereto as security for repayment of the said sum together with interest at [RATE]% per annum.

COVENANTS:
1. To repay the principal sum with interest on [TERMS].
2. To pay all taxes and outgoings on the property.
3. Not to sell or encumber without mortgagee's consent.
4. To keep buildings in good repair and insured.

PROVIDED that upon repayment this mortgage shall become void.

SCHEDULE
[PROPERTY DESCRIPTION]""",

            "lease_deed": """DEED OF LEASE

THIS DEED OF LEASE made at [PLACE] on [DATE] BETWEEN [LESSOR NAME] of [ADDRESS] (the "LESSOR") AND [LESSEE NAME] of [ADDRESS] (the "LESSEE").

WITNESSETH:
1. The LESSOR leases unto the LESSEE the premises described in the Schedule for [TERM] years from [START DATE].
2. The LESSEE shall pay monthly rent of Rs. [AMOUNT] in advance.
3. The LESSEE shall use premises only for [PURPOSE].
4. The LESSEE shall not assign or sublet without consent.
5. The LESSEE shall maintain premises in good repair.
6. At termination, LESSEE shall surrender premises peacefully.

SCHEDULE
[PROPERTY DESCRIPTION]""",

            "last_will": """LAST WILL AND TESTAMENT

I, [TESTATOR NAME] (holder of National Identity Card No. [NIC]) of [ADDRESS], being of sound mind, do hereby make this my Last Will, revoking all former Wills.

1. I appoint [EXECUTOR NAME] as Executor of this Will.
2. I direct payment of all debts and funeral expenses.
3. I give, devise and bequeath my property as follows:
   (a) To [BENEFICIARY], I give [BEQUEST].
   (b) To [BENEFICIARY], I give [BEQUEST].

IN WITNESS WHEREOF I have signed this [DATE].

TESTATOR: ________________________

WITNESSES:
1. Name: _____________ Signature: _____________
2. Name: _____________ Signature: _____________"""
        }
        
        for template_id, content in templates.items():
            filepath = RAW_DIR / f"{template_id}_template.txt"
            filepath.write_text(content.strip(), encoding='utf-8')
        
        combined = "\n\n".join([f"{'='*60}\n{k.upper()}\n{'='*60}\n{v}" for k, v in templates.items()])
        (RAW_DIR / "deed_templates_combined.txt").write_text(combined, encoding='utf-8')
        
        print(f"  ✓ Created {len(templates)} deed templates")
        
        return {"id": "deed_templates", "title": "Sri Lankan Deed Templates", "template_count": len(templates)}

    def create_legal_principles(self) -> Dict:
        """Create a document of key legal principles."""
        
        principles = """# Key Legal Principles in Sri Lankan Property Law

## 1. Roman-Dutch Law Foundation
Sri Lankan property law is based on Roman-Dutch law from Dutch colonial rule (1658-1796):
- Dominium: absolute ownership concept
- Nemo plus juris transferre potest quam ipse habet (cannot transfer more rights than you have)
- Prior tempore potior jure (first in time, stronger in right)

## 2. Registration Systems

### Deeds Registration (Registration of Documents Ordinance)
- Registration provides notice, not guarantee of title
- Priority by date/time of registration
- Unregistered deeds valid between parties only

### Title Registration (Bim Saviya - Registration of Title Act 1998)
- State guarantees registered title
- Register is conclusive evidence
- First Class Title: absolute ownership
- Second Class Title: needs 10 years to convert

## 3. Prevention of Frauds Ordinance
All land transactions require:
- Written deed
- Notary attestation
- Two witnesses
- Applies to: sales, gifts, mortgages, leases over one month

## 4. Partition Act No. 21 of 1977
- Any co-owner can file partition action
- Court may order sale if property indivisible
- Decree is conclusive and binding
- Must be registered

## 5. Prescription Ordinance
Acquisitive prescription requires:
- 10 years adverse possession
- Nec vi (without force)
- Nec clam (without secrecy)
- Nec precario (without permission)

## 6. Mortgage Law
Types: Primary, Secondary, Parate execution (banks)
Mortgagee rights: Sue on covenant, foreclosure, sale, possession
Mortgagor rights: Redemption, surplus after sale

## 7. Rent Act Protection
Protected tenants have:
- Security of tenure
- Rent increase protection
- Ejectment only on specified grounds

## 8. State Land (Land Development Ordinance)
Alienation types: Absolute grant, conditional grant, permit, lease, license
Special succession rules apply

## 9. Foreign Ownership
Land (Restrictions on Alienation) Act:
- 100% tax on transfers to foreigners
- Condos above ground floor exempt
- BOI projects may have exemptions

## 10. Personal Laws
Kandyan Law: Applies to Kandyan Sinhalese, special inheritance rules
Thesawalamai: Applies to Jaffna Tamils, husband consent requirements
Muslim Law: Special inheritance and wakf provisions"""

        filepath = RAW_DIR / "legal_principles.txt"
        filepath.write_text(principles.strip(), encoding='utf-8')
        
        print(f"  ✓ Created legal principles document")
        return {"id": "legal_principles", "title": "Key Legal Principles"}

    def create_qa_training_data(self) -> Dict:
        """Create Q&A pairs for training."""
        
        qa_pairs = [
            {"q": "What is required for a valid transfer of land in Sri Lanka?",
             "a": "A valid transfer requires: (1) Written deed, (2) Notary attestation, (3) Two witnesses, (4) Registration at Land Registry, (5) Proper property description, (6) Competent parties."},
            {"q": "What is the difference between deeds registration and title registration?",
             "a": "Deeds registration only records transactions without guaranteeing title. Title registration (Bim Saviya) provides state-guaranteed title where the register is conclusive evidence of ownership."},
            {"q": "How can someone acquire title through prescription?",
             "a": "Under the Prescription Ordinance, 10 years of adverse possession can establish title. Possession must be nec vi (without force), nec clam (without secrecy), and nec precario (without permission)."},
            {"q": "What are the grounds for ejectment under the Rent Act?",
             "a": "Grounds include: non-payment of rent, breach of conditions, landlord's own occupation requirement, demolition/reconstruction, nuisance or illegal use, and premises vacant for 6+ months."},
            {"q": "What is parate execution in mortgage law?",
             "a": "Parate execution allows licensed banks to sell mortgaged property without court intervention when borrowers default, by public auction after proper notice."},
            {"q": "Can foreigners own land in Sri Lanka?",
             "a": "Foreigners face a 100% tax on land transfers (effectively prohibitive). However, they can own condominium units above ground floor, and BOI-approved projects may have exemptions."},
        ]
        
        json_path = PROCESSED_DIR / "qa_training_pairs.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(qa_pairs, f, indent=2, ensure_ascii=False)
        
        text_content = "# Sri Lankan Property Law Q&A\n\n"
        for i, qa in enumerate(qa_pairs, 1):
            text_content += f"Q{i}: {qa['q']}\nA{i}: {qa['a']}\n\n"
        
        (RAW_DIR / "qa_training_pairs.txt").write_text(text_content, encoding='utf-8')
        
        print(f"  ✓ Created {len(qa_pairs)} Q&A pairs")
        return {"id": "qa_training_pairs", "pair_count": len(qa_pairs)}

    def save_metadata(self):
        """Save metadata to JSON file."""
        self.metadata["stats"] = self.stats
        with open(METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)

    def download_all(self):
        """Download all property law data."""
        print("=" * 70)
        print("SRI LANKAN PROPERTY LAW DATA DOWNLOADER v2")
        print("=" * 70)
        print(f"Output: {OUTPUT_DIR.absolute()}")
        print("-" * 70)
        
        # 1. Download from SriLankaLaw.lk
        print("\n📚 Source 1: SriLankaLaw.lk - Statutory Laws")
        print("-" * 50)
        for key, info in self.PROPERTY_LAW_URLS.items():
            self.stats["total"] += 1
            doc_meta = self.download_from_srilankalaw(key, info)
            if doc_meta:
                self.metadata["documents"].append(doc_meta)
            time.sleep(2)
        
        # 2-5. Create compiled content
        for name, func in [
            ("📖 Legal Definitions", self.create_property_law_definitions),
            ("📝 Deed Templates", self.create_deed_templates),
            ("⚖️ Legal Principles", self.create_legal_principles),
            ("❓ Q&A Training Data", self.create_qa_training_data),
        ]:
            print(f"\n{name}")
            print("-" * 50)
            self.stats["total"] += 1
            self.metadata["documents"].append(func())
            self.stats["success"] += 1
        
        self.save_metadata()
        
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Total: {self.stats['total']} | Success: {self.stats['success']} | Failed: {self.stats['failed']}")
        print(f"Output: {OUTPUT_DIR.absolute()}")
        
        if self.stats['failed'] > 0:
            print("\n ⚠️  Some downloads failed. Check URLs at:")
            print("    https://www.srilankalaw.lk/revised-statutes/alphabetical-list-of-statutes.html")


if __name__ == "__main__":
    print("\n Sri Lankan Property Law Data Download v2\n")
    
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        os.system("pip install beautifulsoup4 -q")
        from bs4 import BeautifulSoup
    
    SriLankanLawDownloader().download_all()
    print("\n✅ Complete! Check ./data/sri_lankan_laws/")