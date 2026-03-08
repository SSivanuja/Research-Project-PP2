"""
Load Sri Lankan Property Law Data into Neo4j Knowledge Graph.
Adds statutes, sections, legal definitions, principles, and deed requirements.

This script creates the legal framework that governs property deeds in Sri Lanka,
enabling queries like "What law governs this deed?" and "Is this deed compliant?"

Usage:
    python load_srilankan_laws_to_neo4j.py

Requirements:
    pip install neo4j python-dotenv
"""

import os
import json
from datetime import datetime
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# Configuration
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASS = os.getenv("NEO4J_PASS")


class SriLankanLawLoader:
    """Load Sri Lankan property law data into Neo4j."""
    
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        self.stats = {
            "statutes": 0,
            "sections": 0,
            "definitions": 0,
            "principles": 0,
            "requirements": 0,
            "relationships": 0
        }
    
    def close(self):
        self.driver.close()
    
    # =========================================================================
    # SRI LANKAN PROPERTY LAW DATA
    # =========================================================================
    
    def get_statutes(self):
        """Sri Lankan statutes governing property law."""
        return [
            {
                "id": "STAT_001",
                "name": "Prevention of Frauds Ordinance",
                "short_name": "PFO",
                "act_number": "Ordinance No. 7 of 1840",
                "year": 1840,
                "category": "Property Transfer",
                "description": "Requires certain contracts and conveyances relating to land to be in writing and attested by a notary public.",
                "key_provisions": [
                    "All sales, purchases, transfers of land must be in writing",
                    "Must be signed by parties and attested by a notary",
                    "Notary must read and explain the document to parties",
                    "Two witnesses required for attestation"
                ],
                "applies_to": ["sale_transfer", "gift", "mortgage", "lease", "exchange"]
            },
            {
                "id": "STAT_002",
                "name": "Registration of Documents Ordinance",
                "short_name": "RDO",
                "act_number": "Ordinance No. 23 of 1927",
                "year": 1927,
                "category": "Registration",
                "description": "Provides for the registration of documents affecting land and establishes the system of land registration in Sri Lanka.",
                "key_provisions": [
                    "Documents must be registered within 3 months of execution",
                    "Registration at the Land Registry of the district where land is situated",
                    "Unregistered documents have no legal effect against third parties",
                    "Priority determined by date and time of registration"
                ],
                "applies_to": ["sale_transfer", "gift", "mortgage", "lease", "partition"]
            },
            {
                "id": "STAT_003",
                "name": "Registration of Title Act",
                "short_name": "RTA",
                "act_number": "Act No. 21 of 1998",
                "year": 1998,
                "category": "Title Registration",
                "description": "Establishes the Bim Saviya (Title Registration) system providing state-guaranteed title to land.",
                "key_provisions": [
                    "Title registered is conclusive evidence of ownership",
                    "State guarantees registered title",
                    "Gradual conversion from deed registration to title registration",
                    "Title certificate issued to registered owner"
                ],
                "applies_to": ["sale_transfer", "gift", "mortgage", "lease"]
            },
            {
                "id": "STAT_004",
                "name": "Prescription Ordinance",
                "short_name": "PO",
                "act_number": "Ordinance No. 22 of 1871",
                "year": 1871,
                "category": "Prescription",
                "description": "Governs acquisition of title by prescription (adverse possession) and limitation periods for legal actions.",
                "key_provisions": [
                    "10 years undisturbed possession for prescriptive title",
                    "Possession must be peaceful, uninterrupted, and adverse",
                    "Cannot prescribe against the state",
                    "Limitation periods for various legal actions"
                ],
                "applies_to": ["prescription", "adverse_possession"]
            },
            {
                "id": "STAT_005",
                "name": "Partition Act",
                "short_name": "PA",
                "act_number": "Act No. 21 of 1977",
                "year": 1977,
                "category": "Partition",
                "description": "Governs the partition of land held by co-owners and provides procedures for dividing common property.",
                "key_provisions": [
                    "Any co-owner can file partition action",
                    "Court determines shares based on title",
                    "Property divided physically or sold and proceeds divided",
                    "Partition decree is final and conclusive"
                ],
                "applies_to": ["partition"]
            },
            {
                "id": "STAT_006",
                "name": "Mortgage Act",
                "short_name": "MA",
                "act_number": "Act No. 6 of 1949",
                "year": 1949,
                "category": "Mortgage",
                "description": "Consolidates and amends the law relating to mortgages of immovable property.",
                "key_provisions": [
                    "Mortgage must be by notarial deed",
                    "Mortgagee has right to sell on default",
                    "Mortgagor retains right of redemption",
                    "Priority based on registration date"
                ],
                "applies_to": ["mortgage"]
            },
            {
                "id": "STAT_007",
                "name": "Recovery of Loans by Banks Act",
                "short_name": "RLBA",
                "act_number": "Act No. 4 of 1990",
                "year": 1990,
                "category": "Mortgage",
                "description": "Provides special procedures for banks to recover loans secured by mortgages.",
                "key_provisions": [
                    "Parate execution without court intervention",
                    "Board of Review for disputes",
                    "Special auction procedures",
                    "Applies to scheduled banks"
                ],
                "applies_to": ["mortgage", "bank_loan"]
            },
            {
                "id": "STAT_008",
                "name": "Rent Act",
                "short_name": "RA",
                "act_number": "Act No. 7 of 1972",
                "year": 1972,
                "category": "Tenancy",
                "description": "Provides for the control of rent of residential and business premises and protection of tenants.",
                "key_provisions": [
                    "Rent control for covered premises",
                    "Security of tenure for tenants",
                    "Landlord requires court order for eviction",
                    "Prescribed grounds for eviction"
                ],
                "applies_to": ["lease", "tenancy"]
            },
            {
                "id": "STAT_009",
                "name": "Land Development Ordinance",
                "short_name": "LDO",
                "act_number": "Ordinance No. 19 of 1935",
                "year": 1935,
                "category": "State Land",
                "description": "Governs the alienation and development of state land.",
                "key_provisions": [
                    "State land granted under permits or grants",
                    "Conditions attached to grants",
                    "Restrictions on alienation without approval",
                    "Land can revert to state on breach"
                ],
                "applies_to": ["state_land", "grant"]
            },
            {
                "id": "STAT_010",
                "name": "State Lands Ordinance",
                "short_name": "SLO",
                "act_number": "Ordinance No. 8 of 1947",
                "year": 1947,
                "category": "State Land",
                "description": "Governs the administration, management, and disposal of state land.",
                "key_provisions": [
                    "All land is presumed state land unless proven otherwise",
                    "Encroachment on state land is illegal",
                    "State can grant, lease, or sell state land",
                    "Special procedures for disposal"
                ],
                "applies_to": ["state_land"]
            },
            {
                "id": "STAT_011",
                "name": "Land (Restrictions on Alienation) Act",
                "short_name": "LRAA",
                "act_number": "Act No. 38 of 2014",
                "year": 2014,
                "category": "Foreign Ownership",
                "description": "Restricts ownership of land by foreigners and foreign-owned companies.",
                "key_provisions": [
                    "Foreigners cannot own freehold land",
                    "99-year lease maximum for foreigners",
                    "Companies with >50% foreign ownership restricted",
                    "Exemptions for BOI projects"
                ],
                "applies_to": ["foreign_ownership", "sale_transfer"]
            },
            {
                "id": "STAT_012",
                "name": "Notaries Ordinance",
                "short_name": "NO",
                "act_number": "Ordinance No. 1 of 1907",
                "year": 1907,
                "category": "Attestation",
                "description": "Governs the appointment, duties, and functions of notaries public.",
                "key_provisions": [
                    "Notary must be enrolled and licensed",
                    "Must read and explain deed to parties",
                    "Must verify identity of parties",
                    "Must maintain protocol (deed register)"
                ],
                "applies_to": ["all_deeds"]
            },
            {
                "id": "STAT_013",
                "name": "Stamp Duty Act",
                "short_name": "SDA",
                "act_number": "Act No. 43 of 1982",
                "year": 1982,
                "category": "Taxation",
                "description": "Imposes stamp duty on instruments and documents.",
                "key_provisions": [
                    "Stamp duty payable on conveyances",
                    "Rate depends on value and type of transaction",
                    "Unstamped documents not admissible as evidence",
                    "Exemptions for certain transactions"
                ],
                "applies_to": ["sale_transfer", "gift", "mortgage", "lease"]
            },
            {
                "id": "STAT_014",
                "name": "Wills Ordinance",
                "short_name": "WO",
                "act_number": "Ordinance No. 7 of 1840 (Part)",
                "year": 1840,
                "category": "Succession",
                "description": "Governs the making and validity of wills.",
                "key_provisions": [
                    "Will must be in writing",
                    "Signed by testator or marked",
                    "Attested by two witnesses",
                    "Testator must have testamentary capacity"
                ],
                "applies_to": ["will"]
            },
            {
                "id": "STAT_015",
                "name": "Intestate Succession Ordinance",
                "short_name": "ISO",
                "act_number": "Ordinance No. 12 of 1944",
                "year": 1944,
                "category": "Succession",
                "description": "Governs succession to property when a person dies without a valid will.",
                "key_provisions": [
                    "Spouse and children inherit first",
                    "Parents inherit if no spouse/children",
                    "Siblings inherit if no spouse/children/parents",
                    "Different rules for different communities"
                ],
                "applies_to": ["succession", "will"]
            }
        ]
    
    def get_sections(self):
        """Key sections from the statutes."""
        return [
            # Prevention of Frauds Ordinance
            {
                "id": "SEC_PFO_2",
                "statute_id": "STAT_001",
                "section_number": "Section 2",
                "title": "Contracts for Sale of Land",
                "content": "No action shall be brought upon any contract for the sale of lands unless the agreement or some memorandum or note thereof shall be in writing and signed by the party to be charged.",
                "importance": "critical"
            },
            {
                "id": "SEC_PFO_3",
                "statute_id": "STAT_001",
                "section_number": "Section 3",
                "title": "Leases Must Be in Writing",
                "content": "No lease of lands for any term exceeding one month shall be valid unless the same shall be in writing signed by the lessor.",
                "importance": "critical"
            },
            {
                "id": "SEC_PFO_4",
                "statute_id": "STAT_001",
                "section_number": "Section 4",
                "title": "Transfer of Land Must Be Notarized",
                "content": "No sale, purchase, transfer, assignment, or mortgage of land shall be valid unless the same shall be in writing and signed and attested by a notary public.",
                "importance": "critical"
            },
            # Registration of Documents Ordinance
            {
                "id": "SEC_RDO_17",
                "statute_id": "STAT_002",
                "section_number": "Section 17",
                "title": "Documents Required to be Registered",
                "content": "All notarially executed documents affecting land must be registered at the Land Registry within three months of execution.",
                "importance": "critical"
            },
            {
                "id": "SEC_RDO_22",
                "statute_id": "STAT_002",
                "section_number": "Section 22",
                "title": "Effect of Non-Registration",
                "content": "An unregistered document shall not affect any person who has not signed the same and shall not confer any priority.",
                "importance": "critical"
            },
            # Prescription Ordinance
            {
                "id": "SEC_PO_3",
                "statute_id": "STAT_004",
                "section_number": "Section 3",
                "title": "Acquisition by Prescription",
                "content": "Proof of undisturbed and uninterrupted possession by a defendant for ten years previous to the bringing of such action shall entitle the defendant to a decree in his favor.",
                "importance": "critical"
            },
            # Partition Act
            {
                "id": "SEC_PA_2",
                "statute_id": "STAT_005",
                "section_number": "Section 2",
                "title": "Right to Partition",
                "content": "Any co-owner of land may institute an action for the partition of such land.",
                "importance": "high"
            },
            # Mortgage Act
            {
                "id": "SEC_MA_6",
                "statute_id": "STAT_006",
                "section_number": "Section 6",
                "title": "Form of Mortgage",
                "content": "Every mortgage of immovable property shall be effected by a notarially executed deed.",
                "importance": "critical"
            },
            {
                "id": "SEC_MA_11",
                "statute_id": "STAT_006",
                "section_number": "Section 11",
                "title": "Right of Redemption",
                "content": "The mortgagor shall have the right to redeem the mortgaged property at any time before sale.",
                "importance": "high"
            },
            # Notaries Ordinance
            {
                "id": "SEC_NO_31",
                "statute_id": "STAT_012",
                "section_number": "Section 31",
                "title": "Duty to Read and Explain",
                "content": "The notary shall read over and explain the contents of the deed to the parties before attestation.",
                "importance": "critical"
            },
            {
                "id": "SEC_NO_32",
                "statute_id": "STAT_012",
                "section_number": "Section 32",
                "title": "Identification of Parties",
                "content": "The notary shall satisfy himself as to the identity of the parties to the deed.",
                "importance": "critical"
            }
        ]
    
    def get_legal_definitions(self):
        """Sri Lankan property law definitions."""
        return [
            {
                "id": "DEF_001",
                "term": "Immovable Property",
                "definition": "Land, benefits arising out of land, and things attached to the earth or permanently fastened to anything attached to the earth.",
                "source": "Roman-Dutch Law"
            },
            {
                "id": "DEF_002",
                "term": "Conveyance",
                "definition": "A transfer of ownership of immovable property from one person to another by means of a written instrument.",
                "source": "Prevention of Frauds Ordinance"
            },
            {
                "id": "DEF_003",
                "term": "Vendor",
                "definition": "The person who sells or transfers property; also known as the transferor.",
                "source": "Common Legal Usage"
            },
            {
                "id": "DEF_004",
                "term": "Vendee",
                "definition": "The person who purchases or receives property; also known as the transferee or purchaser.",
                "source": "Common Legal Usage"
            },
            {
                "id": "DEF_005",
                "term": "Notary Public",
                "definition": "A legally authorized officer who attests and certifies deeds, contracts, and other legal documents.",
                "source": "Notaries Ordinance"
            },
            {
                "id": "DEF_006",
                "term": "Attestation",
                "definition": "The act of witnessing the execution of a document and signing it as a witness to confirm its authenticity.",
                "source": "Prevention of Frauds Ordinance"
            },
            {
                "id": "DEF_007",
                "term": "Prescription",
                "definition": "The acquisition of title to property through continuous, uninterrupted, and adverse possession for a statutory period (10 years in Sri Lanka).",
                "source": "Prescription Ordinance"
            },
            {
                "id": "DEF_008",
                "term": "Mortgage",
                "definition": "A transfer of an interest in immovable property as security for a debt, with the right of redemption upon payment.",
                "source": "Mortgage Act"
            },
            {
                "id": "DEF_009",
                "term": "Lease",
                "definition": "A contract by which one party (lessor) grants to another (lessee) the right to use immovable property for a specified period in exchange for rent.",
                "source": "Prevention of Frauds Ordinance"
            },
            {
                "id": "DEF_010",
                "term": "Partition",
                "definition": "The division of property held by co-owners into separate portions, with each owner receiving exclusive ownership of their portion.",
                "source": "Partition Act"
            },
            {
                "id": "DEF_011",
                "term": "Gift Inter Vivos",
                "definition": "A gift made during the lifetime of the donor, transferring ownership immediately without consideration.",
                "source": "Roman-Dutch Law"
            },
            {
                "id": "DEF_012",
                "term": "Testator",
                "definition": "A person who makes a will; the person whose property is disposed of by will after death.",
                "source": "Wills Ordinance"
            },
            {
                "id": "DEF_013",
                "term": "Encumbrance",
                "definition": "A claim, lien, charge, or liability attached to property that may diminish its value or restrict its transfer.",
                "source": "Common Legal Usage"
            },
            {
                "id": "DEF_014",
                "term": "Survey Plan",
                "definition": "A plan prepared by a licensed surveyor showing the boundaries, extent, and location of a land parcel.",
                "source": "Survey Act"
            },
            {
                "id": "DEF_015",
                "term": "Folio",
                "definition": "The volume and page reference in the Land Registry where a deed is registered.",
                "source": "Registration of Documents Ordinance"
            },
            {
                "id": "DEF_016",
                "term": "Consideration",
                "definition": "The value given in exchange for property; typically money in a sale transaction.",
                "source": "Contract Law"
            },
            {
                "id": "DEF_017",
                "term": "Easement",
                "definition": "A right to use another's land for a specific purpose, such as a right of way.",
                "source": "Roman-Dutch Law"
            },
            {
                "id": "DEF_018",
                "term": "Servitude",
                "definition": "A burden imposed on one property (servient tenement) for the benefit of another property (dominant tenement).",
                "source": "Roman-Dutch Law"
            },
            {
                "id": "DEF_019",
                "term": "Co-ownership",
                "definition": "Ownership of property by two or more persons simultaneously, each having an undivided share.",
                "source": "Roman-Dutch Law"
            },
            {
                "id": "DEF_020",
                "term": "Bim Saviya",
                "definition": "The title registration system in Sri Lanka that provides state-guaranteed title to land under the Registration of Title Act.",
                "source": "Registration of Title Act"
            }
        ]
    
    def get_legal_principles(self):
        """Key legal principles in Sri Lankan property law."""
        return [
            {
                "id": "PRIN_001",
                "name": "Nemo Dat Quod Non Habet",
                "english": "No one can give what they do not have",
                "description": "A person cannot transfer better title than they possess. A purchaser cannot acquire ownership if the seller does not have valid title.",
                "application": "Essential for validating chain of title in property transfers."
            },
            {
                "id": "PRIN_002",
                "name": "Caveat Emptor",
                "english": "Let the buyer beware",
                "description": "The buyer is responsible for verifying title and condition of property before purchase. The seller has no duty to disclose defects.",
                "application": "Emphasizes importance of title search before purchase."
            },
            {
                "id": "PRIN_003",
                "name": "Prior Tempore Potior Jure",
                "english": "First in time, stronger in right",
                "description": "Between competing claims to the same property, the one registered first has priority.",
                "application": "Determines priority of mortgages and other encumbrances."
            },
            {
                "id": "PRIN_004",
                "name": "Accessio Cedit Principali",
                "english": "The accessory follows the principal",
                "description": "Things attached to land become part of the land and pass with ownership of the land.",
                "application": "Determines ownership of buildings, trees, and fixtures."
            },
            {
                "id": "PRIN_005",
                "name": "Superficies Solo Cedit",
                "english": "Whatever is attached to the soil belongs to the soil",
                "description": "Buildings and permanent structures become part of the land and belong to the landowner.",
                "application": "Important in determining ownership of improvements."
            },
            {
                "id": "PRIN_006",
                "name": "Possession is Nine-Tenths of the Law",
                "english": "Possession creates presumption of ownership",
                "description": "A person in possession of land is presumed to be the owner unless proven otherwise.",
                "application": "Important in prescription and adverse possession claims."
            },
            {
                "id": "PRIN_007",
                "name": "Equity of Redemption",
                "english": "Right to redeem mortgaged property",
                "description": "A mortgagor has the right to redeem the property by paying the debt at any time before sale.",
                "application": "Protects mortgagor's interest in mortgaged property."
            },
            {
                "id": "PRIN_008",
                "name": "Registration Provides Constructive Notice",
                "english": "Registration gives notice to the world",
                "description": "Once a document is registered, all persons are deemed to have notice of its contents.",
                "application": "Protects registered rights against subsequent claims."
            },
            {
                "id": "PRIN_009",
                "name": "State is the Ultimate Owner",
                "english": "All land vests in the State",
                "description": "All land in Sri Lanka is presumed to belong to the State unless private ownership is proven.",
                "application": "Important in proving title against State claims."
            },
            {
                "id": "PRIN_010",
                "name": "Once a Mortgage, Always a Mortgage",
                "english": "Mortgage cannot be converted to absolute transfer",
                "description": "Any agreement that extinguishes the mortgagor's right of redemption is void.",
                "application": "Protects mortgagor from losing property through unfair terms."
            }
        ]
    
    def get_deed_requirements(self):
        """Legal requirements for different deed types."""
        return [
            {
                "id": "REQ_SALE",
                "deed_type": "sale_transfer",
                "name": "Sale/Transfer Deed Requirements",
                "requirements": [
                    {"item": "Written document", "statute": "STAT_001", "mandatory": True},
                    {"item": "Notarially attested", "statute": "STAT_001", "mandatory": True},
                    {"item": "Two witnesses", "statute": "STAT_001", "mandatory": True},
                    {"item": "Parties identified by NIC", "statute": "STAT_012", "mandatory": True},
                    {"item": "Property clearly described", "statute": "STAT_002", "mandatory": True},
                    {"item": "Survey plan referenced", "statute": "STAT_002", "mandatory": False},
                    {"item": "Consideration stated", "statute": "STAT_013", "mandatory": True},
                    {"item": "Stamp duty paid", "statute": "STAT_013", "mandatory": True},
                    {"item": "Registered within 3 months", "statute": "STAT_002", "mandatory": True}
                ],
                "stamp_duty": "3% of consideration or market value",
                "registration_fee": "Based on consideration value"
            },
            {
                "id": "REQ_GIFT",
                "deed_type": "gift",
                "name": "Gift Deed Requirements",
                "requirements": [
                    {"item": "Written document", "statute": "STAT_001", "mandatory": True},
                    {"item": "Notarially attested", "statute": "STAT_001", "mandatory": True},
                    {"item": "Two witnesses", "statute": "STAT_001", "mandatory": True},
                    {"item": "Donor and donee identified", "statute": "STAT_012", "mandatory": True},
                    {"item": "Property clearly described", "statute": "STAT_002", "mandatory": True},
                    {"item": "Acceptance by donee", "statute": "STAT_001", "mandatory": True},
                    {"item": "Registered within 3 months", "statute": "STAT_002", "mandatory": True}
                ],
                "stamp_duty": "3% of market value (may be exempt for close relatives)",
                "registration_fee": "Based on market value"
            },
            {
                "id": "REQ_MORTGAGE",
                "deed_type": "mortgage",
                "name": "Mortgage Deed Requirements",
                "requirements": [
                    {"item": "Written document", "statute": "STAT_006", "mandatory": True},
                    {"item": "Notarially attested", "statute": "STAT_006", "mandatory": True},
                    {"item": "Two witnesses", "statute": "STAT_001", "mandatory": True},
                    {"item": "Loan amount stated", "statute": "STAT_006", "mandatory": True},
                    {"item": "Interest rate specified", "statute": "STAT_006", "mandatory": True},
                    {"item": "Property clearly described", "statute": "STAT_006", "mandatory": True},
                    {"item": "Registered within 3 months", "statute": "STAT_002", "mandatory": True}
                ],
                "stamp_duty": "0.25% of loan amount",
                "registration_fee": "Based on loan amount"
            },
            {
                "id": "REQ_LEASE",
                "deed_type": "lease",
                "name": "Lease Deed Requirements",
                "requirements": [
                    {"item": "Written document (if > 1 month)", "statute": "STAT_001", "mandatory": True},
                    {"item": "Notarially attested (if > 1 year)", "statute": "STAT_001", "mandatory": True},
                    {"item": "Lease period stated", "statute": "STAT_001", "mandatory": True},
                    {"item": "Rent amount specified", "statute": "STAT_001", "mandatory": True},
                    {"item": "Property clearly described", "statute": "STAT_002", "mandatory": True},
                    {"item": "Registered (if > 1 year)", "statute": "STAT_002", "mandatory": True}
                ],
                "stamp_duty": "1% of total rent for lease period",
                "registration_fee": "Based on annual rent"
            },
            {
                "id": "REQ_WILL",
                "deed_type": "will",
                "name": "Will/Testament Requirements",
                "requirements": [
                    {"item": "Written document", "statute": "STAT_014", "mandatory": True},
                    {"item": "Signed by testator", "statute": "STAT_014", "mandatory": True},
                    {"item": "Two witnesses present", "statute": "STAT_014", "mandatory": True},
                    {"item": "Witnesses must sign", "statute": "STAT_014", "mandatory": True},
                    {"item": "Testator of sound mind", "statute": "STAT_014", "mandatory": True},
                    {"item": "Testator above 21 years", "statute": "STAT_014", "mandatory": True}
                ],
                "stamp_duty": "Not applicable",
                "registration_fee": "Optional registration"
            },
            {
                "id": "REQ_PARTITION",
                "deed_type": "partition",
                "name": "Partition Requirements",
                "requirements": [
                    {"item": "Court action filed", "statute": "STAT_005", "mandatory": True},
                    {"item": "All co-owners made parties", "statute": "STAT_005", "mandatory": True},
                    {"item": "Title established", "statute": "STAT_005", "mandatory": True},
                    {"item": "Survey plan prepared", "statute": "STAT_005", "mandatory": True},
                    {"item": "Court decree obtained", "statute": "STAT_005", "mandatory": True}
                ],
                "stamp_duty": "Court fees applicable",
                "registration_fee": "Decree must be registered"
            }
        ]
    
    # =========================================================================
    # NEO4J LOADING METHODS
    # =========================================================================
    
    def create_constraints(self):
        """Create uniqueness constraints for legal nodes."""
        constraints = [
            "CREATE CONSTRAINT statute_id IF NOT EXISTS FOR (s:Statute) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT section_id IF NOT EXISTS FOR (s:Section) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT definition_id IF NOT EXISTS FOR (d:LegalDefinition) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT principle_id IF NOT EXISTS FOR (p:LegalPrinciple) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT requirement_id IF NOT EXISTS FOR (r:DeedRequirement) REQUIRE r.id IS UNIQUE",
        ]
        
        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    # Constraint may already exist
                    pass
        
        print("✓ Constraints created")
    
    def load_statutes(self):
        """Load statutes into Neo4j."""
        statutes = self.get_statutes()
        
        query = """
        UNWIND $statutes AS s
        MERGE (stat:Statute {id: s.id})
        SET stat.name = s.name,
            stat.short_name = s.short_name,
            stat.act_number = s.act_number,
            stat.year = s.year,
            stat.category = s.category,
            stat.description = s.description,
            stat.key_provisions = s.key_provisions,
            stat.applies_to = s.applies_to,
            stat.loaded_at = datetime()
        RETURN count(stat) AS count
        """
        
        with self.driver.session() as session:
            result = session.run(query, statutes=statutes)
            count = result.single()["count"]
            self.stats["statutes"] = count
            print(f"✓ Loaded {count} statutes")
    
    def load_sections(self):
        """Load statute sections into Neo4j."""
        sections = self.get_sections()
        
        query = """
        UNWIND $sections AS sec
        MERGE (s:Section {id: sec.id})
        SET s.section_number = sec.section_number,
            s.title = sec.title,
            s.content = sec.content,
            s.importance = sec.importance,
            s.loaded_at = datetime()
        WITH s, sec
        MATCH (stat:Statute {id: sec.statute_id})
        MERGE (s)-[:PART_OF]->(stat)
        RETURN count(s) AS count
        """
        
        with self.driver.session() as session:
            result = session.run(query, sections=sections)
            count = result.single()["count"]
            self.stats["sections"] = count
            print(f"✓ Loaded {count} sections")
    
    def load_definitions(self):
        """Load legal definitions into Neo4j."""
        definitions = self.get_legal_definitions()
        
        query = """
        UNWIND $definitions AS def
        MERGE (d:LegalDefinition {id: def.id})
        SET d.term = def.term,
            d.definition = def.definition,
            d.source = def.source,
            d.loaded_at = datetime()
        RETURN count(d) AS count
        """
        
        with self.driver.session() as session:
            result = session.run(query, definitions=definitions)
            count = result.single()["count"]
            self.stats["definitions"] = count
            print(f"✓ Loaded {count} legal definitions")
    
    def load_principles(self):
        """Load legal principles into Neo4j."""
        principles = self.get_legal_principles()
        
        query = """
        UNWIND $principles AS prin
        MERGE (p:LegalPrinciple {id: prin.id})
        SET p.name = prin.name,
            p.english = prin.english,
            p.description = prin.description,
            p.application = prin.application,
            p.loaded_at = datetime()
        RETURN count(p) AS count
        """
        
        with self.driver.session() as session:
            result = session.run(query, principles=principles)
            count = result.single()["count"]
            self.stats["principles"] = count
            print(f"✓ Loaded {count} legal principles")
    
    def load_deed_requirements(self):
        """Load deed requirements into Neo4j."""
        requirements = self.get_deed_requirements()
        
        query = """
        UNWIND $requirements AS req
        MERGE (r:DeedRequirement {id: req.id})
        SET r.deed_type = req.deed_type,
            r.name = req.name,
            r.requirements = [item IN req.requirements | item.item],
            r.stamp_duty = req.stamp_duty,
            r.registration_fee = req.registration_fee,
            r.loaded_at = datetime()
        RETURN count(r) AS count
        """
        
        with self.driver.session() as session:
            result = session.run(query, requirements=requirements)
            count = result.single()["count"]
            self.stats["requirements"] = count
            print(f"✓ Loaded {count} deed requirement sets")
    
    def create_deed_statute_relationships(self):
        """Create relationships between deed types and governing statutes."""
        # Link deed requirements to statutes
        query1 = """
        MATCH (r:DeedRequirement)
        MATCH (s:Statute)
        WHERE r.deed_type IN s.applies_to
        MERGE (r)-[:GOVERNED_BY]->(s)
        RETURN count(*) AS count
        """
        
        # Link existing Instruments to statutes based on type
        query2 = """
        MATCH (i:Instrument)
        MATCH (s:Statute)
        WHERE i.type IN s.applies_to
        MERGE (i)-[:GOVERNED_BY]->(s)
        RETURN count(*) AS count
        """
        
        # Link Instruments to DeedRequirements
        query3 = """
        MATCH (i:Instrument)
        MATCH (r:DeedRequirement)
        WHERE i.type = r.deed_type
        MERGE (i)-[:MUST_COMPLY_WITH]->(r)
        RETURN count(*) AS count
        """
        
        with self.driver.session() as session:
            r1 = session.run(query1).single()["count"]
            r2 = session.run(query2).single()["count"]
            r3 = session.run(query3).single()["count"]
            
            total = r1 + r2 + r3
            self.stats["relationships"] = total
            print(f"✓ Created {total} legal relationships")
            print(f"  - Requirement → Statute: {r1}")
            print(f"  - Instrument → Statute: {r2}")
            print(f"  - Instrument → Requirement: {r3}")
    
    def create_indexes(self):
        """Create indexes for efficient querying."""
        indexes = [
            "CREATE INDEX statute_name IF NOT EXISTS FOR (s:Statute) ON (s.name)",
            "CREATE INDEX statute_category IF NOT EXISTS FOR (s:Statute) ON (s.category)",
            "CREATE INDEX definition_term IF NOT EXISTS FOR (d:LegalDefinition) ON (d.term)",
            "CREATE INDEX principle_name IF NOT EXISTS FOR (p:LegalPrinciple) ON (p.name)",
            "CREATE INDEX requirement_type IF NOT EXISTS FOR (r:DeedRequirement) ON (r.deed_type)",
        ]
        
        with self.driver.session() as session:
            for index in indexes:
                try:
                    session.run(index)
                except Exception as e:
                    pass
        
        print("✓ Indexes created")
    
    def load_all(self):
        """Load all legal data into Neo4j."""
        print("=" * 80)
        print("LOADING SRI LANKAN PROPERTY LAW INTO NEO4J")
        print("=" * 80)
        print(f"Database: {NEO4J_URI}")
        print("-" * 80)
        
        self.create_constraints()
        self.load_statutes()
        self.load_sections()
        self.load_definitions()
        self.load_principles()
        self.load_deed_requirements()
        self.create_deed_statute_relationships()
        self.create_indexes()
        
        print("\n" + "=" * 80)
        print("LOADING COMPLETE")
        print("=" * 80)
        print(f"Statutes:      {self.stats['statutes']}")
        print(f"Sections:      {self.stats['sections']}")
        print(f"Definitions:   {self.stats['definitions']}")
        print(f"Principles:    {self.stats['principles']}")
        print(f"Requirements:  {self.stats['requirements']}")
        print(f"Relationships: {self.stats['relationships']}")
        
        # Save stats
        stats_file = "law_loading_stats.json"
        with open(stats_file, 'w') as f:
            json.dump({
                "loaded_at": datetime.now().isoformat(),
                "stats": self.stats
            }, f, indent=2)
        print(f"\n✓ Stats saved to: {stats_file}")


def main():
    print("\n" + "=" * 80)
    print("  SRI LANKAN PROPERTY LAW LOADER")
    print("  Loads statutes, sections, definitions, and principles into Neo4j")
    print("=" * 80 + "\n")
    
    if not NEO4J_PASS:
        print("❌ NEO4J_PASS environment variable not set!")
        print("Set it in .env file or export NEO4J_PASS=your_password")
        return
    
    loader = SriLankanLawLoader()
    
    try:
        loader.load_all()
        
        print("\n" + "=" * 80)
        print("SAMPLE QUERIES YOU CAN NOW RUN")
        print("=" * 80)
        print("""
// Find statutes governing sale deeds
MATCH (s:Statute)
WHERE 'sale_transfer' IN s.applies_to
RETURN s.name, s.description

// Get requirements for a gift deed
MATCH (r:DeedRequirement {deed_type: 'gift'})
RETURN r.name, r.requirements

// Find what law a specific deed must comply with
MATCH (i:Instrument {type: 'sale_transfer'})-[:GOVERNED_BY]->(s:Statute)
RETURN i.code_number, s.name, s.act_number

// Get legal definition of a term
MATCH (d:LegalDefinition)
WHERE toLower(d.term) CONTAINS 'mortgage'
RETURN d.term, d.definition

// Find key sections of Prevention of Frauds Ordinance
MATCH (sec:Section)-[:PART_OF]->(s:Statute {short_name: 'PFO'})
RETURN sec.section_number, sec.title, sec.content
        """)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        loader.close()


if __name__ == "__main__":
    main()
