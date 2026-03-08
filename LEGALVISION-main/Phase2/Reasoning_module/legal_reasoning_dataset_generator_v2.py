"""
Legal Reasoning Dataset Generator V2 - ENHANCED VERSION
Generates massive Chain-of-Thought, IRAC, and Decision Tree training data

Author: S. Sivanuja
Project: LegalVision - Explainable Legal Reasoning Module
Version: 2.0 - Enhanced for Large-Scale Training Data Generation

Key Improvements:
- 10x more seed questions per topic
- Multiple question variations and paraphrasing
- Scenario-based question generation from downloaded laws
- Multi-turn conversation generation
- Cross-topic relationship training
- Difficulty progression datasets
- Adversarial/edge case generation
- Synthetic case study generation
- Comparative analysis pairs
- Error correction training data
"""

import os
import json
import time
import random
import hashlib
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
from openai import OpenAI
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

load_dotenv()

# Configuration
INPUT_DIR = Path("./data/sri_lankan_laws/raw")
OUTPUT_DIR = Path("./data/reasoning_dataset_v2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL = "gpt-4o"
FAST_MODEL = "gpt-4o-mini"  # For bulk generation

# Thread safety
api_lock = threading.Lock()


# =============================================================================
# EXPANDED LEGAL KNOWLEDGE BASE
# =============================================================================

LEGAL_TOPICS = {
    "property_transfer": {
        "name": "Property Transfer and Conveyancing",
        "statutes": [
            "Prevention of Frauds Ordinance",
            "Registration of Documents Ordinance",
            "Notaries Ordinance",
            "Stamp Duty Act"
        ],
        "key_sections": {
            "Prevention of Frauds Ordinance": [
                "Section 2 - Writing requirement for land transfers",
                "Section 3 - Exceptions to writing requirement"
            ],
            "Registration of Documents Ordinance": [
                "Section 7 - Effect of registration",
                "Section 8 - Priority of registration",
                "Section 17 - Time for registration"
            ],
            "Notaries Ordinance": [
                "Section 31 - Attestation requirements",
                "Section 32 - Notary duties",
                "Section 47 - Notary protocol"
            ]
        },
        "concepts": [
            "deed", "conveyance", "attestation", "registration", "transfer",
            "vendor", "vendee", "consideration", "title", "chain of title",
            "execution", "delivery", "acceptance", "stamp duty"
        ],
        "related_forms": ["sale deed", "gift deed", "exchange deed", "settlement deed"],
        "common_issues": [
            "defective attestation", "missing witnesses", "late registration",
            "incorrect property description", "forged signatures", "capacity issues"
        ]
    },
    "title_registration": {
        "name": "Title Registration (Bim Saviya)",
        "statutes": ["Registration of Title Act No. 21 of 1998"],
        "key_sections": {
            "Registration of Title Act": [
                "Section 4 - Title Register",
                "Section 13 - First Class Title",
                "Section 14 - Second Class Title",
                "Section 20 - Indefeasibility",
                "Section 24 - Caveats",
                "Section 32 - Fraud exception"
            ]
        },
        "concepts": [
            "bim saviya", "first class title", "second class title",
            "cadastral map", "indefeasible title", "folio", "title certificate",
            "conversion", "rectification", "indemnity", "title insurance"
        ],
        "related_forms": ["title certificate", "caveat", "priority notice"],
        "common_issues": [
            "boundary disputes", "overlapping titles", "fraudulent registration",
            "conversion delays", "cadastral mapping errors"
        ]
    },
    "prescription": {
        "name": "Prescription and Adverse Possession",
        "statutes": ["Prescription Ordinance"],
        "key_sections": {
            "Prescription Ordinance": [
                "Section 3 - Prescriptive title acquisition",
                "Section 6 - Ten year period",
                "Section 13 - Interruption of prescription",
                "Section 14 - Effect on co-owners",
                "Section 17 - Extinctive prescription"
            ]
        },
        "concepts": [
            "adverse possession", "nec vi", "nec clam", "nec precario",
            "prescriptive title", "hostile possession", "continuous possession",
            "interruption", "acknowledgment", "disability", "tacking"
        ],
        "related_forms": ["declaration of title action", "rei vindicatio"],
        "common_issues": [
            "permissive occupation", "shared possession", "boundary encroachment",
            "proving 10 years", "state land prescription"
        ]
    },
    "partition": {
        "name": "Partition of Co-owned Property",
        "statutes": ["Partition Act No. 21 of 1977"],
        "key_sections": {
            "Partition Act": [
                "Section 2 - Right to partition",
                "Section 5 - Court powers",
                "Section 17 - Interlocutory decree",
                "Section 26 - Sale in lieu of partition",
                "Section 48 - Final decree effect"
            ]
        },
        "concepts": [
            "co-ownership", "undivided share", "partition action",
            "interlocutory decree", "final decree", "res judicata",
            "shares", "allotment", "survey", "commissioner"
        ],
        "related_forms": ["partition plaint", "interlocutory decree", "final decree"],
        "common_issues": [
            "determining shares", "contesting parties", "survey disputes",
            "building allocation", "access routes", "encumbrance apportionment"
        ]
    },
    "mortgage": {
        "name": "Mortgage and Securities",
        "statutes": [
            "Mortgage Act No. 6 of 1949",
            "Recovery of Loans by Banks Act",
            "Debt Recovery (Special Provisions) Act"
        ],
        "key_sections": {
            "Mortgage Act": [
                "Section 6 - Primary mortgage rights",
                "Section 7 - Subsequent mortgages",
                "Section 12 - Foreclosure",
                "Section 18 - Sale by mortgagee"
            ],
            "Recovery of Loans by Banks Act": [
                "Section 4 - Parate execution",
                "Section 5 - Notice requirements",
                "Section 7 - Surplus distribution"
            ]
        },
        "concepts": [
            "primary mortgage", "secondary mortgage", "parate execution",
            "foreclosure", "equity of redemption", "mortgagee", "mortgagor",
            "clog on equity", "puisne mortgage", "marshalling"
        ],
        "related_forms": ["mortgage bond", "release deed", "foreclosure action"],
        "common_issues": [
            "priority disputes", "inadequate security", "default proceedings",
            "surplus distribution", "guarantor liability"
        ]
    },
    "lease_tenancy": {
        "name": "Lease and Tenancy",
        "statutes": ["Rent Act No. 7 of 1972", "Civil Procedure Code"],
        "key_sections": {
            "Rent Act": [
                "Section 10 - Authorized rent",
                "Section 22 - Protected tenants",
                "Section 23 - Grounds for ejectment",
                "Section 36 - Subletting restrictions"
            ]
        },
        "concepts": [
            "lease", "tenancy", "protected tenant", "ejectment",
            "authorized rent", "key money", "goodwill", "subletting",
            "assignment", "surrender", "forfeiture", "holding over"
        ],
        "related_forms": ["lease deed", "tenancy agreement", "ejectment action"],
        "common_issues": [
            "rent control applicability", "tenant succession",
            "premises condition", "illegal ejectment", "rent arrears"
        ]
    },
    "state_land": {
        "name": "State Land Administration",
        "statutes": [
            "Land Development Ordinance",
            "State Lands Ordinance",
            "Land Settlement Ordinance"
        ],
        "key_sections": {
            "Land Development Ordinance": [
                "Section 19 - Permits",
                "Section 20 - Grants",
                "Section 49 - Succession rules",
                "Section 67 - Alienation restrictions"
            ],
            "State Lands Ordinance": [
                "Section 6 - Alienation of state land",
                "Section 51 - Reservation of state land"
            ]
        },
        "concepts": [
            "state land", "permit", "grant", "crown land", "alienation",
            "LDO permit", "Jayabhoomi", "Swarnabhoomi", "encroachment",
            "regularization", "resumption"
        ],
        "related_forms": ["LDO permit", "grant document", "lease from state"],
        "common_issues": [
            "permit succession", "unauthorized alienation", "encroachment",
            "permit cancellation", "boundary with private land"
        ]
    },
    "foreign_ownership": {
        "name": "Foreign Ownership Restrictions",
        "statutes": [
            "Land (Restrictions on Alienation) Act",
            "Apartment Ownership Law",
            "Board of Investment Act"
        ],
        "key_sections": {
            "Land (Restrictions on Alienation) Act": [
                "Section 2 - 100% tax imposition",
                "Section 3 - Exemptions",
                "Section 5 - Company shareholding rules"
            ]
        },
        "concepts": [
            "foreign ownership", "100% tax", "condominium exemption",
            "BOI exemption", "company ownership", "beneficial ownership",
            "residential status", "dual citizenship"
        ],
        "related_forms": ["BOI agreement", "condominium deed"],
        "common_issues": [
            "defining 'foreigner'", "company structures", "trust arrangements",
            "nominee agreements", "tax calculation"
        ]
    },
    "inheritance": {
        "name": "Inheritance and Succession",
        "statutes": [
            "Intestate Succession Ordinance",
            "Wills Ordinance",
            "Kandyan Law",
            "Thesawalamai",
            "Muslim Law"
        ],
        "key_sections": {
            "Intestate Succession Ordinance": [
                "Section 2 - Applicable law",
                "Section 14 - Surviving spouse rights",
                "Section 15 - Children's shares"
            ],
            "Wills Ordinance": [
                "Section 4 - Capacity to make will",
                "Section 7 - Execution requirements"
            ]
        },
        "concepts": [
            "intestate succession", "testamentary succession", "legitim",
            "probate", "letters of administration", "executor", "administrator",
            "specific legacy", "residuary estate", "codicil"
        ],
        "related_forms": ["last will", "probate petition", "administration petition"],
        "common_issues": [
            "proving death", "missing heirs", "will challenges",
            "personal law determination", "foreign assets"
        ]
    },
    "easements": {
        "name": "Easements and Servitudes",
        "statutes": ["Civil Procedure Code", "Prescription Ordinance"],
        "key_sections": {},
        "concepts": [
            "easement", "servitude", "right of way", "light and air",
            "dominant tenement", "servient tenement", "grant", "prescription",
            "necessity", "apparent", "continuous"
        ],
        "related_forms": ["easement deed", "right of way agreement"],
        "common_issues": [
            "access disputes", "blocking easements", "excessive use",
            "abandonment", "landlocked parcels"
        ]
    },
    "encumbrances": {
        "name": "Encumbrances and Liens",
        "statutes": ["Registration of Documents Ordinance"],
        "key_sections": {},
        "concepts": [
            "encumbrance", "lien", "charge", "lis pendens", "caveat",
            "encumbrance certificate", "search report", "title search"
        ],
        "related_forms": ["encumbrance certificate", "search report"],
        "common_issues": [
            "hidden encumbrances", "priority disputes", "clearing title",
            "encumbrance certificate errors"
        ]
    },
    "contracts_property": {
        "name": "Contracts Related to Property",
        "statutes": ["Prevention of Frauds Ordinance", "Contract Law"],
        "key_sections": {},
        "concepts": [
            "sale agreement", "promise to sell", "specific performance",
            "earnest money", "breach", "rescission", "frustration"
        ],
        "related_forms": ["agreement of sale", "MOU"],
        "common_issues": [
            "agreement vs deed", "conditional sales", "time essence",
            "part performance", "oral agreements"
        ]
    }
}

# =============================================================================
# EXPANDED SEED QUESTIONS - 10x MORE PER TOPIC
# =============================================================================

SEED_QUESTIONS = {
    "property_transfer": [
        # Basic
        "What are the legal requirements for a valid property transfer in Sri Lanka?",
        "What happens if a deed is not registered?",
        "Who can attest a property deed in Sri Lanka?",
        "What is the difference between a sale deed and a gift deed?",
        "Can a property transfer be done without a notary?",
        "What documents are needed for property transfer?",
        "How long do you have to register a deed after execution?",
        "What is the effect of an unregistered deed?",
        # Intermediate
        "What is the Prevention of Frauds Ordinance and how does it affect property transfers?",
        "Can a minor transfer property in Sri Lanka?",
        "What is the role of witnesses in a property deed?",
        "How does stamp duty apply to property transfers?",
        "What is the difference between execution and registration of a deed?",
        "Can a deed be registered in any Land Registry office?",
        "What happens if there is an error in a registered deed?",
        "Can a deed be cancelled after registration?",
        # Advanced
        "What are the legal consequences of a forged deed in Sri Lanka?",
        "How does the doctrine of part performance apply to property contracts?",
        "What remedies are available for a breach of agreement to sell?",
        "How do you verify the chain of title for a property?",
        "What is the effect of subsequent sale to a bona fide purchaser?",
        "Can an unregistered deed prevail over a registered deed?",
        "What are the special requirements for gifting ancestral property?",
        "How does death of vendor affect an uncompleted sale?",
        # Practical scenarios
        "A vendor dies after signing but before registration - what happens?",
        "Two people claim ownership based on different deeds - who wins?",
        "Can property be transferred to a trust in Sri Lanka?",
        "What happens if stamp duty is not paid on a deed?",
        "Can a power of attorney holder execute a property deed?",
        "What is the procedure for correcting a deed error?",
    ],
    "title_registration": [
        # Basic
        "What is Bim Saviya and how does it work?",
        "What is the difference between deeds registration and title registration?",
        "What is a First Class Title under the Registration of Title Act?",
        "How can a Second Class Title be converted to First Class?",
        "What are the benefits of title registration?",
        "Is title registration mandatory in Sri Lanka?",
        "What is a cadastral map?",
        # Intermediate
        "What is the meaning of indefeasible title?",
        "What is a caveat and when should it be lodged?",
        "How does title registration protect against fraud?",
        "What happens to existing deeds when title registration is implemented?",
        "Can title registration be challenged in court?",
        "What is the role of the Registrar of Titles?",
        "How are boundaries determined in title registration?",
        "What is a priority notice?",
        # Advanced
        "What are the exceptions to indefeasibility of title?",
        "How does fraud affect a registered title?",
        "Can adverse possession defeat a registered title?",
        "What compensation is available for errors in title registration?",
        "How are overriding interests treated in title registration?",
        "What is the mirror principle in title registration?",
        "How does title registration affect existing encumbrances?",
        "What happens when cadastral survey reveals boundary errors?",
        # Practical
        "My neighbor's building encroaches after title registration - what can I do?",
        "How do I object to someone else's title registration application?",
        "Can I register a caveat to protect an unregistered interest?",
        "What documents do I need for first registration of title?",
    ],
    "prescription": [
        # Basic
        "How can someone acquire land through prescription in Sri Lanka?",
        "What is the time period for acquisitive prescription?",
        "What does 'nec vi, nec clam, nec precario' mean?",
        "Can prescription run against state land?",
        "What interrupts the running of prescription?",
        "Is a prescriptive title as good as a deed-based title?",
        # Intermediate
        "Can a tenant claim prescriptive title?",
        "What is the difference between acquisitive and extinctive prescription?",
        "How does acknowledgment affect prescription?",
        "Can prescription run between co-owners?",
        "What is the effect of disability on prescription?",
        "How do you prove 10 years of adverse possession?",
        "Can you add your predecessor's possession to your own (tacking)?",
        "What is the role of animus possidendi in prescription?",
        # Advanced
        "How does prescription apply to servitudes and easements?",
        "What is the effect of registered title on prescriptive claims?",
        "Can prescription defeat a mortgage?",
        "How do personal laws affect prescriptive rights?",
        "What is the effect of partition on prescriptive possession?",
        "Can a prescriptive title be registered?",
        "How does prescription apply to temple and religious land?",
        # Practical scenarios
        "I've occupied vacant land for 12 years - do I own it now?",
        "The true owner was abroad for 10 years - does prescription still apply?",
        "Can I claim prescription over land I used with owner's verbal permission?",
        "My fence has been in the wrong place for 15 years - what are my rights?",
        "How do I file a case to establish prescriptive title?",
    ],
    "partition": [
        # Basic
        "What is a partition action and who can file one?",
        "Can the court order sale instead of physical partition?",
        "What is an interlocutory decree in partition?",
        "How are shares determined in a partition action?",
        "Can a minority shareholder force partition?",
        "What happens to encumbrances in a partition?",
        # Intermediate
        "What is the difference between interlocutory and final decree?",
        "Can partition be appealed?",
        "How are buildings allocated in partition?",
        "What is the role of a commissioner in partition?",
        "Can partition action be withdrawn?",
        "How long does a partition case typically take?",
        "What happens if some co-owners cannot be found?",
        "Can undivided shares be sold before partition?",
        # Advanced
        "What is the res judicata effect of a partition decree?",
        "How does partition affect leases and tenancies?",
        "Can a court refuse to order partition?",
        "What are the grounds for setting aside a partition decree?",
        "How does prescription interact with partition?",
        "Can a partition decree be reopened for fraud?",
        "What happens to rights of way in partition?",
        # Practical
        "Three siblings inherited land but one refuses to partition - what can be done?",
        "Can I buy another co-owner's share before partition is complete?",
        "The property has a building - how will it be divided?",
        "One co-owner has been in exclusive possession - how does this affect shares?",
        "Can improvements by one co-owner be compensated in partition?",
    ],
    "mortgage": [
        # Basic
        "What is the difference between primary and secondary mortgage?",
        "What is parate execution?",
        "Can a bank sell mortgaged property without going to court?",
        "What is the equity of redemption?",
        "What happens if the mortgagor defaults?",
        "Can a mortgagor sell the mortgaged property?",
        # Intermediate
        "What notice is required before parate execution?",
        "How is surplus from mortgage sale distributed?",
        "What is marshalling of securities?",
        "Can a mortgagee take possession of mortgaged property?",
        "What are the mortgagor's rights during foreclosure?",
        "How does death of mortgagor affect the mortgage?",
        "Can a third party redeem a mortgage?",
        "What is a clog on the equity of redemption?",
        # Advanced
        "How do priority rules work between multiple mortgages?",
        "What is the effect of registration on mortgage priority?",
        "Can mortgage conditions be considered unconscionable?",
        "How does insolvency affect mortgage rights?",
        "What remedies are available against wrongful parate execution?",
        "How does time limitation apply to mortgage enforcement?",
        "Can a mortgagee be held liable for selling at undervalue?",
        # Practical
        "The bank wants to sell my property - can I stop them?",
        "I want to pay off mortgage early - can the bank refuse?",
        "Can I mortgage property that is already under a primary mortgage?",
        "The property sold for more than the debt - who gets the surplus?",
        "Can I negotiate with the bank after receiving parate execution notice?",
    ],
    "lease_tenancy": [
        # Basic
        "Who is a protected tenant under the Rent Act?",
        "What are the grounds for ejectment under the Rent Act?",
        "Can a landlord increase rent freely?",
        "What rights does a tenant have?",
        "Can a lease be terminated before the end of the term?",
        "What is the difference between a lease and a tenancy?",
        # Intermediate
        "When does the Rent Act apply?",
        "Can a landlord evict for personal use?",
        "What is key money and is it legal?",
        "Can a tenant make alterations to the premises?",
        "What happens when the landlord sells the property?",
        "Can a tenant assign or sublet?",
        "What is holding over and its consequences?",
        "How is authorized rent calculated?",
        # Advanced
        "What is the effect of the Rent Act on new buildings?",
        "How do personal laws affect tenancy succession?",
        "Can a lease be specifically enforced?",
        "What remedies are available for illegal ejectment?",
        "How does the Rent Act interact with mortgage foreclosure?",
        "What is the status of informal tenancy arrangements?",
        "Can business goodwill compensation be claimed by tenants?",
        # Practical
        "My landlord wants me to leave for renovation - do I have to?",
        "The tenant hasn't paid rent for 6 months - can I evict?",
        "Can I charge market rent for a commercial property?",
        "The tenant has died - can family members continue occupying?",
        "Is a verbal tenancy agreement enforceable?",
    ],
    "state_land": [
        # Basic
        "How is state land alienated in Sri Lanka?",
        "What is the difference between a permit and a grant?",
        "Can state land be sold by the permit holder?",
        "What are the succession rules for permit land?",
        "Can state land be mortgaged?",
        # Intermediate
        "What conditions apply to LDO permits?",
        "Can a permit be cancelled? On what grounds?",
        "What is the difference between alienation and regularization?",
        "How are encroachments on state land handled?",
        "Can state land be leased?",
        "What is the Jayabhoomi program?",
        "How do you convert a permit to a grant?",
        # Advanced
        "What are the inheritance rules for different types of state land permits?",
        "How does the Land Development Ordinance interact with succession laws?",
        "Can prescription run against state land?",
        "What happens to state land permits on death without nominated successor?",
        "How are disputes over state land boundaries resolved?",
        "What is the legal status of unauthorized constructions on state land?",
        # Practical
        "My father had an LDO permit - how do I transfer it to my name?",
        "Can I build a permanent structure on permit land?",
        "The government wants to take back my permit land - what are my rights?",
        "Can I subdivide permit land among my children?",
        "What happens if permit conditions are violated?",
    ],
    "foreign_ownership": [
        # Basic
        "Can foreigners buy land in Sri Lanka?",
        "What is the 100% tax on foreign land ownership?",
        "Can foreigners own apartments in Sri Lanka?",
        "Are there any exemptions for foreign ownership restrictions?",
        "Can a company with foreign shareholders own land?",
        # Intermediate
        "What is the difference in rules for land vs condominiums?",
        "How does the BOI exemption work?",
        "What percentage of foreign ownership triggers the restrictions?",
        "Can a dual citizen be treated as a foreigner for land ownership?",
        "What about land inherited by a foreigner?",
        "Can foreigners lease land long-term?",
        # Advanced
        "How are trust arrangements with foreign beneficiaries treated?",
        "What is the effect of nominee agreements for foreign buyers?",
        "How do the restrictions apply to companies with indirect foreign ownership?",
        "Can the 100% tax be avoided through corporate structuring?",
        "What due diligence should be done for foreign investment in property?",
        "How do bilateral investment treaties affect foreign land ownership?",
        # Practical
        "I'm a Sri Lankan living abroad - am I considered a foreigner?",
        "Can my foreign spouse own property jointly with me?",
        "I want to buy land through my Sri Lankan relative - is this legal?",
        "What happens if a company becomes foreign-owned after buying land?",
        "Can a foreign company own commercial property?",
    ],
    "inheritance": [
        # Basic
        "How is property inherited in Sri Lanka?",
        "What is the difference between testate and intestate succession?",
        "Do I need probate to inherit property?",
        "Can I disinherit my children in Sri Lanka?",
        "What is the legitim?",
        # Intermediate
        "How do personal laws affect inheritance?",
        "What are the intestate succession shares for spouse and children?",
        "Can a will be contested? On what grounds?",
        "What is the procedure for obtaining probate?",
        "How is property transferred after probate?",
        "What are the executor's duties?",
        "Can joint property be inherited separately?",
        # Advanced
        "How does Kandyan Law affect property inheritance?",
        "What are Thesawalamai restrictions on property rights?",
        "How does Muslim law affect inheritance of property?",
        "Can a testator give everything to charity?",
        "What is the doctrine of election in inheritance?",
        "How are debts of the deceased handled against inherited property?",
        # Practical
        "My father died without a will - how do we divide the house?",
        "The will says property goes to one child only - is this valid?",
        "How do I transfer the deed to my name after inheriting?",
        "What if there are multiple wills?",
        "Can a deed transfer be registered based on a will without probate?",
    ],
    "easements": [
        # Basic
        "What is an easement?",
        "How is a right of way created?",
        "Can an easement be terminated?",
        "What is the difference between dominant and servient tenement?",
        # Intermediate
        "Can easements be acquired by prescription?",
        "What is an easement of necessity?",
        "Can the scope of an easement be expanded?",
        "How do you register an easement?",
        "What happens to easements when property is sold?",
        # Advanced
        "How does partition affect existing easements?",
        "Can an easement be abandoned?",
        "What remedies exist for interference with easements?",
        "How are disputes over easement location resolved?",
        # Practical
        "My neighbor blocked my access road - what can I do?",
        "I bought land with no road access - what are my rights?",
        "Can I use a wider vehicle than the original right of way allowed?",
        "The servient land was sold - does my easement continue?",
    ],
}

# =============================================================================
# QUESTION VARIATION TEMPLATES
# =============================================================================

QUESTION_VARIATIONS = {
    "rephrase": [
        "In Sri Lanka, {core_question}",
        "Under Sri Lankan law, {core_question}",
        "According to Sri Lankan property law, {core_question}",
        "What is the legal position regarding {topic_description}?",
        "How does the law deal with {topic_description}?",
        "Could you explain {topic_description}?",
        "Please clarify {topic_description}",
        "What are the rules governing {topic_description}?",
    ],
    "scenario_prefix": [
        "If someone wants to {action}, what must they do?",
        "A person is trying to {action}. What legal requirements apply?",
        "Consider a situation where {scenario}. What is the legal outcome?",
        "Suppose {scenario}. How would the law apply?",
        "Imagine {scenario}. What would be the legal consequence?",
    ],
    "difficulty_modifiers": {
        "basic": [
            "What is {concept}?",
            "Define {concept}",
            "Explain {concept} simply",
            "What does {concept} mean in property law?",
        ],
        "intermediate": [
            "How does {concept} work in practice?",
            "What are the requirements for {concept}?",
            "Explain the procedure for {concept}",
            "What conditions must be met for {concept}?",
        ],
        "advanced": [
            "What are the exceptions to {concept}?",
            "How do courts interpret {concept} in complex cases?",
            "What happens when {concept} conflicts with {related_concept}?",
            "Analyze the legal implications of {concept} in edge cases",
        ]
    }
}

# =============================================================================
# MULTI-TURN CONVERSATION TEMPLATES
# =============================================================================

CONVERSATION_TEMPLATES = [
    {
        "name": "clarification_flow",
        "turns": [
            {"role": "user", "content": "{initial_question}"},
            {"role": "assistant", "content": "{initial_answer}"},
            {"role": "user", "content": "Can you explain that in simpler terms?"},
            {"role": "assistant", "content": "{simplified_answer}"},
        ]
    },
    {
        "name": "follow_up_flow",
        "turns": [
            {"role": "user", "content": "{initial_question}"},
            {"role": "assistant", "content": "{initial_answer}"},
            {"role": "user", "content": "What if {follow_up_scenario}?"},
            {"role": "assistant", "content": "{follow_up_answer}"},
        ]
    },
    {
        "name": "example_request_flow",
        "turns": [
            {"role": "user", "content": "{initial_question}"},
            {"role": "assistant", "content": "{initial_answer}"},
            {"role": "user", "content": "Can you give me a practical example?"},
            {"role": "assistant", "content": "{example_answer}"},
        ]
    },
    {
        "name": "deep_dive_flow",
        "turns": [
            {"role": "user", "content": "{initial_question}"},
            {"role": "assistant", "content": "{initial_answer}"},
            {"role": "user", "content": "What statute governs this?"},
            {"role": "assistant", "content": "{statute_answer}"},
            {"role": "user", "content": "What are the relevant sections?"},
            {"role": "assistant", "content": "{sections_answer}"},
        ]
    },
    {
        "name": "comparison_flow",
        "turns": [
            {"role": "user", "content": "{initial_question}"},
            {"role": "assistant", "content": "{initial_answer}"},
            {"role": "user", "content": "How is this different from {related_topic}?"},
            {"role": "assistant", "content": "{comparison_answer}"},
        ]
    }
]

# =============================================================================
# CASE STUDY TEMPLATES
# =============================================================================

CASE_STUDY_TEMPLATES = [
    {
        "type": "dispute_resolution",
        "template": """
Case Study: {title}

FACTS:
{facts}

PARTIES:
- Plaintiff/Applicant: {plaintiff}
- Defendant/Respondent: {defendant}

ISSUES:
{issues}

APPLICABLE LAW:
{applicable_law}

ANALYSIS:
{analysis}

OUTCOME:
{outcome}

KEY TAKEAWAYS:
{takeaways}
"""
    },
    {
        "type": "transaction_advisory",
        "template": """
Case Study: {title}

CLIENT PROFILE:
{client_profile}

OBJECTIVE:
{objective}

FACTS:
{facts}

LEGAL CONSIDERATIONS:
{legal_considerations}

RECOMMENDED APPROACH:
{recommendation}

DOCUMENTS REQUIRED:
{documents}

RISKS AND MITIGATION:
{risks}
"""
    },
    {
        "type": "compliance_check",
        "template": """
Case Study: {title}

SITUATION:
{situation}

COMPLIANCE CHECKLIST:
{checklist}

DEFICIENCIES IDENTIFIED:
{deficiencies}

REMEDIATION STEPS:
{remediation}

TIMELINE:
{timeline}
"""
    }
]


# =============================================================================
# ENHANCED GENERATOR CLASS
# =============================================================================

class EnhancedLegalReasoningGenerator:
    """Enhanced generator with multiple data generation strategies."""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.generated_count = 0
        self.cache = {}
        
    def _call_api(self, prompt: str, system_prompt: str, 
                  model: str = MODEL, temperature: float = 0.3,
                  max_tokens: int = 2000) -> Optional[str]:
        """Thread-safe API call with caching."""
        
        cache_key = hashlib.md5(f"{prompt}{system_prompt}".encode()).hexdigest()
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        with api_lock:
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                content = response.choices[0].message.content.strip()
                
                # Clean JSON response
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                content = content.strip()
                
                self.cache[cache_key] = content
                self.generated_count += 1
                return content
                
            except Exception as e:
                print(f"    ⚠ API error: {e}")
                return None

    def generate_reasoning_data(self, question: str, topic_key: str) -> Optional[Dict]:
        """Generate complete reasoning data with enhanced structure."""
        
        topic_info = LEGAL_TOPICS.get(topic_key, {})
        statutes = topic_info.get("statutes", [])
        concepts = topic_info.get("concepts", [])
        common_issues = topic_info.get("common_issues", [])
        
        prompt = f"""You are a Sri Lankan property law expert. Generate a comprehensive legal reasoning dataset entry.

QUESTION: {question}

TOPIC: {topic_info.get('name', topic_key)}
RELEVANT STATUTES: {', '.join(statutes)}
KEY CONCEPTS: {', '.join(concepts)}
COMMON ISSUES: {', '.join(common_issues)}

Generate a JSON response with this EXACT structure:
{{
    "question": "{question}",
    "short_answer": "A concise 1-2 sentence answer",
    "detailed_answer": "A comprehensive 3-5 sentence answer with more detail",
    "reasoning_chain": [
        {{
            "step_number": 1,
            "action": "What legal analysis step is being taken",
            "legal_basis": "The statute, section, or principle being applied",
            "result": "What this step determines or establishes",
            "confidence": "high/medium/low"
        }}
        // Include 4-6 logical steps
    ],
    "irac_analysis": {{
        "issue": "The precise legal question to be resolved",
        "rule": "The applicable legal rules with specific statute citations",
        "application": "Detailed application of rules to the situation",
        "conclusion": "The legal conclusion with any qualifications"
    }},
    "legal_references": [
        {{
            "statute": "Name of the Act/Ordinance",
            "section": "Specific section number",
            "relevance": "Why this section is relevant",
            "quote": "Key text from the section (if known)",
            "interpretation": "How courts have interpreted this"
        }}
    ],
    "example_scenarios": [
        {{
            "facts": "A practical example scenario (2-3 sentences)",
            "analysis": "How the law applies to this scenario",
            "outcome": "The legal outcome"
        }},
        {{
            "facts": "A contrasting scenario showing different outcome",
            "analysis": "Why the law applies differently here",
            "outcome": "The different legal outcome"
        }}
    ],
    "common_mistakes": [
        "Mistake 1 people commonly make regarding this topic",
        "Mistake 2"
    ],
    "practical_tips": [
        "Practical tip 1 for someone dealing with this issue",
        "Practical tip 2"
    ],
    "related_questions": [
        "A related question the user might also want to know",
        "Another related question"
    ],
    "keywords": ["list", "of", "relevant", "legal", "terms"],
    "difficulty": "basic/intermediate/advanced",
    "estimated_reading_time": "X minutes"
}}

IMPORTANT:
- Base answers on actual Sri Lankan law
- Include specific statute names and section numbers
- Make reasoning steps logical and sequential
- Ensure example scenarios are realistic and contrasting
- Return ONLY valid JSON, no markdown formatting"""

        system_prompt = """You are a Sri Lankan property law expert specializing in legal education. 
You provide accurate, well-structured legal information based on Sri Lankan statutes and case law.
Always respond with valid JSON only, no additional text or formatting."""

        content = self._call_api(prompt, system_prompt)
        
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                print(f"    ⚠ JSON parse error: {e}")
        return None

    def generate_question_variations(self, base_question: str, topic_key: str, 
                                    num_variations: int = 5) -> List[str]:
        """Generate variations of a question for data augmentation."""
        
        topic_info = LEGAL_TOPICS.get(topic_key, {})
        
        prompt = f"""Generate {num_variations} different ways to ask the same legal question.
Each variation should maintain the same legal meaning but use different wording.

ORIGINAL QUESTION: {base_question}
TOPIC: {topic_info.get('name', topic_key)}

Generate variations that:
1. Use different phrasing (formal/informal)
2. Add context (scenario-based)
3. Focus on different aspects (procedural/substantive)
4. Target different audiences (lawyer/layperson)
5. Include regional terms where appropriate

Return a JSON array of strings:
["variation 1", "variation 2", ...]"""

        system_prompt = "You are a legal language expert. Return only valid JSON array."
        
        content = self._call_api(prompt, system_prompt, model=FAST_MODEL, temperature=0.7)
        
        if content:
            try:
                return json.loads(content)
            except:
                pass
        return []

    def generate_multi_turn_conversation(self, topic_key: str, 
                                         template_name: str = "follow_up_flow") -> Optional[Dict]:
        """Generate a multi-turn conversation for chat training."""
        
        topic_info = LEGAL_TOPICS.get(topic_key, {})
        questions = SEED_QUESTIONS.get(topic_key, [])
        
        if not questions:
            return None
            
        initial_question = random.choice(questions)
        
        prompt = f"""Generate a multi-turn legal consultation conversation about Sri Lankan property law.

TOPIC: {topic_info.get('name', topic_key)}
INITIAL QUESTION: {initial_question}
CONVERSATION TYPE: {template_name}

Generate a realistic conversation where:
1. User asks the initial question
2. Assistant provides a helpful, accurate answer
3. User asks follow-up questions
4. Assistant provides increasingly specific information
5. Include at least 4-6 turns total

Return JSON:
{{
    "conversation_id": "unique_id",
    "topic": "{topic_key}",
    "turns": [
        {{"role": "user", "content": "..."}},
        {{"role": "assistant", "content": "...", "references": ["statute citations"]}},
        ...
    ],
    "summary": "Brief summary of what was discussed",
    "key_legal_points": ["point 1", "point 2"]
}}"""

        system_prompt = """You are simulating a legal consultation conversation.
The assistant should be knowledgeable, helpful, and cite relevant Sri Lankan law.
Return only valid JSON."""

        content = self._call_api(prompt, system_prompt, temperature=0.5, max_tokens=3000)
        
        if content:
            try:
                return json.loads(content)
            except:
                pass
        return None

    def generate_case_study(self, topic_key: str, case_type: str = "dispute_resolution") -> Optional[Dict]:
        """Generate a detailed case study for training."""
        
        topic_info = LEGAL_TOPICS.get(topic_key, {})
        
        prompt = f"""Generate a detailed, realistic legal case study for Sri Lankan property law.

TOPIC: {topic_info.get('name', topic_key)}
CASE TYPE: {case_type}
RELEVANT STATUTES: {', '.join(topic_info.get('statutes', []))}
COMMON ISSUES: {', '.join(topic_info.get('common_issues', []))}

Generate a comprehensive case study with:
1. Realistic Sri Lankan names and locations
2. Specific property descriptions (A-R-P format)
3. Relevant dates and timelines
4. Multiple legal issues intertwined
5. Step-by-step legal analysis
6. Clear outcome with reasoning

Return JSON:
{{
    "case_id": "unique_id",
    "title": "Descriptive case title",
    "type": "{case_type}",
    "topic": "{topic_key}",
    "difficulty": "basic/intermediate/advanced",
    "facts": {{
        "parties": [{{"name": "...", "role": "...", "description": "..."}}],
        "property": {{"description": "...", "extent": "A-R-P", "location": "..."}},
        "timeline": [{{"date": "...", "event": "..."}}],
        "dispute": "Description of the core dispute"
    }},
    "legal_issues": [
        {{"issue": "...", "relevant_law": "...", "analysis": "..."}}
    ],
    "arguments": {{
        "plaintiff": ["argument 1", "argument 2"],
        "defendant": ["counter-argument 1", "counter-argument 2"]
    }},
    "outcome": {{
        "decision": "...",
        "reasoning": "...",
        "orders": ["order 1", "order 2"]
    }},
    "lessons": ["lesson 1", "lesson 2"],
    "qa_pairs": [
        {{"question": "Question about this case", "answer": "Answer based on case facts"}}
    ]
}}"""

        system_prompt = """You are a Sri Lankan property law expert creating educational case studies.
Make cases realistic with proper legal terminology and accurate law application.
Return only valid JSON."""

        content = self._call_api(prompt, system_prompt, temperature=0.6, max_tokens=4000)
        
        if content:
            try:
                return json.loads(content)
            except:
                pass
        return None

    def generate_comparison_pair(self, topic1: str, topic2: str) -> Optional[Dict]:
        """Generate comparison training data between two related topics."""
        
        topic1_info = LEGAL_TOPICS.get(topic1, {})
        topic2_info = LEGAL_TOPICS.get(topic2, {})
        
        prompt = f"""Generate a detailed comparison between two related property law topics.

TOPIC 1: {topic1_info.get('name', topic1)}
TOPIC 2: {topic2_info.get('name', topic2)}

Create a comprehensive comparison covering:
1. Key differences in legal requirements
2. Procedural differences
3. When to use which
4. Common confusion points
5. Practical implications

Return JSON:
{{
    "comparison_id": "unique_id",
    "topics": ["{topic1}", "{topic2}"],
    "question": "What is the difference between {topic1_info.get('name', topic1)} and {topic2_info.get('name', topic2)}?",
    "summary": "Brief summary of key differences",
    "detailed_comparison": {{
        "definition": {{"topic1": "...", "topic2": "..."}},
        "legal_basis": {{"topic1": "...", "topic2": "..."}},
        "procedure": {{"topic1": "...", "topic2": "..."}},
        "time_requirements": {{"topic1": "...", "topic2": "..."}},
        "cost": {{"topic1": "...", "topic2": "..."}},
        "effect": {{"topic1": "...", "topic2": "..."}}
    }},
    "when_to_use": {{
        "use_topic1_when": ["condition 1", "condition 2"],
        "use_topic2_when": ["condition 1", "condition 2"]
    }},
    "common_mistakes": ["mistake 1", "mistake 2"],
    "example_scenario": {{
        "facts": "Scenario where choice matters",
        "analysis": "Why one is better than the other here",
        "recommendation": "Which to use and why"
    }}
}}"""

        system_prompt = """You are a Sri Lankan property law expert creating comparison guides.
Be precise about legal distinctions. Return only valid JSON."""

        content = self._call_api(prompt, system_prompt, temperature=0.4)
        
        if content:
            try:
                return json.loads(content)
            except:
                pass
        return None

    def generate_error_correction_pair(self, topic_key: str) -> Optional[Dict]:
        """Generate incorrect answer + correction for training."""
        
        topic_info = LEGAL_TOPICS.get(topic_key, {})
        questions = SEED_QUESTIONS.get(topic_key, [])
        
        if not questions:
            return None
            
        question = random.choice(questions)
        
        prompt = f"""Generate an error correction training pair for legal education.

TOPIC: {topic_info.get('name', topic_key)}
QUESTION: {question}

Generate:
1. A plausible but INCORRECT answer (containing common misconceptions)
2. The CORRECT answer with explanation of errors

Return JSON:
{{
    "question": "{question}",
    "incorrect_answer": {{
        "content": "The wrong answer with subtle errors",
        "errors": ["specific error 1", "specific error 2"]
    }},
    "correct_answer": {{
        "content": "The correct, accurate answer",
        "corrections": [
            {{"error": "what was wrong", "correction": "what is correct", "explanation": "why"}}
        ]
    }},
    "learning_points": ["key takeaway 1", "key takeaway 2"],
    "references": ["relevant statute or case"]
}}"""

        system_prompt = """You are a Sri Lankan property law expert creating error correction exercises.
Make errors realistic (common misconceptions) but clearly incorrect.
Return only valid JSON."""

        content = self._call_api(prompt, system_prompt, model=FAST_MODEL, temperature=0.5)
        
        if content:
            try:
                return json.loads(content)
            except:
                pass
        return None

    def generate_decision_tree(self, topic_key: str) -> Optional[Dict]:
        """Generate an enhanced decision tree for legal reasoning."""
        
        topic_info = LEGAL_TOPICS.get(topic_key, {})
        
        prompt = f"""Create a comprehensive legal decision tree for Sri Lankan property law.

TOPIC: {topic_info.get('name', topic_key)}
STATUTES: {', '.join(topic_info.get('statutes', []))}
COMMON ISSUES: {', '.join(topic_info.get('common_issues', []))}

Generate a decision tree that:
1. Starts with the most fundamental question
2. Branches based on yes/no or multiple choice
3. Includes 8-12 decision nodes
4. Each path leads to a clear legal conclusion
5. Cites relevant law at each node

Return JSON:
{{
    "tree_id": "unique_id",
    "topic": "{topic_key}",
    "topic_name": "{topic_info.get('name', topic_key)}",
    "purpose": "What this decision tree helps determine",
    "entry_question": "The main question being answered",
    "nodes": {{
        "start": {{
            "id": "start",
            "question": "First question",
            "type": "yes_no",
            "yes_path": "node_id",
            "no_path": "node_id or OUTCOME:outcome_id",
            "legal_basis": "Relevant law citation",
            "explanation": "Why this question matters"
        }},
        "node_2": {{
            "id": "node_2",
            "question": "Next question",
            "type": "yes_no",
            "yes_path": "...",
            "no_path": "...",
            "legal_basis": "...",
            "explanation": "..."
        }}
    }},
    "outcomes": {{
        "outcome_1": {{
            "id": "outcome_1",
            "result": "Clear legal conclusion",
            "explanation": "Detailed reasoning",
            "next_steps": ["step 1", "step 2"],
            "documents_needed": ["doc 1", "doc 2"],
            "estimated_time": "X weeks/months",
            "estimated_cost": "approximate range"
        }}
    }},
    "usage_notes": "How to use this decision tree effectively"
}}"""

        system_prompt = """You are a Sri Lankan property law expert creating decision trees.
Make trees comprehensive, accurate, and practically useful.
Return only valid JSON."""

        content = self._call_api(prompt, system_prompt, max_tokens=3000)
        
        if content:
            try:
                return json.loads(content)
            except:
                pass
        return None

    def generate_from_legal_text(self, text: str, source: str, topic_key: str) -> Optional[List[Dict]]:
        """Generate Q&A pairs from actual legal text (downloaded laws)."""
        
        # Truncate if too long
        if len(text) > 8000:
            text = text[:8000] + "..."
        
        prompt = f"""Analyze this Sri Lankan legal text and generate training Q&A pairs.

SOURCE: {source}
TOPIC: {topic_key}

LEGAL TEXT:
{text}

Generate 5-10 Q&A pairs based on this text:
1. Questions should be what a layperson might ask
2. Answers should accurately reflect the law
3. Include section references where applicable
4. Vary difficulty (basic to advanced)

Return JSON:
{{
    "source": "{source}",
    "qa_pairs": [
        {{
            "question": "A natural question about this law",
            "answer": "Accurate answer based on the text",
            "section_reference": "Section X if applicable",
            "difficulty": "basic/intermediate/advanced",
            "keywords": ["relevant", "keywords"]
        }}
    ]
}}"""

        system_prompt = """You are a legal educator analyzing Sri Lankan statutes.
Generate accurate, educational Q&A pairs. Return only valid JSON."""

        content = self._call_api(prompt, system_prompt, model=FAST_MODEL, max_tokens=2000)
        
        if content:
            try:
                data = json.loads(content)
                return data.get("qa_pairs", [])
            except:
                pass
        return None


# =============================================================================
# DATASET BUILDER CLASS
# =============================================================================

class EnhancedDatasetBuilder:
    """Builds massive training datasets with multiple strategies."""
    
    def __init__(self, api_key: str):
        self.generator = EnhancedLegalReasoningGenerator(api_key)
        self.dataset = {
            "metadata": {
                "name": "Sri Lankan Property Law Reasoning Dataset V2",
                "version": "2.0",
                "created_at": datetime.now().isoformat(),
                "description": "Enhanced dataset for LLM fine-tuning with multiple data types",
                "author": "LegalVision Project - S. Sivanuja",
                "topics": list(LEGAL_TOPICS.keys()),
                "data_types": [
                    "reasoning_entries", "conversations", "case_studies",
                    "comparisons", "error_corrections", "decision_trees",
                    "text_derived_qa"
                ]
            },
            "reasoning_entries": [],
            "conversations": [],
            "case_studies": [],
            "comparisons": [],
            "error_corrections": [],
            "decision_trees": [],
            "text_derived_qa": [],
            "statistics": {}
        }
        self.stats = {topic: {"generated": 0, "failed": 0} for topic in LEGAL_TOPICS}
        
    def build_full_dataset(self, 
                          entries_per_topic: int = 10,
                          variations_per_question: int = 3,
                          conversations_per_topic: int = 5,
                          case_studies_per_topic: int = 3,
                          include_comparisons: bool = True,
                          include_error_corrections: bool = True,
                          include_decision_trees: bool = True,
                          process_downloaded_laws: bool = True):
        """Build the complete enhanced dataset."""
        
        print("=" * 70)
        print("ENHANCED LEGAL REASONING DATASET GENERATOR V2")
        print("=" * 70)
        print(f"Model: {MODEL} (quality) / {FAST_MODEL} (bulk)")
        print(f"Topics: {len(LEGAL_TOPICS)}")
        print("-" * 70)
        print("Generation Plan:")
        print(f"  • Reasoning entries per topic: {entries_per_topic}")
        print(f"  • Question variations: {variations_per_question}")
        print(f"  • Conversations per topic: {conversations_per_topic}")
        print(f"  • Case studies per topic: {case_studies_per_topic}")
        print(f"  • Comparisons: {'Yes' if include_comparisons else 'No'}")
        print(f"  • Error corrections: {'Yes' if include_error_corrections else 'No'}")
        print(f"  • Decision trees: {'Yes' if include_decision_trees else 'No'}")
        print(f"  • Process downloaded laws: {'Yes' if process_downloaded_laws else 'No'}")
        print("-" * 70)
        
        entry_id = 1
        
        # 1. Generate main reasoning entries with variations
        print("\n📚 PHASE 1: Main Reasoning Entries")
        print("=" * 50)
        
        for topic_key, topic_info in LEGAL_TOPICS.items():
            print(f"\n🏷️  Topic: {topic_info['name']}")
            print("-" * 40)
            
            questions = SEED_QUESTIONS.get(topic_key, [])[:entries_per_topic]
            
            for i, question in enumerate(questions, 1):
                print(f"  [{i}/{len(questions)}] {question[:50]}...")
                
                # Generate main entry
                data = self.generator.generate_reasoning_data(question, topic_key)
                
                if data:
                    data["id"] = f"RE_{entry_id:05d}"
                    data["topic_key"] = topic_key
                    data["topic_name"] = topic_info["name"]
                    data["generated_at"] = datetime.now().isoformat()
                    data["source"] = "seed_question"
                    
                    self.dataset["reasoning_entries"].append(data)
                    self.stats[topic_key]["generated"] += 1
                    entry_id += 1
                    print(f"    ✓ Generated main entry")
                    
                    # Generate variations
                    if variations_per_question > 0:
                        variations = self.generator.generate_question_variations(
                            question, topic_key, variations_per_question
                        )
                        for var_q in variations:
                            var_data = self.generator.generate_reasoning_data(var_q, topic_key)
                            if var_data:
                                var_data["id"] = f"RE_{entry_id:05d}"
                                var_data["topic_key"] = topic_key
                                var_data["topic_name"] = topic_info["name"]
                                var_data["generated_at"] = datetime.now().isoformat()
                                var_data["source"] = "variation"
                                var_data["original_question"] = question
                                
                                self.dataset["reasoning_entries"].append(var_data)
                                self.stats[topic_key]["generated"] += 1
                                entry_id += 1
                        
                        print(f"    ✓ Generated {len(variations)} variations")
                else:
                    self.stats[topic_key]["failed"] += 1
                    print(f"    ✗ Failed")
                
                time.sleep(0.5)  # Rate limiting
        
        # 2. Generate multi-turn conversations
        print("\n💬 PHASE 2: Multi-turn Conversations")
        print("=" * 50)
        
        conv_id = 1
        conversation_types = ["follow_up_flow", "clarification_flow", "deep_dive_flow", 
                            "example_request_flow", "comparison_flow"]
        
        for topic_key, topic_info in LEGAL_TOPICS.items():
            print(f"\n🏷️  Topic: {topic_info['name']}")
            
            for i in range(conversations_per_topic):
                conv_type = conversation_types[i % len(conversation_types)]
                print(f"  [{i+1}/{conversations_per_topic}] Generating {conv_type}...")
                
                conv = self.generator.generate_multi_turn_conversation(topic_key, conv_type)
                
                if conv:
                    conv["id"] = f"CONV_{conv_id:05d}"
                    conv["generated_at"] = datetime.now().isoformat()
                    self.dataset["conversations"].append(conv)
                    conv_id += 1
                    print(f"    ✓ Generated")
                else:
                    print(f"    ✗ Failed")
                
                time.sleep(0.5)
        
        # 3. Generate case studies
        print("\n📋 PHASE 3: Case Studies")
        print("=" * 50)
        
        case_id = 1
        case_types = ["dispute_resolution", "transaction_advisory", "compliance_check"]
        
        for topic_key, topic_info in LEGAL_TOPICS.items():
            print(f"\n🏷️  Topic: {topic_info['name']}")
            
            for i in range(case_studies_per_topic):
                case_type = case_types[i % len(case_types)]
                print(f"  [{i+1}/{case_studies_per_topic}] Generating {case_type}...")
                
                case = self.generator.generate_case_study(topic_key, case_type)
                
                if case:
                    case["id"] = f"CASE_{case_id:05d}"
                    case["generated_at"] = datetime.now().isoformat()
                    self.dataset["case_studies"].append(case)
                    case_id += 1
                    print(f"    ✓ Generated")
                else:
                    print(f"    ✗ Failed")
                
                time.sleep(0.5)
        
        # 4. Generate comparisons between related topics
        if include_comparisons:
            print("\n⚖️  PHASE 4: Topic Comparisons")
            print("=" * 50)
            
            comparison_pairs = [
                ("property_transfer", "title_registration"),
                ("prescription", "property_transfer"),
                ("mortgage", "lease_tenancy"),
                ("partition", "inheritance"),
                ("state_land", "property_transfer"),
                ("easements", "encumbrances"),
            ]
            
            comp_id = 1
            for topic1, topic2 in comparison_pairs:
                if topic1 in LEGAL_TOPICS and topic2 in LEGAL_TOPICS:
                    print(f"  Comparing: {topic1} vs {topic2}...")
                    
                    comp = self.generator.generate_comparison_pair(topic1, topic2)
                    
                    if comp:
                        comp["id"] = f"COMP_{comp_id:05d}"
                        comp["generated_at"] = datetime.now().isoformat()
                        self.dataset["comparisons"].append(comp)
                        comp_id += 1
                        print(f"    ✓ Generated")
                    else:
                        print(f"    ✗ Failed")
                    
                    time.sleep(0.5)
        
        # 5. Generate error correction pairs
        if include_error_corrections:
            print("\n❌➡️✓ PHASE 5: Error Correction Pairs")
            print("=" * 50)
            
            err_id = 1
            errors_per_topic = 3
            
            for topic_key, topic_info in LEGAL_TOPICS.items():
                print(f"\n🏷️  Topic: {topic_info['name']}")
                
                for i in range(errors_per_topic):
                    print(f"  [{i+1}/{errors_per_topic}] Generating error pair...")
                    
                    err = self.generator.generate_error_correction_pair(topic_key)
                    
                    if err:
                        err["id"] = f"ERR_{err_id:05d}"
                        err["topic_key"] = topic_key
                        err["generated_at"] = datetime.now().isoformat()
                        self.dataset["error_corrections"].append(err)
                        err_id += 1
                        print(f"    ✓ Generated")
                    else:
                        print(f"    ✗ Failed")
                    
                    time.sleep(0.3)
        
        # 6. Generate decision trees
        if include_decision_trees:
            print("\n🌳 PHASE 6: Decision Trees")
            print("=" * 50)
            
            for topic_key, topic_info in LEGAL_TOPICS.items():
                print(f"  Generating tree for: {topic_info['name']}...")
                
                tree = self.generator.generate_decision_tree(topic_key)
                
                if tree:
                    tree["generated_at"] = datetime.now().isoformat()
                    self.dataset["decision_trees"].append(tree)
                    print(f"    ✓ Generated")
                else:
                    print(f"    ✗ Failed")
                
                time.sleep(0.5)
        
        # 7. Process downloaded law files
        if process_downloaded_laws and INPUT_DIR.exists():
            print("\n📜 PHASE 7: Processing Downloaded Laws")
            print("=" * 50)
            
            self._process_downloaded_laws()
        
        # Update metadata
        self._update_metadata()
        
        return self.dataset
    
    def _process_downloaded_laws(self):
        """Process downloaded law text files to generate Q&A pairs."""
        
        law_files = list(INPUT_DIR.glob("*.txt"))
        print(f"Found {len(law_files)} law files")
        
        # Map filenames to topics
        file_topic_map = {
            "prevention_of_frauds": "property_transfer",
            "registration_of_documents": "property_transfer",
            "notaries": "property_transfer",
            "registration_of_title": "title_registration",
            "prescription": "prescription",
            "partition": "partition",
            "mortgage": "mortgage",
            "rent_act": "lease_tenancy",
            "land_development": "state_land",
            "state_lands": "state_land",
            "land_acquisition": "state_land",
            "apartment_ownership": "foreign_ownership",
            "condominium": "foreign_ownership",
            "trust": "inheritance",
            "evidence": "property_transfer",
            "civil_procedure": "partition",
            "survey": "title_registration",
        }
        
        qa_id = 1
        for file_path in law_files:
            filename = file_path.stem.lower()
            
            # Determine topic
            topic_key = None
            for key_part, topic in file_topic_map.items():
                if key_part in filename:
                    topic_key = topic
                    break
            
            if not topic_key:
                topic_key = "property_transfer"  # default
            
            print(f"  Processing: {file_path.name} -> {topic_key}")
            
            try:
                text = file_path.read_text(encoding='utf-8')
                
                if len(text) < 500:
                    print(f"    ⚠ File too short, skipping")
                    continue
                
                qa_pairs = self.generator.generate_from_legal_text(
                    text, file_path.name, topic_key
                )
                
                if qa_pairs:
                    for qa in qa_pairs:
                        qa["id"] = f"TQA_{qa_id:05d}"
                        qa["source_file"] = file_path.name
                        qa["topic_key"] = topic_key
                        qa["generated_at"] = datetime.now().isoformat()
                        self.dataset["text_derived_qa"].append(qa)
                        qa_id += 1
                    
                    print(f"    ✓ Generated {len(qa_pairs)} Q&A pairs")
                else:
                    print(f"    ✗ No Q&A pairs generated")
                    
            except Exception as e:
                print(f"    ✗ Error: {e}")
            
            time.sleep(0.5)
    
    def _update_metadata(self):
        """Update dataset metadata with counts."""
        
        self.dataset["metadata"]["total_entries"] = {
            "reasoning_entries": len(self.dataset["reasoning_entries"]),
            "conversations": len(self.dataset["conversations"]),
            "case_studies": len(self.dataset["case_studies"]),
            "comparisons": len(self.dataset["comparisons"]),
            "error_corrections": len(self.dataset["error_corrections"]),
            "decision_trees": len(self.dataset["decision_trees"]),
            "text_derived_qa": len(self.dataset["text_derived_qa"]),
        }
        
        total = sum(self.dataset["metadata"]["total_entries"].values())
        self.dataset["metadata"]["grand_total"] = total
        self.dataset["statistics"] = self.stats
        self.dataset["metadata"]["completed_at"] = datetime.now().isoformat()
    
    def save_dataset(self, output_dir: Path = OUTPUT_DIR):
        """Save the dataset in multiple formats."""
        
        print("\n💾 SAVING DATASET")
        print("=" * 50)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Complete dataset
        complete_path = output_dir / "complete_dataset_v2.json"
        with open(complete_path, 'w', encoding='utf-8') as f:
            json.dump(self.dataset, f, indent=2, ensure_ascii=False)
        print(f"  ✓ Complete dataset: {complete_path}")
        
        # 2. Individual components
        for key in ["reasoning_entries", "conversations", "case_studies", 
                   "comparisons", "error_corrections", "decision_trees", "text_derived_qa"]:
            if self.dataset[key]:
                path = output_dir / f"{key}.json"
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(self.dataset[key], f, indent=2, ensure_ascii=False)
                print(f"  ✓ {key}: {path}")
        
        # 3. Fine-tuning formats
        self._save_finetuning_formats(output_dir)
        
        # 4. Statistics
        stats_path = output_dir / "generation_stats.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": self.dataset["metadata"],
                "statistics": self.stats
            }, f, indent=2)
        print(f"  ✓ Statistics: {stats_path}")
        
        print("\n" + "=" * 50)
        print("DATASET SUMMARY")
        print("=" * 50)
        for key, count in self.dataset["metadata"]["total_entries"].items():
            print(f"  {key}: {count}")
        print(f"  GRAND TOTAL: {self.dataset['metadata']['grand_total']}")
    
    def _save_finetuning_formats(self, output_dir: Path):
        """Save in various fine-tuning formats."""
        
        # 1. OpenAI JSONL format
        jsonl_path = output_dir / "finetuning_openai.jsonl"
        with open(jsonl_path, 'w', encoding='utf-8') as f:
            # Reasoning entries
            for entry in self.dataset["reasoning_entries"]:
                self._write_reasoning_to_jsonl(f, entry)
            
            # Conversations
            for conv in self.dataset["conversations"]:
                self._write_conversation_to_jsonl(f, conv)
            
            # Error corrections
            for err in self.dataset["error_corrections"]:
                self._write_error_correction_to_jsonl(f, err)
            
            # Text-derived QA
            for qa in self.dataset["text_derived_qa"]:
                self._write_qa_to_jsonl(f, qa)
        
        print(f"  ✓ OpenAI JSONL: {jsonl_path}")
        
        # 2. Alpaca format
        alpaca_data = []
        for entry in self.dataset["reasoning_entries"]:
            alpaca_data.append({
                "instruction": entry.get("question", ""),
                "input": "",
                "output": self._format_reasoning_output(entry)
            })
        
        alpaca_path = output_dir / "finetuning_alpaca.json"
        with open(alpaca_path, 'w', encoding='utf-8') as f:
            json.dump(alpaca_data, f, indent=2, ensure_ascii=False)
        print(f"  ✓ Alpaca format: {alpaca_path}")
        
        # 3. ShareGPT format (for conversations)
        sharegpt_data = []
        for conv in self.dataset["conversations"]:
            sharegpt_conv = {
                "id": conv.get("id", ""),
                "conversations": []
            }
            for turn in conv.get("turns", []):
                sharegpt_conv["conversations"].append({
                    "from": "human" if turn["role"] == "user" else "gpt",
                    "value": turn["content"]
                })
            sharegpt_data.append(sharegpt_conv)
        
        sharegpt_path = output_dir / "finetuning_sharegpt.json"
        with open(sharegpt_path, 'w', encoding='utf-8') as f:
            json.dump(sharegpt_data, f, indent=2, ensure_ascii=False)
        print(f"  ✓ ShareGPT format: {sharegpt_path}")
    
    def _write_reasoning_to_jsonl(self, f, entry: Dict):
        """Write reasoning entry to JSONL."""
        
        system_msg = """You are a Sri Lankan property law expert. Provide step-by-step legal reasoning with references to relevant statutes. Structure your response with:
1. A clear answer
2. Step-by-step reasoning
3. IRAC analysis (Issue, Rule, Application, Conclusion)
4. Relevant legal references
5. Practical examples where helpful"""
        
        user_msg = entry.get("question", "")
        
        # Build comprehensive response
        response = f"**Answer:** {entry.get('short_answer', '')}\n\n"
        
        if entry.get("detailed_answer"):
            response += f"**Detailed Explanation:** {entry.get('detailed_answer')}\n\n"
        
        response += "**Step-by-Step Reasoning:**\n\n"
        for step in entry.get("reasoning_chain", []):
            response += f"**Step {step.get('step_number', '')}:** {step.get('action', '')}\n"
            response += f"- Legal Basis: {step.get('legal_basis', '')}\n"
            response += f"- Result: {step.get('result', '')}\n\n"
        
        irac = entry.get("irac_analysis", {})
        response += "**IRAC Analysis:**\n"
        response += f"- **Issue:** {irac.get('issue', '')}\n"
        response += f"- **Rule:** {irac.get('rule', '')}\n"
        response += f"- **Application:** {irac.get('application', '')}\n"
        response += f"- **Conclusion:** {irac.get('conclusion', '')}\n\n"
        
        refs = entry.get("legal_references", [])
        if refs:
            response += "**Legal References:**\n"
            for ref in refs:
                response += f"- {ref.get('statute', '')}, {ref.get('section', '')}: {ref.get('relevance', '')}\n"
        
        finetuning_entry = {
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": response}
            ]
        }
        
        f.write(json.dumps(finetuning_entry, ensure_ascii=False) + "\n")
    
    def _write_conversation_to_jsonl(self, f, conv: Dict):
        """Write conversation to JSONL."""
        
        system_msg = """You are a Sri Lankan property law expert providing legal consultation. 
Be helpful, accurate, and cite relevant laws. Explain complex concepts clearly."""
        
        messages = [{"role": "system", "content": system_msg}]
        
        for turn in conv.get("turns", []):
            messages.append({
                "role": turn["role"],
                "content": turn["content"]
            })
        
        f.write(json.dumps({"messages": messages}, ensure_ascii=False) + "\n")
    
    def _write_error_correction_to_jsonl(self, f, err: Dict):
        """Write error correction pair to JSONL."""
        
        # Format as correction request
        system_msg = """You are a Sri Lankan property law expert. When presented with a legal statement, 
identify any errors and provide corrections with proper legal reasoning."""
        
        incorrect = err.get("incorrect_answer", {})
        correct = err.get("correct_answer", {})
        
        user_msg = f"""Question: {err.get('question', '')}

Someone answered: "{incorrect.get('content', '')}"

Is this answer correct? If not, please identify the errors and provide the correct answer."""

        response = f"""The given answer contains errors.

**Errors identified:**
"""
        for error in incorrect.get("errors", []):
            response += f"- {error}\n"

        response += f"""
**Correct Answer:**
{correct.get('content', '')}

**Corrections explained:**
"""
        for corr in correct.get("corrections", []):
            response += f"- Error: {corr.get('error', '')}\n"
            response += f"  Correction: {corr.get('correction', '')}\n"
            response += f"  Explanation: {corr.get('explanation', '')}\n\n"

        finetuning_entry = {
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": response}
            ]
        }
        
        f.write(json.dumps(finetuning_entry, ensure_ascii=False) + "\n")
    
    def _write_qa_to_jsonl(self, f, qa: Dict):
        """Write Q&A pair to JSONL."""
        
        system_msg = "You are a Sri Lankan property law expert. Provide accurate answers based on Sri Lankan statutes."
        
        finetuning_entry = {
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": qa.get("question", "")},
                {"role": "assistant", "content": qa.get("answer", "")}
            ]
        }
        
        f.write(json.dumps(finetuning_entry, ensure_ascii=False) + "\n")
    
    def _format_reasoning_output(self, entry: Dict) -> str:
        """Format reasoning entry for Alpaca format."""
        
        output = f"{entry.get('short_answer', '')}\n\n"
        
        output += "Reasoning:\n"
        for step in entry.get("reasoning_chain", []):
            output += f"{step.get('step_number', '')}. {step.get('action', '')}: {step.get('result', '')}\n"
        
        irac = entry.get("irac_analysis", {})
        output += f"\nLegal Analysis:\n"
        output += f"Issue: {irac.get('issue', '')}\n"
        output += f"Rule: {irac.get('rule', '')}\n"
        output += f"Application: {irac.get('application', '')}\n"
        output += f"Conclusion: {irac.get('conclusion', '')}\n"
        
        return output


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    print("\n" + "=" * 70)
    print("🏛️  ENHANCED LEGAL REASONING DATASET GENERATOR V2")
    print("    LegalVision Project - Sivanuja's Reasoning Module")
    print("=" * 70)
    
    # Check for API key
    if not OPENAI_API_KEY:
        print("\n⚠️  No OpenAI API key found!")
        print("   Set OPENAI_API_KEY in .env file")
        print("\n📝 Creating sample configuration...")
        
        # Create sample .env file
        env_path = Path(".env")
        if not env_path.exists():
            env_path.write_text("OPENAI_API_KEY=your_api_key_here\n")
            print(f"   Created {env_path} - please add your API key")
        
        return
    
    print(f"\n✓ OpenAI API key found")
    print(f"  Quality Model: {MODEL}")
    print(f"  Bulk Model: {FAST_MODEL}")
    
    # Configuration
    print("\n" + "-" * 70)
    print("CONFIGURATION")
    print("-" * 70)
    
    try:
        entries = int(input("Entries per topic (recommended 10-20): ") or "10")
        variations = int(input("Variations per question (recommended 2-3): ") or "2")
        conversations = int(input("Conversations per topic (recommended 3-5): ") or "3")
        case_studies = int(input("Case studies per topic (recommended 2-3): ") or "2")
    except ValueError:
        entries, variations, conversations, case_studies = 10, 2, 3, 2
    
    # Build dataset
    builder = EnhancedDatasetBuilder(OPENAI_API_KEY)
    
    dataset = builder.build_full_dataset(
        entries_per_topic=entries,
        variations_per_question=variations,
        conversations_per_topic=conversations,
        case_studies_per_topic=case_studies,
        include_comparisons=True,
        include_error_corrections=True,
        include_decision_trees=True,
        process_downloaded_laws=INPUT_DIR.exists()
    )
    
    # Save dataset
    builder.save_dataset()
    
    # Final summary
    print("\n" + "=" * 70)
    print("✅ GENERATION COMPLETE")
    print("=" * 70)
    print(f"\nOutput directory: {OUTPUT_DIR.absolute()}")
    print("\nGenerated files:")
    print("  - complete_dataset_v2.json (full dataset)")
    print("  - reasoning_entries.json")
    print("  - conversations.json")
    print("  - case_studies.json")
    print("  - comparisons.json")
    print("  - error_corrections.json")
    print("  - decision_trees.json")
    print("  - text_derived_qa.json")
    print("  - finetuning_openai.jsonl (OpenAI format)")
    print("  - finetuning_alpaca.json (Alpaca format)")
    print("  - finetuning_sharegpt.json (ShareGPT format)")
    print("  - generation_stats.json")
    
    total = dataset["metadata"].get("grand_total", 0)
    print(f"\n📊 Total training samples generated: {total}")


if __name__ == "__main__":
    main()
