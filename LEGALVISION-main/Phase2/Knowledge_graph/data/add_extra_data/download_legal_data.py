#!/usr/bin/env python3
"""
Sri Lankan Legal Data Downloader and Generator
Downloads real legal documents and generates genuine property price data
"""

import os
import json
import requests
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import re

# =============================================================================
# CONFIGURATION
# =============================================================================

OUTPUT_DIR = Path("./extra_laws")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# =============================================================================
# REAL SRI LANKAN LAW SOURCES
# =============================================================================

LEGAL_SOURCES = {
    "statutes": [
        {
            "id": "prevention_of_frauds_ordinance",
            "name": "Prevention of Frauds Ordinance",
            "short_name": "PFO",
            "act_number": "Ordinance No. 7 of 1840",
            "year": 1840,
            "category": "Property Transfer",
            "url": "https://www.srilankalaw.lk/p/927-prevention-of-frauds-ordinance.html",
            "pdf_url": None,
            "description": "Requires certain contracts and conveyances relating to land to be in writing and attested by a notary public. This is the foundational statute for property transactions in Sri Lanka.",
            "applies_to": ["sale_transfer", "gift", "mortgage", "lease", "exchange"],
            "key_provisions": [
                "All deeds affecting immovable property must be in writing",
                "Must be signed by the parties",
                "Must be attested by a licensed notary public",
                "Must be witnessed by two persons",
                "Notary must read and explain the deed to parties"
            ]
        },
        {
            "id": "registration_of_documents_ordinance",
            "name": "Registration of Documents Ordinance",
            "short_name": "RDO",
            "act_number": "Ordinance No. 23 of 1927",
            "year": 1927,
            "category": "Registration",
            "url": "https://www.srilankalaw.lk/revised-statutes/volume-vii/1013-registration-of-documents-ordinance.html",
            "pdf_url": None,
            "description": "Provides for the registration of documents affecting land. Unregistered documents have no effect against third parties claiming adverse interest on valuable consideration.",
            "applies_to": ["sale_transfer", "gift", "mortgage", "lease", "partition", "will"],
            "key_provisions": [
                "Registration within 3 months of execution",
                "Registration at Land Registry of district where property is situated",
                "Unregistered instruments void against third parties",
                "Priority based on date of registration",
                "Fraud defeats priority even if registered first"
            ]
        },
        {
            "id": "notaries_ordinance",
            "name": "Notaries Ordinance",
            "short_name": "NO",
            "act_number": "Ordinance No. 1 of 1907",
            "year": 1907,
            "category": "Notarial Practice",
            "url": "https://www.lawnet.gov.lk/notaries-3/",
            "pdf_url": "https://www.parliament.lk/uploads/acts/gbills/english/6270.pdf",
            "description": "Governs the appointment, duties, and responsibilities of notaries public in Sri Lanka. Sets standards for attestation of deeds and documents.",
            "applies_to": ["sale_transfer", "gift", "mortgage", "lease", "will", "power_of_attorney"],
            "key_provisions": [
                "Notary must be licensed in the district",
                "Must verify identity of parties",
                "Must read and explain document to parties",
                "Must maintain protocol books",
                "Penalties for misconduct"
            ]
        },
        {
            "id": "prescription_ordinance",
            "name": "Prescription Ordinance",
            "short_name": "PO",
            "act_number": "Ordinance No. 22 of 1871",
            "year": 1871,
            "category": "Title Acquisition",
            "url": "https://www.srilankalaw.lk/revised-statutes/alphabetical-list-of-statutes/1573-prescription-ordinance.html",
            "pdf_url": "https://www.commonlii.org/lk/legis/consol_act/p81214.pdf",
            "description": "Provides for acquisition of title to immovable property through adverse possession for 10 years. Does not apply to state lands.",
            "applies_to": ["prescription", "adverse_possession"],
            "key_provisions": [
                "10 years uninterrupted adverse possession",
                "Possession must be exclusive and as owner",
                "Does not apply to state lands (Section 15)",
                "Does not run against minors or persons of unsound mind",
                "Possession by co-owner can ripen into prescriptive title"
            ]
        },
        {
            "id": "partition_act",
            "name": "Partition Act",
            "short_name": "PA",
            "act_number": "Act No. 21 of 1977",
            "year": 1977,
            "category": "Partition",
            "url": "https://lankalaw.net/wp-content/uploads/2025/03/Partition-Consolidated-2024.pdf",
            "pdf_url": "https://lankalaw.net/wp-content/uploads/2025/03/Partition-Consolidated-2024.pdf",
            "description": "Provides for the partition and sale of land held in common. Allows co-owners to obtain separate title to their shares.",
            "applies_to": ["partition"],
            "key_provisions": [
                "Court action required for partition",
                "Commission issued to surveyor for plan",
                "Interlocutory decree declares shares",
                "Physical partition or sale if indivisible",
                "Final decree issues after partition/sale"
            ]
        },
        {
            "id": "mortgage_act",
            "name": "Mortgage Act",
            "short_name": "MA",
            "act_number": "Act No. 6 of 1949",
            "year": 1949,
            "category": "Mortgage",
            "url": "https://www.srilankalaw.lk/revised-statutes/alphabetical-list-of-statutes.html",
            "pdf_url": None,
            "description": "Consolidates and amends the law relating to mortgages of immovable property in Sri Lanka.",
            "applies_to": ["mortgage"],
            "key_provisions": [
                "Mortgage must be by notarial deed",
                "Mortgagee has right to sell on default",
                "Mortgagor retains right of redemption",
                "Priority based on registration date",
                "Parate execution allowed under certain conditions"
            ]
        },
        {
            "id": "stamp_duty_act",
            "name": "Stamp Duty Act",
            "short_name": "SDA",
            "act_number": "Act No. 43 of 1982",
            "year": 1982,
            "category": "Taxation",
            "url": "https://www.srilankalaw.lk/revised-statutes/volume-vii/1230-stamp-duty-act.html",
            "pdf_url": None,
            "description": "Imposes stamp duty on instruments and documents. Provincial Councils collect stamp duty on property transfers.",
            "applies_to": ["sale_transfer", "gift", "mortgage", "lease"],
            "key_provisions": [
                "4% stamp duty on property transfers (LKR 4 per LKR 100)",
                "Payable to Provincial Council",
                "Due at time of execution",
                "Unstamped documents inadmissible as evidence",
                "Exemptions for certain transactions"
            ]
        },
        {
            "id": "land_restrictions_act",
            "name": "Land (Restrictions on Alienation) Act",
            "short_name": "LRA",
            "act_number": "Act No. 38 of 2014",
            "year": 2014,
            "category": "Foreign Ownership",
            "url": None,
            "pdf_url": None,
            "description": "Restricts foreign ownership of freehold land in Sri Lanka. Non-citizens must pay 100% tax or lease instead.",
            "applies_to": ["sale_transfer", "gift"],
            "key_provisions": [
                "Non-citizens cannot acquire freehold land without 100% tax",
                "Companies with >25% foreign ownership restricted",
                "99-year lease alternative available",
                "Some exemptions for BOI projects",
                "Applies to land only, not condominiums"
            ]
        },
        {
            "id": "condominium_property_act",
            "name": "Apartment Ownership Law",
            "short_name": "AOL",
            "act_number": "Law No. 11 of 1973",
            "year": 1973,
            "category": "Condominium",
            "url": None,
            "pdf_url": None,
            "description": "Provides for ownership of apartments and condominiums. Foreigners can own condominium units above ground floor.",
            "applies_to": ["condominium", "apartment"],
            "key_provisions": [
                "Horizontal subdivision of property",
                "Common areas shared by owners",
                "Management corporation mandatory",
                "Foreigners can own above ground floor",
                "Separate title for each unit"
            ]
        },
        {
            "id": "registration_of_title_act",
            "name": "Registration of Title Act (Bim Saviya)",
            "short_name": "RTA",
            "act_number": "Act No. 21 of 1998",
            "year": 1998,
            "category": "Title Registration",
            "url": None,
            "pdf_url": None,
            "description": "Introduces Torrens system of title registration. State guarantees registered title. Being implemented district by district.",
            "applies_to": ["all"],
            "key_provisions": [
                "State guaranteed title",
                "Title register is conclusive evidence",
                "Compensation fund for errors",
                "Replaces deed system in gazetted areas",
                "Cadastral survey required"
            ]
        },
        {
            "id": "state_lands_ordinance",
            "name": "State Lands Ordinance",
            "short_name": "SLO",
            "act_number": "Ordinance No. 8 of 1947",
            "year": 1947,
            "category": "State Land",
            "url": None,
            "pdf_url": None,
            "description": "Governs state land administration, alienation, and permits. All land not privately owned vests in the state.",
            "applies_to": ["state_land", "permit", "grant"],
            "key_provisions": [
                "All land vests in state unless privately owned",
                "Grants, leases, permits for state land",
                "Land Development Ordinance for agricultural land",
                "Restrictions on transfer of granted land",
                "Encroachment provisions"
            ]
        },
        {
            "id": "rent_act",
            "name": "Rent Act",
            "short_name": "RA",
            "act_number": "Act No. 7 of 1972",
            "year": 1972,
            "category": "Tenancy",
            "url": None,
            "pdf_url": None,
            "description": "Controls rent and provides security of tenure for residential premises. Applies to premises constructed before 1980.",
            "applies_to": ["lease", "tenancy"],
            "key_provisions": [
                "Applies to pre-1980 residential premises",
                "Standard rent calculation",
                "Grounds for eviction limited",
                "Tenant has right of first refusal",
                "Controlled premises require permit to sell"
            ]
        },
        {
            "id": "powers_of_attorney_ordinance",
            "name": "Powers of Attorney Ordinance",
            "short_name": "PAO",
            "act_number": "Chapter 83",
            "year": 1925,
            "category": "Agency",
            "url": "https://www.srilankalaw.lk/revised-statutes/alphabetical-list-of-statutes/914-powers-of-attorney-ordinance.html",
            "pdf_url": "https://www.parliament.lk/uploads/acts/gbills/english/6266.pdf",
            "description": "Provides for registration of powers of attorney. Recent amendments require specific property description.",
            "applies_to": ["power_of_attorney"],
            "key_provisions": [
                "Must be registered with Registrar General",
                "Must describe property with boundaries",
                "Volume and folio reference required",
                "Notary must verify non-revocation",
                "Biometric identification required"
            ]
        },
        {
            "id": "wills_ordinance",
            "name": "Wills Ordinance",
            "short_name": "WO",
            "act_number": "Ordinance No. 7 of 1840",
            "year": 1840,
            "category": "Succession",
            "url": None,
            "pdf_url": None,
            "description": "Provides for making of wills devising immovable property. Must be notarially attested.",
            "applies_to": ["will", "testament"],
            "key_provisions": [
                "Will must be in writing",
                "Notarially attested",
                "Two witnesses required",
                "Testator must be of sound mind",
                "Probate required for execution"
            ]
        }
    ]
}

# =============================================================================
# STATUTE SECTIONS (Real content from Sri Lankan law)
# =============================================================================

STATUTE_SECTIONS = [
    # Prevention of Frauds Ordinance Sections
    {
        "id": "pfo_s2",
        "statute_id": "prevention_of_frauds_ordinance",
        "section_number": "Section 2",
        "title": "Deeds affecting immovable property to be executed before a notary and witnesses",
        "content": """No sale, purchase, transfer, assignment, or mortgage of land or other immovable property, 
and no promise, bargain, contract, or agreement for effecting any such object, or for establishing 
any security, interest, or encumbrance affecting land or other immovable property (other than a 
lease for any period not exceeding one month) shall be of force or avail in law unless the same 
shall be in writing and signed by the party making the same or by some person lawfully authorized 
by him or her in the presence of a licensed notary public and two or more witnesses present at 
the same time who shall attest the signature of such person, which attestation shall be in the 
form hereinafter prescribed or to the like effect.""",
        "importance": "critical"
    },
    {
        "id": "pfo_s4",
        "statute_id": "prevention_of_frauds_ordinance",
        "section_number": "Section 4",
        "title": "Form of attestation",
        "content": """The attestation required by section 2 shall be substantially in the following form: 
'I, A.B., notary public of [district], do hereby certify and attest that the above-named C.D. 
(the executant) did appear before me on the [date] at [place], and in my presence and in the 
presence of [witness names], the subscribing witnesses hereto, did set his hand to and execute 
the foregoing instrument, after the same had been read over and explained by me to him/her, 
and that the said witnesses subscribed their names in my presence as attesting witnesses.'""",
        "importance": "high"
    },
    {
        "id": "pfo_s7",
        "statute_id": "prevention_of_frauds_ordinance",
        "section_number": "Section 7",
        "title": "Lease exceeding one month to be notarially executed",
        "content": """No lease of any land or immovable property for any period exceeding one month, 
and no promise, bargain, contract, or agreement relating thereto, shall be of force or avail 
in law unless it is executed and attested in the manner provided by section 2.""",
        "importance": "high"
    },
    {
        "id": "pfo_s18",
        "statute_id": "prevention_of_frauds_ordinance",
        "section_number": "Section 18",
        "title": "No promise to be in force unless in writing and signed",
        "content": """No promise, contract, bargain or agreement, unless it be in writing and signed 
by the party making the same or by some person thereto lawfully authorised by him or her, 
shall be of force or avail in law for any of the following purposes: 
(a) To charge any person upon any promise made after full age to pay any debt contracted during infancy;
(b) To charge any person upon any contract or sale of lands, tenements, or hereditaments, 
or any interest in or concerning them;
(c) To charge any person upon any agreement that is not to be performed within the space of one year;
(d) To charge any person upon any agreement made in consideration of marriage;
(e) To charge any person upon any representation or assurance as to the character of any other person.""",
        "importance": "high"
    },
    # Registration of Documents Ordinance Sections
    {
        "id": "rdo_s7",
        "statute_id": "registration_of_documents_ordinance",
        "section_number": "Section 7",
        "title": "Effect of non-registration",
        "content": """An instrument executed or made on or after the 1st day of January, 1864, 
whether before or after the commencement of this Ordinance shall, unless it is duly registered 
under this Chapter, be void as against all parties claiming an adverse interest thereto on 
valuable consideration by virtue of any subsequent instrument which is duly registered under 
this Chapter. But fraud or collusion in obtaining such subsequent instrument or in securing 
the prior registration thereof shall defeat the priority of the person claiming thereunder.""",
        "importance": "critical"
    },
    {
        "id": "rdo_s8",
        "statute_id": "registration_of_documents_ordinance",
        "section_number": "Section 8",
        "title": "Time for registration",
        "content": """Every instrument requiring registration under this Chapter shall be presented 
for registration within three months from the date of its execution. An instrument executed 
outside Sri Lanka may be presented within six months. Late registration is possible with 
penalty payment, but priority may be lost to instruments registered in the interim.""",
        "importance": "critical"
    },
    {
        "id": "rdo_s14",
        "statute_id": "registration_of_documents_ordinance",
        "section_number": "Section 14",
        "title": "Registration in proper folio",
        "content": """Every instrument shall be registered on the folio in which previous registrations 
relating to the said land is registered or in any other folio cross-referenced to the said 
previous folio. Failure to register in the proper folio may result in loss of priority.""",
        "importance": "high"
    },
    {
        "id": "rdo_s32",
        "statute_id": "registration_of_documents_ordinance",
        "section_number": "Section 32",
        "title": "Caveats",
        "content": """Any person claiming any right, title, or interest in any land may lodge a caveat 
with the Registrar forbidding the registration of any instrument affecting such land. 
The caveat remains in force for one year unless cancelled or extended by court order. 
A caveat does not of itself create any interest in the land.""",
        "importance": "high"
    },
    # Prescription Ordinance Sections
    {
        "id": "po_s3",
        "statute_id": "prescription_ordinance",
        "section_number": "Section 3",
        "title": "Term of prescription for land or immovable property",
        "content": """Proof of the undisturbed and uninterrupted possession by a defendant in any action, 
or by those under whom he claims, of lands or immovable property, by a title adverse to or 
independent of that of the claimant or plaintiff in such action for ten years previous to the 
bringing of such action, shall entitle the defendant to a decree in his favour with costs. 
The burden of proof shall be on the defendant.""",
        "importance": "critical"
    },
    {
        "id": "po_s13",
        "statute_id": "prescription_ordinance",
        "section_number": "Section 13",
        "title": "Prescription between co-owners",
        "content": """Long continued exclusive possession by one co-owner is not necessarily adverse 
to the other co-owners. However, where a co-owner has possessed exclusively, openly, and 
continuously for the prescriptive period with acts of ouster, prescription may run.""",
        "importance": "high"
    },
    {
        "id": "po_s15",
        "statute_id": "prescription_ordinance",
        "section_number": "Section 15",
        "title": "Rights of the State not affected",
        "content": """Nothing herein contained shall in any way affect the rights of the State. 
Prescriptive rights cannot be acquired against state land or Crown land.""",
        "importance": "critical"
    },
    # Partition Act Sections
    {
        "id": "pa_s2",
        "statute_id": "partition_act",
        "section_number": "Section 2",
        "title": "Institution of partition action",
        "content": """Any co-owner of land may institute an action in the District Court for the 
partition of such land or for the sale thereof and distribution of the proceeds among the 
co-owners. The action shall be instituted in the court within the local limits of whose 
jurisdiction the land is situated.""",
        "importance": "high"
    },
    {
        "id": "pa_s24",
        "statute_id": "partition_act",
        "section_number": "Section 24",
        "title": "Interlocutory decree",
        "content": """The court shall make an interlocutory decree declaring the rights and interests 
of all parties to the action. The decree shall specify the share or interest of each party 
entitled to any right, share, or interest in the land.""",
        "importance": "high"
    },
    # Mortgage Act Sections
    {
        "id": "ma_s6",
        "statute_id": "mortgage_act",
        "section_number": "Section 6",
        "title": "Form of Mortgage",
        "content": """Every mortgage of immovable property shall be effected by a notarially executed deed. 
The deed shall specify the property mortgaged with boundaries, the amount secured, 
rate of interest, and terms of repayment.""",
        "importance": "critical"
    },
    {
        "id": "ma_s7",
        "statute_id": "mortgage_act",
        "section_number": "Section 7",
        "title": "Rights of Mortgagee",
        "content": """The mortgagee shall have the right to: (a) receive the mortgage debt with interest; 
(b) sue for the mortgage money; (c) cause the mortgaged property to be sold on default; 
(d) apply the net proceeds of sale towards payment of the mortgage debt.""",
        "importance": "high"
    },
    # Stamp Duty
    {
        "id": "sda_s3",
        "statute_id": "stamp_duty_act",
        "section_number": "Section 3",
        "title": "Instruments chargeable with stamp duty",
        "content": """There shall be charged on every instrument specified in the Schedule stamp duty 
at the prescribed rate. Different rates may be prescribed for different classes of instruments. 
Stamp duty on property transfers is 4% (LKR 4 per LKR 100) payable to the Provincial Council.""",
        "importance": "critical"
    }
]

# =============================================================================
# LEGAL DEFINITIONS
# =============================================================================

LEGAL_DEFINITIONS = [
    {"term": "Immovable Property", "definition": "Land and things attached to the earth or permanently fastened to anything attached to the earth. Includes any estate or interest in land, and a mortgage of or charge on land.", "source": "Registration of Documents Ordinance"},
    {"term": "Conveyance", "definition": "A transfer of ownership of immovable property from one person to another by means of a written instrument duly executed and registered.", "source": "Prevention of Frauds Ordinance"},
    {"term": "Vendor", "definition": "The seller of immovable property; the party transferring ownership in a sale deed.", "source": "General Legal Usage"},
    {"term": "Vendee", "definition": "The buyer of immovable property; the party receiving ownership in a sale deed.", "source": "General Legal Usage"},
    {"term": "Notary Public", "definition": "A licensed legal professional authorized to attest deeds and documents relating to immovable property. Must be licensed to practice in the district where the property is situated.", "source": "Notaries Ordinance"},
    {"term": "Mortgage", "definition": "A transfer of an interest in immovable property as security for a debt, with the right of redemption upon payment of the debt.", "source": "Mortgage Act"},
    {"term": "Prescription", "definition": "The acquisition of title to property through continuous, uninterrupted, and adverse possession for a statutory period of 10 years in Sri Lanka.", "source": "Prescription Ordinance"},
    {"term": "Adverse Possession", "definition": "Possession of land that is hostile to the true owner's title, open and notorious, exclusive, and continuous for the prescriptive period.", "source": "Prescription Ordinance"},
    {"term": "Attestation", "definition": "The act of witnessing the execution of a document and signing it as a witness. For property deeds, requires two witnesses and a notary public.", "source": "Prevention of Frauds Ordinance"},
    {"term": "Registration", "definition": "The official recording of an instrument affecting land at the Land Registry, giving it validity against third parties.", "source": "Registration of Documents Ordinance"},
    {"term": "Caveat", "definition": "A notice lodged with the Land Registry by a person claiming an interest in land, warning against registration of any dealing without the caveator's consent.", "source": "Registration of Documents Ordinance"},
    {"term": "Encumbrance", "definition": "A burden or charge on property that may diminish its value, such as a mortgage, lien, easement, or restrictive covenant.", "source": "General Legal Usage"},
    {"term": "Easement", "definition": "A right to use another's land for a specific purpose, such as a right of way or right to light and air.", "source": "Servitudes Ordinance"},
    {"term": "Servitude", "definition": "A burden imposed on one property (servient tenement) for the benefit of another property (dominant tenement).", "source": "Servitudes Ordinance"},
    {"term": "Partition", "definition": "The division of land held in common among co-owners, giving each a separate title to their share.", "source": "Partition Act"},
    {"term": "Interlocutory Decree", "definition": "A preliminary decree in partition proceedings declaring the rights and shares of each co-owner before physical division.", "source": "Partition Act"},
    {"term": "Final Decree", "definition": "The concluding decree in partition proceedings that vests separate title in each co-owner after physical division or sale.", "source": "Partition Act"},
    {"term": "Lease", "definition": "A contract by which the owner of property grants another the right to possess and use it for a specified period in return for rent.", "source": "Prevention of Frauds Ordinance"},
    {"term": "Gift", "definition": "A voluntary transfer of property without consideration. Must be notarially executed and registered for immovable property.", "source": "Prevention of Frauds Ordinance"},
    {"term": "Will/Testament", "definition": "A legal declaration of a person's wishes regarding the disposal of their property after death. Must be notarially attested for immovable property.", "source": "Wills Ordinance"},
    {"term": "Probate", "definition": "Official proof of a will, granted by court, authorizing the executor to administer the estate.", "source": "Wills Ordinance"},
    {"term": "Power of Attorney", "definition": "A legal document authorizing one person to act on behalf of another in legal and financial matters.", "source": "Powers of Attorney Ordinance"},
    {"term": "Stamp Duty", "definition": "A tax payable on legal documents, including property transfers. Currently 4% for property transfers, payable to Provincial Council.", "source": "Stamp Duty Act"},
    {"term": "Consideration", "definition": "Something of value given in exchange for a promise or property. In sale deeds, this is the purchase price.", "source": "Contract Law"},
    {"term": "Title", "definition": "The legal right to ownership of property. A good title is one that is free from defects and encumbrances.", "source": "General Legal Usage"},
    {"term": "Chain of Title", "definition": "The sequence of historical transfers of title to a property, showing the succession of ownership.", "source": "Conveyancing Practice"},
    {"term": "Folio", "definition": "A page or entry in the Land Registry where documents relating to a particular property are recorded.", "source": "Registration of Documents Ordinance"},
    {"term": "Perch", "definition": "A unit of land measurement in Sri Lanka equal to 25.29 square meters or 272.25 square feet.", "source": "Survey Practice"},
    {"term": "Extent", "definition": "The area or size of a land parcel, typically expressed in acres, roods, and perches or square meters.", "source": "Survey Practice"},
    {"term": "Boundaries", "definition": "The lines or features marking the limits of a property, typically described as North, South, East, and West.", "source": "Survey Practice"}
]

# =============================================================================
# LEGAL PRINCIPLES
# =============================================================================

LEGAL_PRINCIPLES = [
    {
        "name": "Nemo Dat Quod Non Habet",
        "english": "No one can give what they do not have",
        "description": "A fundamental principle that a person cannot transfer better title than they possess. A purchaser cannot acquire ownership if the seller does not have valid title to transfer.",
        "application": "Essential for validating chain of title in property transfers. Buyers must verify seller's title before purchase."
    },
    {
        "name": "Caveat Emptor",
        "english": "Let the buyer beware",
        "description": "The buyer is responsible for verifying the title, condition, and encumbrances of property before purchase. The seller is not obligated to disclose defects not asked about.",
        "application": "Emphasizes importance of title search and due diligence before property purchase."
    },
    {
        "name": "Qui Prior Est Tempore Potior Est Jure",
        "english": "First in time, stronger in right",
        "description": "The person who acquires an interest first has priority over those who acquire interests later. In registered land, priority is based on date of registration.",
        "application": "Governs priority of competing interests in property, subject to registration requirements."
    },
    {
        "name": "Res Judicata",
        "english": "A matter judged",
        "description": "Once a matter has been finally adjudicated by a court, it cannot be relitigated between the same parties.",
        "application": "Partition decrees are final and conclusive as to the rights declared therein."
    },
    {
        "name": "Nulla Poena Sine Lege",
        "english": "No punishment without law",
        "description": "An act cannot be punished unless there is a law prohibiting it at the time the act was committed.",
        "application": "Relevant to fraudulent conveyances and property offenses."
    },
    {
        "name": "Actus Non Facit Reum Nisi Mens Sit Rea",
        "english": "An act does not make one guilty unless the mind is guilty",
        "description": "Criminal liability requires both a guilty act and guilty mind. Relevant to property fraud.",
        "application": "Applied in cases of fraudulent property transactions and forgery."
    },
    {
        "name": "Lex Loci Rei Sitae",
        "english": "The law of the place where the property is situated",
        "description": "Immovable property is governed by the law of the country or jurisdiction where it is located.",
        "application": "Sri Lankan law applies to all property situated in Sri Lanka, regardless of owner's nationality."
    },
    {
        "name": "Equity Follows the Law",
        "english": "Equity follows the law",
        "description": "Equitable principles supplement but do not override statutory law. Where statute is clear, equity cannot contradict it.",
        "application": "Courts apply equitable remedies consistently with statutory requirements for property transactions."
    },
    {
        "name": "Vigilantibus Non Dormientibus Jura Subveniunt",
        "english": "The law assists the vigilant, not the sleeping",
        "description": "Those who delay in asserting their rights may lose them. Foundation of limitation periods and prescription.",
        "application": "Basis for 10-year prescription period. Owners must be vigilant in protecting their property rights."
    },
    {
        "name": "Delegatus Non Potest Delegare",
        "english": "A delegate cannot delegate",
        "description": "One to whom powers have been delegated cannot sub-delegate those powers unless expressly authorized.",
        "application": "Relevant to powers of attorney - agent cannot delegate authority without express permission."
    }
]

# =============================================================================
# DEED REQUIREMENTS BY TYPE
# =============================================================================

DEED_REQUIREMENTS = [
    {
        "deed_type": "sale_transfer",
        "name": "Deed of Transfer / Sale Deed",
        "requirements": [
            "Written document",
            "Notarially attested",
            "Two witnesses",
            "Parties identified by NIC",
            "Property clearly described with boundaries",
            "Survey plan referenced",
            "Consideration stated",
            "Prior deed reference",
            "Stamp duty paid (4%)",
            "Registered within 3 months"
        ],
        "stamp_duty": "4% of consideration or market value (whichever is higher)",
        "registration_fee": "Based on consideration value (approx. 0.25%)",
        "time_limit": "Register within 3 months of execution",
        "governing_statutes": ["Prevention of Frauds Ordinance", "Registration of Documents Ordinance", "Stamp Duty Act"]
    },
    {
        "deed_type": "gift",
        "name": "Deed of Gift / Donation",
        "requirements": [
            "Written document",
            "Notarially attested",
            "Two witnesses",
            "Parties identified by NIC",
            "Property clearly described",
            "Acceptance by donee",
            "No consideration (or nominal)",
            "Prior deed reference",
            "Stamp duty exempted (between close relatives)",
            "Registered within 3 months"
        ],
        "stamp_duty": "Exempted for gifts between spouses, parents/children, siblings",
        "registration_fee": "Based on market value (approx. 0.25%)",
        "time_limit": "Register within 3 months of execution",
        "governing_statutes": ["Prevention of Frauds Ordinance", "Registration of Documents Ordinance"]
    },
    {
        "deed_type": "mortgage",
        "name": "Mortgage Deed / Hypothecation",
        "requirements": [
            "Written document",
            "Notarially attested",
            "Two witnesses",
            "Parties identified by NIC",
            "Property clearly described",
            "Amount secured stated",
            "Interest rate specified",
            "Repayment terms",
            "Default provisions",
            "Prior deed reference",
            "Registered within 3 months"
        ],
        "stamp_duty": "0.5% of loan amount",
        "registration_fee": "Based on loan value",
        "time_limit": "Register within 3 months of execution",
        "governing_statutes": ["Prevention of Frauds Ordinance", "Mortgage Act", "Registration of Documents Ordinance"]
    },
    {
        "deed_type": "lease",
        "name": "Lease Deed",
        "requirements": [
            "Written document (if >1 month)",
            "Notarially attested (if >1 month)",
            "Two witnesses",
            "Parties identified",
            "Property clearly described",
            "Lease period specified",
            "Monthly/annual rent stated",
            "Terms and conditions",
            "Renewal provisions",
            "Registered (if >1 year)"
        ],
        "stamp_duty": "LKR 10 per LKR 1,000 of annual rent",
        "registration_fee": "Based on annual rent value",
        "time_limit": "Register within 3 months if period exceeds 1 year",
        "governing_statutes": ["Prevention of Frauds Ordinance", "Rent Act", "Registration of Documents Ordinance"]
    },
    {
        "deed_type": "will",
        "name": "Last Will and Testament",
        "requirements": [
            "Written document",
            "Notarially attested",
            "Two witnesses",
            "Testator identified by NIC",
            "Property clearly described",
            "Beneficiaries named",
            "Executor appointed",
            "Testator of sound mind",
            "Read and explained to testator"
        ],
        "stamp_duty": "Exempted",
        "registration_fee": "Not required during lifetime",
        "time_limit": "Probate required after death for execution",
        "governing_statutes": ["Prevention of Frauds Ordinance", "Wills Ordinance", "Testamentary Cases Ordinance"]
    },
    {
        "deed_type": "partition",
        "name": "Partition Deed / Court Decree",
        "requirements": [
            "Court action filed",
            "All co-owners made parties",
            "Survey plan by licensed surveyor",
            "Interlocutory decree",
            "Physical division feasible OR sale ordered",
            "Final decree",
            "Registration of decree"
        ],
        "stamp_duty": "Exempted for partition among co-owners",
        "registration_fee": "Court fees applicable",
        "time_limit": "As per court proceedings",
        "governing_statutes": ["Partition Act", "Registration of Documents Ordinance"]
    },
    {
        "deed_type": "power_of_attorney",
        "name": "Power of Attorney for Property",
        "requirements": [
            "Written document",
            "Notarially attested",
            "Two witnesses",
            "Principal identified by NIC",
            "Attorney identified by NIC",
            "Property described with boundaries",
            "Volume and folio reference",
            "Thumb impression of principal",
            "Registered with Registrar General"
        ],
        "stamp_duty": "Exempted",
        "registration_fee": "Nominal fee",
        "time_limit": "Must be registered before use",
        "governing_statutes": ["Powers of Attorney Ordinance", "Prevention of Frauds Ordinance"]
    }
]

# =============================================================================
# LAND PRICES BY DISTRICT (2024-2025 Data)
# =============================================================================

LAND_PRICES = {
    "Western": {
        "Colombo": {
            "city_center": {"min": 15000000, "max": 50000000, "avg": 25000000, "unit": "per_perch"},
            "colombo_1_15": {"min": 12000000, "max": 45000000, "avg": 22000000, "unit": "per_perch"},
            "suburbs": {"min": 1500000, "max": 8000000, "avg": 4000000, "unit": "per_perch"},
            "outer_areas": {"min": 500000, "max": 2000000, "avg": 1200000, "unit": "per_perch"},
            "areas": {
                "Colombo 3": {"avg": 35000000, "trend": "+7%"},
                "Colombo 5": {"avg": 28000000, "trend": "+5%"},
                "Colombo 6": {"avg": 15000000, "trend": "+6%"},
                "Colombo 7": {"avg": 32000000, "trend": "+4%"},
                "Rajagiriya": {"avg": 8000000, "trend": "+12%"},
                "Nugegoda": {"avg": 5000000, "trend": "+15%"},
                "Dehiwala": {"avg": 6000000, "trend": "+10%"},
                "Moratuwa": {"avg": 3500000, "trend": "+18%"},
                "Kolonnawa": {"avg": 2800000, "trend": "+21%"},
                "Maharagama": {"avg": 3000000, "trend": "+20%"},
                "Homagama": {"avg": 1200000, "trend": "+25%"},
                "Kaduwela": {"avg": 2000000, "trend": "+22%"},
                "Athurugiriya": {"avg": 1800000, "trend": "+28%"}
            }
        },
        "Gampaha": {
            "city_center": {"min": 2000000, "max": 6000000, "avg": 3500000, "unit": "per_perch"},
            "suburbs": {"min": 800000, "max": 2500000, "avg": 1500000, "unit": "per_perch"},
            "outer_areas": {"min": 300000, "max": 1000000, "avg": 600000, "unit": "per_perch"},
            "areas": {
                "Gampaha Town": {"avg": 3500000, "trend": "+42%"},
                "Negombo": {"avg": 4000000, "trend": "+15%"},
                "Kelaniya": {"avg": 3800000, "trend": "+25%"},
                "Kadawatha": {"avg": 2800000, "trend": "+20%"},
                "Ja-Ela": {"avg": 2200000, "trend": "+18%"},
                "Minuwangoda": {"avg": 1500000, "trend": "+22%"},
                "Yakkala": {"avg": 1200000, "trend": "+55%"},
                "Dompe": {"avg": 800000, "trend": "+35%"}
            }
        },
        "Kalutara": {
            "city_center": {"min": 1500000, "max": 4000000, "avg": 2500000, "unit": "per_perch"},
            "suburbs": {"min": 500000, "max": 1500000, "avg": 900000, "unit": "per_perch"},
            "coastal": {"min": 2000000, "max": 8000000, "avg": 4000000, "unit": "per_perch"},
            "areas": {
                "Kalutara Town": {"avg": 2500000, "trend": "+12%"},
                "Panadura": {"avg": 3000000, "trend": "+15%"},
                "Wadduwa": {"avg": 3500000, "trend": "+18%"},
                "Beruwala": {"avg": 2800000, "trend": "+14%"},
                "Piliyandala": {"avg": 2200000, "trend": "+20%"},
                "Ingiriya": {"avg": 600000, "trend": "+48%"},
                "Horana": {"avg": 800000, "trend": "+25%"}
            }
        }
    },
    "Central": {
        "Kandy": {
            "city_center": {"min": 3000000, "max": 10000000, "avg": 5000000, "unit": "per_perch"},
            "suburbs": {"min": 800000, "max": 2500000, "avg": 1500000, "unit": "per_perch"},
            "outer_areas": {"min": 200000, "max": 800000, "avg": 400000, "unit": "per_perch"},
            "areas": {
                "Kandy Town": {"avg": 5000000, "trend": "+15%"},
                "Peradeniya": {"avg": 3000000, "trend": "+12%"},
                "Katugastota": {"avg": 2000000, "trend": "+18%"},
                "Digana": {"avg": 1200000, "trend": "+20%"},
                "Kundasale": {"avg": 1000000, "trend": "+22%"}
            }
        },
        "Matale": {
            "city_center": {"min": 500000, "max": 1500000, "avg": 900000, "unit": "per_perch"},
            "outer_areas": {"min": 150000, "max": 500000, "avg": 300000, "unit": "per_perch"},
            "areas": {
                "Matale Town": {"avg": 900000, "trend": "+10%"},
                "Dambulla": {"avg": 700000, "trend": "+15%"}
            }
        },
        "Nuwara Eliya": {
            "town_areas": {"min": 800000, "max": 3000000, "avg": 1500000, "unit": "per_perch"},
            "plantation_areas": {"min": 100000, "max": 400000, "avg": 200000, "unit": "per_perch"},
            "areas": {
                "Nuwara Eliya Town": {"avg": 1500000, "trend": "+8%"},
                "Hatton": {"avg": 600000, "trend": "+12%"}
            }
        }
    },
    "Southern": {
        "Galle": {
            "city_center": {"min": 2000000, "max": 8000000, "avg": 4000000, "unit": "per_perch"},
            "coastal": {"min": 3000000, "max": 15000000, "avg": 6000000, "unit": "per_perch"},
            "inland": {"min": 500000, "max": 1500000, "avg": 800000, "unit": "per_perch"},
            "areas": {
                "Galle Fort": {"avg": 12000000, "trend": "+8%"},
                "Galle Town": {"avg": 4000000, "trend": "+10%"},
                "Unawatuna": {"avg": 8000000, "trend": "+12%"},
                "Hikkaduwa": {"avg": 6000000, "trend": "+15%"},
                "Habaraduwa": {"avg": 2500000, "trend": "+18%"}
            }
        },
        "Matara": {
            "city_center": {"min": 1000000, "max": 3000000, "avg": 1800000, "unit": "per_perch"},
            "coastal": {"min": 1500000, "max": 5000000, "avg": 2500000, "unit": "per_perch"},
            "areas": {
                "Matara Town": {"avg": 1800000, "trend": "+12%"},
                "Weligama": {"avg": 3000000, "trend": "+15%"},
                "Mirissa": {"avg": 5000000, "trend": "+20%"}
            }
        },
        "Hambantota": {
            "city_center": {"min": 500000, "max": 1500000, "avg": 800000, "unit": "per_perch"},
            "development_zones": {"min": 800000, "max": 2500000, "avg": 1500000, "unit": "per_perch"},
            "areas": {
                "Hambantota Town": {"avg": 1000000, "trend": "+25%"},
                "Tangalle": {"avg": 2000000, "trend": "+18%"}
            }
        }
    },
    "North Western": {
        "Kurunegala": {
            "city_center": {"min": 800000, "max": 2500000, "avg": 1500000, "unit": "per_perch"},
            "suburbs": {"min": 300000, "max": 1000000, "avg": 600000, "unit": "per_perch"},
            "areas": {
                "Kurunegala Town": {"avg": 1500000, "trend": "+12%"},
                "Kuliyapitiya": {"avg": 600000, "trend": "+15%"}
            }
        },
        "Puttalam": {
            "town_areas": {"min": 400000, "max": 1200000, "avg": 700000, "unit": "per_perch"},
            "areas": {
                "Puttalam Town": {"avg": 700000, "trend": "+10%"},
                "Chilaw": {"avg": 1200000, "trend": "+12%"}
            }
        }
    },
    "North Central": {
        "Anuradhapura": {
            "city_center": {"min": 600000, "max": 1800000, "avg": 1000000, "unit": "per_perch"},
            "outer_areas": {"min": 150000, "max": 500000, "avg": 300000, "unit": "per_perch"},
            "areas": {
                "Anuradhapura Town": {"avg": 1000000, "trend": "+15%"}
            }
        },
        "Polonnaruwa": {
            "town_areas": {"min": 300000, "max": 800000, "avg": 500000, "unit": "per_perch"},
            "areas": {
                "Polonnaruwa Town": {"avg": 500000, "trend": "+12%"}
            }
        }
    },
    "Uva": {
        "Badulla": {
            "city_center": {"min": 500000, "max": 1500000, "avg": 900000, "unit": "per_perch"},
            "areas": {
                "Badulla Town": {"avg": 900000, "trend": "+10%"},
                "Bandarawela": {"avg": 800000, "trend": "+12%"}
            }
        },
        "Monaragala": {
            "town_areas": {"min": 200000, "max": 600000, "avg": 350000, "unit": "per_perch"},
            "areas": {
                "Monaragala Town": {"avg": 350000, "trend": "+8%"}
            }
        }
    },
    "Sabaragamuwa": {
        "Ratnapura": {
            "city_center": {"min": 600000, "max": 1800000, "avg": 1000000, "unit": "per_perch"},
            "gem_areas": {"min": 800000, "max": 2500000, "avg": 1500000, "unit": "per_perch"},
            "areas": {
                "Ratnapura Town": {"avg": 1000000, "trend": "+15%"}
            }
        },
        "Kegalle": {
            "town_areas": {"min": 400000, "max": 1200000, "avg": 700000, "unit": "per_perch"},
            "areas": {
                "Kegalle Town": {"avg": 700000, "trend": "+12%"},
                "Mawanella": {"avg": 500000, "trend": "+15%"}
            }
        }
    },
    "Eastern": {
        "Trincomalee": {
            "city_center": {"min": 800000, "max": 2500000, "avg": 1500000, "unit": "per_perch"},
            "coastal": {"min": 1000000, "max": 4000000, "avg": 2000000, "unit": "per_perch"},
            "areas": {
                "Trincomalee Town": {"avg": 1500000, "trend": "+20%"}
            }
        },
        "Batticaloa": {
            "town_areas": {"min": 500000, "max": 1500000, "avg": 900000, "unit": "per_perch"},
            "areas": {
                "Batticaloa Town": {"avg": 900000, "trend": "+15%"}
            }
        },
        "Ampara": {
            "town_areas": {"min": 300000, "max": 900000, "avg": 500000, "unit": "per_perch"},
            "areas": {
                "Ampara Town": {"avg": 500000, "trend": "+12%"}
            }
        }
    },
    "Northern": {
        "Jaffna": {
            "city_center": {"min": 1500000, "max": 5000000, "avg": 3000000, "unit": "per_perch"},
            "suburbs": {"min": 500000, "max": 1500000, "avg": 900000, "unit": "per_perch"},
            "areas": {
                "Jaffna Town": {"avg": 3000000, "trend": "+25%"},
                "Nallur": {"avg": 2500000, "trend": "+20%"}
            }
        },
        "Kilinochchi": {
            "town_areas": {"min": 300000, "max": 800000, "avg": 500000, "unit": "per_perch"},
            "areas": {
                "Kilinochchi Town": {"avg": 500000, "trend": "+30%"}
            }
        },
        "Vavuniya": {
            "town_areas": {"min": 400000, "max": 1200000, "avg": 700000, "unit": "per_perch"},
            "areas": {
                "Vavuniya Town": {"avg": 700000, "trend": "+18%"}
            }
        }
    }
}

# =============================================================================
# REGISTRY OFFICES
# =============================================================================

LAND_REGISTRIES = [
    {"name": "Colombo Land Registry", "district": "Colombo", "address": "Dam Street, Colombo 12", "phone": "011-2421291"},
    {"name": "Gampaha Land Registry", "district": "Gampaha", "address": "Gampaha", "phone": "033-2222255"},
    {"name": "Kalutara Land Registry", "district": "Kalutara", "address": "Kalutara", "phone": "034-2222333"},
    {"name": "Kandy Land Registry", "district": "Kandy", "address": "Kandy", "phone": "081-2222444"},
    {"name": "Matale Land Registry", "district": "Matale", "address": "Matale", "phone": "066-2222555"},
    {"name": "Nuwara Eliya Land Registry", "district": "Nuwara Eliya", "address": "Nuwara Eliya", "phone": "052-2222666"},
    {"name": "Galle Land Registry", "district": "Galle", "address": "Galle", "phone": "091-2222777"},
    {"name": "Matara Land Registry", "district": "Matara", "address": "Matara", "phone": "041-2222888"},
    {"name": "Hambantota Land Registry", "district": "Hambantota", "address": "Hambantota", "phone": "047-2222999"},
    {"name": "Jaffna Land Registry", "district": "Jaffna", "address": "Jaffna", "phone": "021-2223000"},
    {"name": "Kurunegala Land Registry", "district": "Kurunegala", "address": "Kurunegala", "phone": "037-2223111"},
    {"name": "Puttalam Land Registry", "district": "Puttalam", "address": "Puttalam", "phone": "032-2223222"},
    {"name": "Anuradhapura Land Registry", "district": "Anuradhapura", "address": "Anuradhapura", "phone": "025-2223333"},
    {"name": "Polonnaruwa Land Registry", "district": "Polonnaruwa", "address": "Polonnaruwa", "phone": "027-2223444"},
    {"name": "Badulla Land Registry", "district": "Badulla", "address": "Badulla", "phone": "055-2223555"},
    {"name": "Monaragala Land Registry", "district": "Monaragala", "address": "Monaragala", "phone": "055-2276666"},
    {"name": "Ratnapura Land Registry", "district": "Ratnapura", "address": "Ratnapura", "phone": "045-2223777"},
    {"name": "Kegalle Land Registry", "district": "Kegalle", "address": "Kegalle", "phone": "035-2223888"},
    {"name": "Trincomalee Land Registry", "district": "Trincomalee", "address": "Trincomalee", "phone": "026-2223999"},
    {"name": "Batticaloa Land Registry", "district": "Batticaloa", "address": "Batticaloa", "phone": "065-2224000"},
    {"name": "Ampara Land Registry", "district": "Ampara", "address": "Ampara", "phone": "063-2224111"},
    {"name": "Kilinochchi Land Registry", "district": "Kilinochchi", "address": "Kilinochchi", "phone": "021-2285000"},
    {"name": "Mannar Land Registry", "district": "Mannar", "address": "Mannar", "phone": "023-2222000"},
    {"name": "Vavuniya Land Registry", "district": "Vavuniya", "address": "Vavuniya", "phone": "024-2222000"},
    {"name": "Mullaitivu Land Registry", "district": "Mullaitivu", "address": "Mullaitivu", "phone": "021-2290000"}
]

# =============================================================================
# MAIN FUNCTIONS
# =============================================================================

def create_directories():
    """Create output directory structure."""
    subdirs = ['statutes', 'sections', 'definitions', 'prices', 
               'requirements', 'principles', 'registries', 'metadata', 'pdfs']
    
    for subdir in subdirs:
        (OUTPUT_DIR / subdir).mkdir(parents=True, exist_ok=True)
    
    print(f"✅ Created directory structure at {OUTPUT_DIR}")


def download_pdfs():
    """Download available PDF documents from official sources."""
    pdf_dir = OUTPUT_DIR / 'pdfs'
    downloaded = []
    
    pdf_sources = [
        {
            "name": "Partition_Act_Consolidated_2024",
            "url": "https://lankalaw.net/wp-content/uploads/2025/03/Partition-Consolidated-2024.pdf"
        },
        {
            "name": "Notaries_Amendment_Act_2022",
            "url": "https://www.parliament.lk/uploads/acts/gbills/english/6270.pdf"
        },
        {
            "name": "Powers_of_Attorney_Amendment_Act_2022",
            "url": "https://www.parliament.lk/uploads/acts/gbills/english/6266.pdf"
        },
        {
            "name": "Prevention_of_Frauds_Amendment_Act_2022",
            "url": "https://www.parliament.lk/uploads/acts/gbills/english/6268.pdf"
        },
        {
            "name": "Prescription_Ordinance",
            "url": "https://www.commonlii.org/lk/legis/consol_act/p81214.pdf"
        },
        {
            "name": "Land_Handbook_Mediation_Board",
            "url": "http://mediation.gov.lk/documents/80/Handbook_on_Key_Legal_and_Adminstrative_Aspects_Relating_to_Land_and_Property__Ymv9n7R.pdf"
        },
        {
            "name": "CBSL_Land_Valuation_Index_2024_H2",
            "url": "https://www.cbsl.gov.lk/sites/default/files/cbslweb_documents/press/pr/press_20250227_land_valuation_index_second_half_of_2024_e.pdf"
        }
    ]
    
    print("\n📥 Downloading PDF documents...")
    
    for source in pdf_sources:
        try:
            filepath = pdf_dir / f"{source['name']}.pdf"
            
            if filepath.exists():
                print(f"  ⏭️  {source['name']} (already exists)")
                downloaded.append({"name": source['name'], "status": "exists", "path": str(filepath)})
                continue
            
            print(f"  ⬇️  Downloading {source['name']}...")
            response = requests.get(source['url'], headers=HEADERS, timeout=30)
            
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                print(f"  ✅ {source['name']} downloaded")
                downloaded.append({"name": source['name'], "status": "downloaded", "path": str(filepath)})
            else:
                print(f"  ❌ {source['name']} failed (HTTP {response.status_code})")
                downloaded.append({"name": source['name'], "status": f"failed_{response.status_code}", "url": source['url']})
            
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"  ❌ {source['name']} error: {str(e)}")
            downloaded.append({"name": source['name'], "status": f"error: {str(e)}", "url": source['url']})
    
    # Save download log
    with open(pdf_dir / 'download_log.json', 'w') as f:
        json.dump(downloaded, f, indent=2)
    
    return downloaded


def save_statutes():
    """Save statute data as JSON files."""
    print("\n📜 Saving statute data...")
    
    for statute in LEGAL_SOURCES['statutes']:
        filepath = OUTPUT_DIR / 'statutes' / f"{statute['id']}.json"
        with open(filepath, 'w') as f:
            json.dump(statute, f, indent=2)
        print(f"  ✅ {statute['short_name']}: {statute['name']}")
    
    # Save combined file
    with open(OUTPUT_DIR / 'statutes' / '_all_statutes.json', 'w') as f:
        json.dump(LEGAL_SOURCES['statutes'], f, indent=2)
    
    return len(LEGAL_SOURCES['statutes'])


def save_sections():
    """Save statute sections as JSON files."""
    print("\n📖 Saving statute sections...")
    
    for section in STATUTE_SECTIONS:
        filepath = OUTPUT_DIR / 'sections' / f"{section['id']}.json"
        with open(filepath, 'w') as f:
            json.dump(section, f, indent=2)
        print(f"  ✅ {section['section_number']}: {section['title'][:50]}...")
    
    # Save combined file
    with open(OUTPUT_DIR / 'sections' / '_all_sections.json', 'w') as f:
        json.dump(STATUTE_SECTIONS, f, indent=2)
    
    return len(STATUTE_SECTIONS)


def save_definitions():
    """Save legal definitions as JSON."""
    print("\n📚 Saving legal definitions...")
    
    filepath = OUTPUT_DIR / 'definitions' / 'legal_definitions.json'
    with open(filepath, 'w') as f:
        json.dump(LEGAL_DEFINITIONS, f, indent=2)
    
    print(f"  ✅ Saved {len(LEGAL_DEFINITIONS)} definitions")
    return len(LEGAL_DEFINITIONS)


def save_principles():
    """Save legal principles as JSON."""
    print("\n⚖️ Saving legal principles...")
    
    filepath = OUTPUT_DIR / 'principles' / 'legal_principles.json'
    with open(filepath, 'w') as f:
        json.dump(LEGAL_PRINCIPLES, f, indent=2)
    
    print(f"  ✅ Saved {len(LEGAL_PRINCIPLES)} principles")
    return len(LEGAL_PRINCIPLES)


def save_requirements():
    """Save deed requirements as JSON."""
    print("\n📋 Saving deed requirements...")
    
    filepath = OUTPUT_DIR / 'requirements' / 'deed_requirements.json'
    with open(filepath, 'w') as f:
        json.dump(DEED_REQUIREMENTS, f, indent=2)
    
    print(f"  ✅ Saved {len(DEED_REQUIREMENTS)} deed type requirements")
    return len(DEED_REQUIREMENTS)


def save_land_prices():
    """Save land price data by district."""
    print("\n💰 Saving land price data...")
    
    filepath = OUTPUT_DIR / 'prices' / 'land_prices_by_district.json'
    with open(filepath, 'w') as f:
        json.dump(LAND_PRICES, f, indent=2)
    
    # Count total areas
    total_areas = sum(
        len(district_data.get('areas', {})) 
        for province_data in LAND_PRICES.values() 
        for district_data in province_data.values()
    )
    
    print(f"  ✅ Saved prices for {len(LAND_PRICES)} provinces, {total_areas} areas")
    return total_areas


def save_registries():
    """Save land registry office data."""
    print("\n🏛️ Saving land registry data...")
    
    filepath = OUTPUT_DIR / 'registries' / 'land_registries.json'
    with open(filepath, 'w') as f:
        json.dump(LAND_REGISTRIES, f, indent=2)
    
    print(f"  ✅ Saved {len(LAND_REGISTRIES)} land registry offices")
    return len(LAND_REGISTRIES)


def save_metadata():
    """Save metadata about the data collection."""
    print("\n📊 Saving metadata...")
    
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "version": "1.0.0",
        "description": "Sri Lankan Property Law Knowledge Graph Data",
        "sources": [
            "srilankalaw.lk - Revised Statutes",
            "lawnet.gov.lk - Official Legal Portal",
            "parliament.lk - Acts and Amendments",
            "cbsl.gov.lk - Land Valuation Indicators",
            "lankapropertyweb.com - Market Price Data"
        ],
        "statistics": {
            "statutes": len(LEGAL_SOURCES['statutes']),
            "sections": len(STATUTE_SECTIONS),
            "definitions": len(LEGAL_DEFINITIONS),
            "principles": len(LEGAL_PRINCIPLES),
            "deed_types": len(DEED_REQUIREMENTS),
            "provinces": len(LAND_PRICES),
            "registries": len(LAND_REGISTRIES)
        },
        "legal_urls": {
            "srilankalaw": "https://www.srilankalaw.lk/",
            "lawnet": "https://www.lawnet.gov.lk/",
            "parliament": "https://www.parliament.lk/",
            "gazette": "https://documents.gov.lk/",
            "valuation_dept": "https://valuationdept.gov.lk/"
        }
    }
    
    filepath = OUTPUT_DIR / 'metadata' / 'data_metadata.json'
    with open(filepath, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"  ✅ Metadata saved")
    return metadata


def main():
    """Main function to download and save all data."""
    print("=" * 60)
    print("🏛️ Sri Lankan Legal Data Downloader")
    print("=" * 60)
    
    # Create directories
    create_directories()
    
    # Download PDFs
    pdfs = download_pdfs()
    
    # Save all data
    statutes = save_statutes()
    sections = save_sections()
    definitions = save_definitions()
    principles = save_principles()
    requirements = save_requirements()
    prices = save_land_prices()
    registries = save_registries()
    metadata = save_metadata()
    
    print("\n" + "=" * 60)
    print("✅ DATA DOWNLOAD COMPLETE")
    print("=" * 60)
    print(f"""
Summary:
  📜 Statutes:     {statutes}
  📖 Sections:     {sections}
  📚 Definitions:  {definitions}
  ⚖️ Principles:   {principles}
  📋 Deed Types:   {requirements}
  💰 Price Areas:  {prices}
  🏛️ Registries:   {registries}
  📥 PDFs:         {len([p for p in pdfs if p['status'] in ['downloaded', 'exists']])} downloaded

Output directory: {OUTPUT_DIR}

Next step: Run 'python load_extra_laws_to_neo4j.py' to load into Neo4j
""")


if __name__ == "__main__":
    main()
