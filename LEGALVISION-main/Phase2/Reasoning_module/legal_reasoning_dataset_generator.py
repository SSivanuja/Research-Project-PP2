"""
Legal Reasoning Dataset Generator for LegalVision
Generates Chain-of-Thought, IRAC, and Decision Tree training data

Author: S. Sivanuja
Project: LegalVision - Explainable Legal Reasoning Module
"""

import os
import json
import time
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Configuration
INPUT_DIR = Path("./data/sri_lankan_laws/raw")
OUTPUT_DIR = Path("./data/reasoning_dataset")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL = "gpt-4o"


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ReasoningStep:
    step_number: int
    action: str
    legal_basis: str
    result: str


@dataclass
class LegalReference:
    statute: str
    section: str
    relevance: str
    quote: Optional[str] = None


@dataclass
class IRACAnalysis:
    issue: str
    rule: str
    application: str
    conclusion: str


@dataclass
class ExampleScenario:
    facts: str
    analysis: str
    outcome: str


@dataclass
class ReasoningDataPoint:
    id: str
    topic: str
    category: str
    difficulty: str  # basic, intermediate, advanced
    question: str
    short_answer: str
    reasoning_chain: List[Dict]
    irac_analysis: Dict
    legal_references: List[Dict]
    example_scenario: Dict
    keywords: List[str]
    related_topics: List[str]


# =============================================================================
# LEGAL KNOWLEDGE BASE (Seed Data)
# =============================================================================

LEGAL_TOPICS = {
    "property_transfer": {
        "name": "Property Transfer and Conveyancing",
        "statutes": ["Prevention of Frauds Ordinance", "Registration of Documents Ordinance", "Notaries Ordinance"],
        "key_sections": {
            "Prevention of Frauds Ordinance": ["Section 2 - Writing requirement"],
            "Registration of Documents Ordinance": ["Section 7 - Effect of registration", "Section 8 - Priority"],
            "Notaries Ordinance": ["Section 31 - Attestation requirements"]
        },
        "concepts": ["deed", "conveyance", "attestation", "registration", "transfer"]
    },
    "title_registration": {
        "name": "Title Registration (Bim Saviya)",
        "statutes": ["Registration of Title Act No. 21 of 1998"],
        "key_sections": {
            "Registration of Title Act": ["Section 4 - Title Register", "Section 13 - First Class Title", "Section 14 - Second Class Title"]
        },
        "concepts": ["bim saviya", "first class title", "second class title", "cadastral map", "indefeasible title"]
    },
    "prescription": {
        "name": "Prescription and Adverse Possession",
        "statutes": ["Prescription Ordinance"],
        "key_sections": {
            "Prescription Ordinance": ["Section 3 - Prescriptive title", "Section 6 - 10 year period", "Section 13 - Interruption"]
        },
        "concepts": ["adverse possession", "nec vi", "nec clam", "nec precario", "prescriptive title"]
    },
    "partition": {
        "name": "Partition of Co-owned Property",
        "statutes": ["Partition Act No. 21 of 1977"],
        "key_sections": {
            "Partition Act": ["Section 2 - Right to partition", "Section 5 - Court powers", "Section 48 - Final decree"]
        },
        "concepts": ["co-ownership", "undivided share", "partition action", "interlocutory decree", "final decree"]
    },
    "mortgage": {
        "name": "Mortgage and Securities",
        "statutes": ["Mortgage Act No. 6 of 1949", "Recovery of Loans by Banks Act"],
        "key_sections": {
            "Mortgage Act": ["Section 6 - Primary mortgage", "Section 7 - Subsequent mortgage"],
            "Recovery of Loans by Banks Act": ["Section 4 - Parate execution"]
        },
        "concepts": ["primary mortgage", "secondary mortgage", "parate execution", "foreclosure", "equity of redemption"]
    },
    "lease_tenancy": {
        "name": "Lease and Tenancy",
        "statutes": ["Rent Act No. 7 of 1972"],
        "key_sections": {
            "Rent Act": ["Section 22 - Protected tenants", "Section 23 - Grounds for ejectment", "Section 10 - Authorized rent"]
        },
        "concepts": ["lease", "tenancy", "protected tenant", "ejectment", "authorized rent"]
    },
    "state_land": {
        "name": "State Land Administration",
        "statutes": ["Land Development Ordinance", "State Lands Ordinance"],
        "key_sections": {
            "Land Development Ordinance": ["Section 19 - Permits", "Section 49 - Succession"],
            "State Lands Ordinance": ["Section 6 - Alienation of state land"]
        },
        "concepts": ["state land", "permit", "grant", "crown land", "alienation"]
    },
    "foreign_ownership": {
        "name": "Foreign Ownership Restrictions",
        "statutes": ["Land (Restrictions on Alienation) Act"],
        "key_sections": {
            "Land (Restrictions on Alienation) Act": ["Section 2 - 100% tax", "Section 3 - Exemptions"]
        },
        "concepts": ["foreign ownership", "100% tax", "condominium exemption", "BOI exemption"]
    }
}

# Seed questions for each topic
SEED_QUESTIONS = {
    "property_transfer": [
        "What are the legal requirements for a valid property transfer in Sri Lanka?",
        "What happens if a deed is not registered?",
        "Who can attest a property deed in Sri Lanka?",
        "What is the difference between a sale deed and a gift deed?",
        "Can a property transfer be done without a notary?",
        "What documents are needed for property transfer?",
        "How long do you have to register a deed after execution?",
        "What is the effect of an unregistered deed?",
    ],
    "title_registration": [
        "What is Bim Saviya and how does it work?",
        "What is the difference between deeds registration and title registration?",
        "What is a First Class Title under the Registration of Title Act?",
        "How can a Second Class Title be converted to First Class?",
        "What are the benefits of title registration?",
        "Is title registration mandatory in Sri Lanka?",
        "What is a cadastral map?",
    ],
    "prescription": [
        "How can someone acquire land through prescription in Sri Lanka?",
        "What is the time period for acquisitive prescription?",
        "What does 'nec vi, nec clam, nec precario' mean?",
        "Can prescription run against state land?",
        "What interrupts the running of prescription?",
        "Is a prescriptive title as good as a deed-based title?",
    ],
    "partition": [
        "What is a partition action and who can file one?",
        "Can the court order sale instead of physical partition?",
        "What is an interlocutory decree in partition?",
        "How are shares determined in a partition action?",
        "Can a minority shareholder force partition?",
        "What happens to encumbrances in a partition?",
    ],
    "mortgage": [
        "What is the difference between primary and secondary mortgage?",
        "What is parate execution?",
        "Can a bank sell mortgaged property without going to court?",
        "What is the equity of redemption?",
        "What happens if the mortgagor defaults?",
        "Can a mortgagor sell the mortgaged property?",
    ],
    "lease_tenancy": [
        "Who is a protected tenant under the Rent Act?",
        "What are the grounds for ejectment under the Rent Act?",
        "Can a landlord increase rent freely?",
        "What rights does a tenant have?",
        "Can a lease be terminated before the end of the term?",
        "What is the difference between a lease and a tenancy?",
    ],
    "state_land": [
        "How is state land alienated in Sri Lanka?",
        "What is the difference between a permit and a grant?",
        "Can state land be sold by the permit holder?",
        "What are the succession rules for permit land?",
        "Can state land be mortgaged?",
    ],
    "foreign_ownership": [
        "Can foreigners buy land in Sri Lanka?",
        "What is the 100% tax on foreign land ownership?",
        "Can foreigners own apartments in Sri Lanka?",
        "Are there any exemptions for foreign ownership restrictions?",
        "Can a company with foreign shareholders own land?",
    ]
}


# =============================================================================
# GPT-4o INTEGRATION
# =============================================================================

class LegalReasoningGenerator:
    """Generates legal reasoning datasets using GPT-4o."""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.generated_count = 0
        
    def generate_reasoning_data(self, question: str, topic_key: str) -> Optional[Dict]:
        """Generate complete reasoning data for a question using GPT-4o."""
        
        topic_info = LEGAL_TOPICS.get(topic_key, {})
        statutes = topic_info.get("statutes", [])
        concepts = topic_info.get("concepts", [])
        
        prompt = f"""You are a Sri Lankan property law expert. Generate a comprehensive legal reasoning dataset entry for the following question.

QUESTION: {question}

TOPIC: {topic_info.get('name', topic_key)}
RELEVANT STATUTES: {', '.join(statutes)}
KEY CONCEPTS: {', '.join(concepts)}

Generate a JSON response with this EXACT structure:
{{
    "question": "{question}",
    "short_answer": "A concise 1-2 sentence answer",
    "reasoning_chain": [
        {{
            "step_number": 1,
            "action": "What legal analysis step is being taken",
            "legal_basis": "The statute, section, or principle being applied",
            "result": "What this step determines or establishes"
        }},
        // Include 3-5 logical steps
    ],
    "irac_analysis": {{
        "issue": "The legal question to be resolved",
        "rule": "The applicable legal rules and statutes",
        "application": "How the rules apply to this situation",
        "conclusion": "The legal conclusion reached"
    }},
    "legal_references": [
        {{
            "statute": "Name of the Act/Ordinance",
            "section": "Specific section number",
            "relevance": "Why this section is relevant",
            "quote": "Brief quote from the section if applicable (can be null)"
        }}
    ],
    "example_scenario": {{
        "facts": "A practical example scenario (2-3 sentences)",
        "analysis": "How the law applies to this scenario",
        "outcome": "The legal outcome"
    }},
    "keywords": ["list", "of", "relevant", "legal", "terms"],
    "related_topics": ["other", "related", "legal", "topics"]
}}

IMPORTANT:
- Base answers on actual Sri Lankan law
- Include specific statute names and sections
- Make reasoning steps logical and sequential
- Ensure the example scenario is realistic
- Return ONLY valid JSON, no markdown formatting"""

        try:
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a Sri Lankan property law expert specializing in legal education and explainable AI. Always respond with valid JSON only."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up response (remove markdown if present)
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            
            data = json.loads(content)
            self.generated_count += 1
            return data
            
        except json.JSONDecodeError as e:
            print(f"    ⚠ JSON parse error: {e}")
            return None
        except Exception as e:
            print(f"    ⚠ API error: {e}")
            return None

    def generate_decision_tree(self, topic_key: str) -> Optional[Dict]:
        """Generate a decision tree for a legal topic."""
        
        topic_info = LEGAL_TOPICS.get(topic_key, {})
        
        prompt = f"""Create a legal decision tree for Sri Lankan property law on the topic: {topic_info.get('name', topic_key)}

The decision tree should help someone determine the answer to a common legal question in this area.

Generate a JSON response with this structure:
{{
    "topic": "{topic_info.get('name', topic_key)}",
    "purpose": "What this decision tree helps determine",
    "entry_question": "The main question being answered",
    "nodes": {{
        "start": {{
            "question": "First question to ask",
            "yes_path": "node_id or OUTCOME: result",
            "no_path": "node_id or OUTCOME: result",
            "legal_basis": "Relevant law"
        }},
        "node_2": {{
            "question": "Next question",
            "yes_path": "...",
            "no_path": "...",
            "legal_basis": "..."
        }}
        // Continue for 4-6 nodes total
    }},
    "outcomes": {{
        "outcome_1": {{
            "result": "Legal conclusion",
            "explanation": "Why this is the outcome",
            "next_steps": "What to do next"
        }}
    }}
}}

Return ONLY valid JSON."""

        try:
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "You are a Sri Lankan property law expert. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            return json.loads(content.strip())
            
        except Exception as e:
            print(f"    ⚠ Decision tree error: {e}")
            return None

    def enhance_with_counterarguments(self, data: Dict) -> Dict:
        """Add counter-arguments and limitations to existing data."""
        
        prompt = f"""Given this legal reasoning data, add counter-arguments and limitations.

CURRENT DATA:
Question: {data.get('question')}
Conclusion: {data.get('irac_analysis', {}).get('conclusion', '')}

Generate JSON with:
{{
    "counter_arguments": [
        {{
            "argument": "A potential counter-argument",
            "basis": "Legal or factual basis",
            "rebuttal": "How to address this counter-argument"
        }}
    ],
    "limitations": [
        "Limitation or exception 1",
        "Limitation or exception 2"
    ],
    "practical_considerations": [
        "Real-world consideration 1",
        "Real-world consideration 2"
    ]
}}

Return ONLY valid JSON."""

        try:
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "You are a Sri Lankan property law expert. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=800
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            enhancements = json.loads(content.strip())
            data.update(enhancements)
            return data
            
        except Exception as e:
            print(f"    ⚠ Enhancement error: {e}")
            return data


# =============================================================================
# DATASET BUILDER
# =============================================================================

class LegalReasoningDatasetBuilder:
    """Builds the complete legal reasoning dataset."""
    
    def __init__(self, api_key: str):
        self.generator = LegalReasoningGenerator(api_key)
        self.dataset = {
            "metadata": {
                "name": "Sri Lankan Property Law Reasoning Dataset",
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "description": "Chain-of-thought legal reasoning dataset for LLM fine-tuning",
                "author": "LegalVision Project - S. Sivanuja",
                "topics": list(LEGAL_TOPICS.keys()),
                "total_entries": 0
            },
            "reasoning_entries": [],
            "decision_trees": [],
            "statistics": {}
        }
        
    def build_dataset(self, entries_per_topic: int = 5, include_decision_trees: bool = True):
        """Build the complete dataset."""
        
        print("=" * 70)
        print("LEGAL REASONING DATASET GENERATOR")
        print("=" * 70)
        print(f"Model: {MODEL}")
        print(f"Entries per topic: {entries_per_topic}")
        print(f"Total topics: {len(LEGAL_TOPICS)}")
        print("-" * 70)
        
        entry_id = 1
        stats = {topic: {"generated": 0, "failed": 0} for topic in LEGAL_TOPICS}
        
        # Generate reasoning entries for each topic
        for topic_key, topic_info in LEGAL_TOPICS.items():
            print(f"\n📚 Topic: {topic_info['name']}")
            print("-" * 50)
            
            questions = SEED_QUESTIONS.get(topic_key, [])[:entries_per_topic]
            
            for i, question in enumerate(questions, 1):
                print(f"  [{i}/{len(questions)}] Generating: {question[:50]}...")
                
                # Generate main reasoning data
                data = self.generator.generate_reasoning_data(question, topic_key)
                
                if data:
                    # Add metadata
                    data["id"] = f"LR_{entry_id:04d}"
                    data["topic"] = topic_key
                    data["topic_name"] = topic_info["name"]
                    data["category"] = topic_key
                    data["difficulty"] = self._estimate_difficulty(question)
                    data["generated_at"] = datetime.now().isoformat()
                    
                    # Enhance with counter-arguments (50% of entries)
                    if random.random() > 0.5:
                        data = self.generator.enhance_with_counterarguments(data)
                    
                    self.dataset["reasoning_entries"].append(data)
                    stats[topic_key]["generated"] += 1
                    entry_id += 1
                    print(f"    ✓ Generated successfully")
                else:
                    stats[topic_key]["failed"] += 1
                    print(f"    ✗ Generation failed")
                
                # Rate limiting
                time.sleep(1)
        
        # Generate decision trees
        if include_decision_trees:
            print(f"\n🌳 Generating Decision Trees")
            print("-" * 50)
            
            for topic_key, topic_info in LEGAL_TOPICS.items():
                print(f"  Generating tree for: {topic_info['name']}...")
                
                tree = self.generator.generate_decision_tree(topic_key)
                if tree:
                    tree["id"] = f"DT_{topic_key}"
                    tree["topic_key"] = topic_key
                    self.dataset["decision_trees"].append(tree)
                    print(f"    ✓ Decision tree generated")
                else:
                    print(f"    ✗ Decision tree failed")
                
                time.sleep(1)
        
        # Update metadata
        self.dataset["metadata"]["total_entries"] = len(self.dataset["reasoning_entries"])
        self.dataset["metadata"]["total_decision_trees"] = len(self.dataset["decision_trees"])
        self.dataset["statistics"] = stats
        
        return self.dataset
    
    def _estimate_difficulty(self, question: str) -> str:
        """Estimate question difficulty based on complexity indicators."""
        complex_terms = ["exception", "conflict", "multiple", "versus", "compare", "analyze"]
        intermediate_terms = ["difference", "requirements", "process", "when", "how"]
        
        question_lower = question.lower()
        
        if any(term in question_lower for term in complex_terms):
            return "advanced"
        elif any(term in question_lower for term in intermediate_terms):
            return "intermediate"
        return "basic"
    
    def save_dataset(self, output_dir: Path = OUTPUT_DIR):
        """Save the dataset in multiple formats."""
        
        print(f"\n💾 Saving Dataset")
        print("-" * 50)
        
        # 1. Save complete dataset as JSON
        complete_path = output_dir / "legal_reasoning_dataset_complete.json"
        with open(complete_path, 'w', encoding='utf-8') as f:
            json.dump(self.dataset, f, indent=2, ensure_ascii=False)
        print(f"  ✓ Complete dataset: {complete_path}")
        
        # 2. Save reasoning entries only (for training)
        entries_path = output_dir / "reasoning_entries.json"
        with open(entries_path, 'w', encoding='utf-8') as f:
            json.dump(self.dataset["reasoning_entries"], f, indent=2, ensure_ascii=False)
        print(f"  ✓ Reasoning entries: {entries_path}")
        
        # 3. Save decision trees
        trees_path = output_dir / "decision_trees.json"
        with open(trees_path, 'w', encoding='utf-8') as f:
            json.dump(self.dataset["decision_trees"], f, indent=2, ensure_ascii=False)
        print(f"  ✓ Decision trees: {trees_path}")
        
        # 4. Save in fine-tuning format (JSONL)
        self._save_finetuning_format(output_dir)
        
        # 5. Save in conversational format
        self._save_conversational_format(output_dir)
        
        # 6. Save statistics
        stats_path = output_dir / "generation_stats.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": self.dataset["metadata"],
                "statistics": self.dataset["statistics"]
            }, f, indent=2)
        print(f"  ✓ Statistics: {stats_path}")
        
    def _save_finetuning_format(self, output_dir: Path):
        """Save in OpenAI fine-tuning JSONL format."""
        
        jsonl_path = output_dir / "finetuning_data.jsonl"
        
        with open(jsonl_path, 'w', encoding='utf-8') as f:
            for entry in self.dataset["reasoning_entries"]:
                # Format 1: Question -> Full reasoning
                system_msg = "You are a Sri Lankan property law expert. Provide step-by-step legal reasoning with references to relevant statutes."
                
                user_msg = entry.get("question", "")
                
                # Build assistant response with reasoning chain
                reasoning_text = "Let me analyze this step by step:\n\n"
                for step in entry.get("reasoning_chain", []):
                    reasoning_text += f"**Step {step.get('step_number', '')}**: {step.get('action', '')}\n"
                    reasoning_text += f"- Legal Basis: {step.get('legal_basis', '')}\n"
                    reasoning_text += f"- Result: {step.get('result', '')}\n\n"
                
                irac = entry.get("irac_analysis", {})
                reasoning_text += f"**IRAC Analysis:**\n"
                reasoning_text += f"- Issue: {irac.get('issue', '')}\n"
                reasoning_text += f"- Rule: {irac.get('rule', '')}\n"
                reasoning_text += f"- Application: {irac.get('application', '')}\n"
                reasoning_text += f"- Conclusion: {irac.get('conclusion', '')}\n\n"
                
                refs = entry.get("legal_references", [])
                if refs:
                    reasoning_text += "**Legal References:**\n"
                    for ref in refs:
                        reasoning_text += f"- {ref.get('statute', '')}, {ref.get('section', '')}: {ref.get('relevance', '')}\n"
                
                finetuning_entry = {
                    "messages": [
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg},
                        {"role": "assistant", "content": reasoning_text}
                    ]
                }
                
                f.write(json.dumps(finetuning_entry, ensure_ascii=False) + "\n")
        
        print(f"  ✓ Fine-tuning JSONL: {jsonl_path}")
    
    def _save_conversational_format(self, output_dir: Path):
        """Save in conversational format for chatbot training."""
        
        conv_path = output_dir / "conversational_data.json"
        conversations = []
        
        for entry in self.dataset["reasoning_entries"]:
            conv = {
                "id": entry.get("id"),
                "conversation": [
                    {
                        "role": "user",
                        "content": entry.get("question", "")
                    },
                    {
                        "role": "assistant",
                        "content": entry.get("short_answer", ""),
                        "reasoning_chain": entry.get("reasoning_chain", []),
                        "references": entry.get("legal_references", [])
                    }
                ]
            }
            
            # Add follow-up based on example scenario
            scenario = entry.get("example_scenario", {})
            if scenario:
                conv["conversation"].extend([
                    {
                        "role": "user",
                        "content": f"Can you give me a practical example? For instance: {scenario.get('facts', '')}"
                    },
                    {
                        "role": "assistant",
                        "content": f"In this scenario: {scenario.get('analysis', '')} Therefore, {scenario.get('outcome', '')}",
                        "reasoning_type": "application"
                    }
                ])
            
            conversations.append(conv)
        
        with open(conv_path, 'w', encoding='utf-8') as f:
            json.dump(conversations, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ Conversational data: {conv_path}")


# =============================================================================
# MANUAL SEED DATA (Fallback if no API key)
# =============================================================================

def create_manual_seed_dataset() -> Dict:
    """Create a manual seed dataset without API calls."""
    
    print("Creating manual seed dataset (no API key provided)...")
    
    seed_entries = [
        {
            "id": "LR_0001",
            "topic": "property_transfer",
            "topic_name": "Property Transfer and Conveyancing",
            "category": "property_transfer",
            "difficulty": "basic",
            "question": "What are the legal requirements for a valid property transfer in Sri Lanka?",
            "short_answer": "A valid property transfer requires a written deed, attestation by a licensed notary public, signatures of two witnesses, and registration at the Land Registry.",
            "reasoning_chain": [
                {
                    "step_number": 1,
                    "action": "Check writing requirement",
                    "legal_basis": "Prevention of Frauds Ordinance, Section 2",
                    "result": "All transfers of land must be in writing"
                },
                {
                    "step_number": 2,
                    "action": "Check attestation requirement",
                    "legal_basis": "Prevention of Frauds Ordinance, Section 2; Notaries Ordinance, Section 31",
                    "result": "Deed must be attested by a licensed notary public"
                },
                {
                    "step_number": 3,
                    "action": "Check witness requirement",
                    "legal_basis": "Prevention of Frauds Ordinance, Section 2",
                    "result": "Two witnesses must sign the deed"
                },
                {
                    "step_number": 4,
                    "action": "Check registration requirement",
                    "legal_basis": "Registration of Documents Ordinance, Section 7",
                    "result": "Registration required for effect against third parties"
                }
            ],
            "irac_analysis": {
                "issue": "What formalities are required for a valid property transfer in Sri Lanka?",
                "rule": "Under the Prevention of Frauds Ordinance (Section 2), all instruments affecting land must be in writing, signed by the party, attested by a notary public, and witnessed by two persons. Under the Registration of Documents Ordinance (Section 7), registration is required for the instrument to affect land as against third parties.",
                "application": "Any property transfer must comply with these formalities. A deed that lacks any of these elements will be either void or unenforceable depending on the defect.",
                "conclusion": "A valid property transfer requires: (1) written deed, (2) notarial attestation, (3) two witnesses, and (4) registration. Failure to comply renders the transfer either void or ineffective against third parties."
            },
            "legal_references": [
                {
                    "statute": "Prevention of Frauds Ordinance",
                    "section": "Section 2",
                    "relevance": "Establishes writing, notary, and witness requirements",
                    "quote": "No sale, purchase, transfer, assignment or mortgage of land shall be of force unless in writing signed and attested by a notary public with two witnesses"
                },
                {
                    "statute": "Registration of Documents Ordinance",
                    "section": "Section 7",
                    "relevance": "Establishes registration requirement",
                    "quote": "No instrument affecting land shall be of any force against third parties until registered"
                },
                {
                    "statute": "Notaries Ordinance",
                    "section": "Section 31",
                    "relevance": "Defines notary's duties in attestation",
                    "quote": None
                }
            ],
            "example_scenario": {
                "facts": "A agrees to sell land to B. They sign an agreement on plain paper without a notary. B pays the full price and takes possession.",
                "analysis": "The agreement is void under the Prevention of Frauds Ordinance as it was not attested by a notary public. Despite payment and possession, B has not acquired legal title.",
                "outcome": "B cannot claim legal ownership. B may have a claim for recovery of the purchase price but cannot enforce the transfer."
            },
            "keywords": ["deed", "notary", "registration", "prevention of frauds", "conveyance", "transfer"],
            "related_topics": ["title_registration", "mortgage"]
        },
        {
            "id": "LR_0002",
            "topic": "prescription",
            "topic_name": "Prescription and Adverse Possession",
            "category": "prescription",
            "difficulty": "intermediate",
            "question": "How can someone acquire land through prescription in Sri Lanka?",
            "short_answer": "A person can acquire title through prescription by possessing land continuously for 10 years, where the possession is adverse (without permission), open (not secret), and peaceful (without force).",
            "reasoning_chain": [
                {
                    "step_number": 1,
                    "action": "Identify the prescription period",
                    "legal_basis": "Prescription Ordinance, Section 3",
                    "result": "The statutory period is 10 years of continuous possession"
                },
                {
                    "step_number": 2,
                    "action": "Check the nature of possession required",
                    "legal_basis": "Roman-Dutch law principle: nec vi, nec clam, nec precario",
                    "result": "Possession must be without force, without secrecy, and without permission"
                },
                {
                    "step_number": 3,
                    "action": "Verify continuity of possession",
                    "legal_basis": "Prescription Ordinance, Section 13",
                    "result": "Possession must be uninterrupted; legal action or acknowledgment interrupts prescription"
                },
                {
                    "step_number": 4,
                    "action": "Determine effect of completed prescription",
                    "legal_basis": "Prescription Ordinance, Section 3",
                    "result": "Successful prescription extinguishes the original owner's title"
                }
            ],
            "irac_analysis": {
                "issue": "Under what conditions can a person acquire legal title to land through adverse possession in Sri Lanka?",
                "rule": "Under the Prescription Ordinance, a person who possesses land for 10 years continuously, adversely, openly, and peacefully acquires prescriptive title. The possession must be nec vi (without force), nec clam (without secrecy), and nec precario (without permission).",
                "application": "The claimant must prove: (1) 10 years continuous possession, (2) possession was hostile to the owner's rights, (3) possession was open and notorious, (4) possession was peaceful. If all elements are proven, title vests in the possessor.",
                "conclusion": "Prescriptive title can be acquired through 10 years of adverse, open, and peaceful possession, extinguishing the original owner's title."
            },
            "legal_references": [
                {
                    "statute": "Prescription Ordinance",
                    "section": "Section 3",
                    "relevance": "Establishes prescriptive title acquisition",
                    "quote": None
                },
                {
                    "statute": "Prescription Ordinance",
                    "section": "Section 6",
                    "relevance": "Specifies 10-year period",
                    "quote": None
                },
                {
                    "statute": "Prescription Ordinance",
                    "section": "Section 13",
                    "relevance": "Addresses interruption of prescription",
                    "quote": None
                }
            ],
            "example_scenario": {
                "facts": "C occupies vacant land belonging to D in 2010. C builds a house, pays taxes, and openly lives there. D takes no action until 2022.",
                "analysis": "C has possessed the land openly and peacefully for over 10 years (2010-2022). The possession was adverse as C had no permission from D. D's inaction allowed prescription to complete.",
                "outcome": "C has acquired prescriptive title. D's ownership has been extinguished by operation of law."
            },
            "keywords": ["prescription", "adverse possession", "nec vi", "nec clam", "nec precario", "10 years", "prescriptive title"],
            "related_topics": ["property_transfer", "state_land"]
        },
        {
            "id": "LR_0003",
            "topic": "partition",
            "topic_name": "Partition of Co-owned Property",
            "category": "partition",
            "difficulty": "intermediate",
            "question": "What is a partition action and who can file one?",
            "short_answer": "A partition action is a legal proceeding to divide co-owned property. Any co-owner, regardless of the size of their share, can file a partition action under the Partition Act No. 21 of 1977.",
            "reasoning_chain": [
                {
                    "step_number": 1,
                    "action": "Define partition",
                    "legal_basis": "Partition Act No. 21 of 1977",
                    "result": "Partition is the division of co-owned property among co-owners"
                },
                {
                    "step_number": 2,
                    "action": "Identify who can file",
                    "legal_basis": "Partition Act, Section 2",
                    "result": "Any co-owner can file, regardless of share size"
                },
                {
                    "step_number": 3,
                    "action": "Determine court's powers",
                    "legal_basis": "Partition Act, Section 5",
                    "result": "Court can order physical division or sale if indivisible"
                },
                {
                    "step_number": 4,
                    "action": "Understand the effect of partition decree",
                    "legal_basis": "Partition Act, Section 48",
                    "result": "Final decree is conclusive and binding on all parties"
                }
            ],
            "irac_analysis": {
                "issue": "What is partition and who has the right to initiate partition proceedings?",
                "rule": "Under the Partition Act No. 21 of 1977, any person having an interest in land as co-owner may institute an action for partition. The court has power to order physical division or, if the property cannot be conveniently divided, to order sale and division of proceeds.",
                "application": "Even a minority shareholder (e.g., owning 1/10th share) can compel partition. The majority cannot prevent partition. The court will determine the most equitable method of division.",
                "conclusion": "Any co-owner can file partition action regardless of share size. The court will either physically divide the property or order its sale."
            },
            "legal_references": [
                {
                    "statute": "Partition Act No. 21 of 1977",
                    "section": "Section 2",
                    "relevance": "Right to partition",
                    "quote": None
                },
                {
                    "statute": "Partition Act No. 21 of 1977",
                    "section": "Section 5",
                    "relevance": "Court's power to order sale",
                    "quote": None
                },
                {
                    "statute": "Partition Act No. 21 of 1977",
                    "section": "Section 48",
                    "relevance": "Finality of decree",
                    "quote": None
                }
            ],
            "example_scenario": {
                "facts": "Three siblings inherit a house equally. Two want to keep it, but one wants to sell their share. The majority refuses to buy out the minority.",
                "analysis": "The minority sibling (1/3 share) can file partition action. The court cannot deny partition merely because the majority objects. If the house cannot be physically divided, the court will order sale.",
                "outcome": "Partition will be granted. The house will likely be sold and proceeds divided equally among the three siblings."
            },
            "keywords": ["partition", "co-ownership", "undivided share", "partition decree", "interlocutory decree", "final decree"],
            "related_topics": ["property_transfer", "prescription"]
        }
    ]
    
    # Create decision tree example
    decision_trees = [
        {
            "id": "DT_property_transfer",
            "topic_key": "property_transfer",
            "topic": "Property Transfer and Conveyancing",
            "purpose": "Determine if a property transfer is legally valid",
            "entry_question": "Is this property transfer legally valid?",
            "nodes": {
                "start": {
                    "question": "Is there a written deed/instrument?",
                    "yes_path": "node_2",
                    "no_path": "OUTCOME_INVALID_WRITING",
                    "legal_basis": "Prevention of Frauds Ordinance, Section 2"
                },
                "node_2": {
                    "question": "Was the deed attested by a licensed notary public?",
                    "yes_path": "node_3",
                    "no_path": "OUTCOME_INVALID_NOTARY",
                    "legal_basis": "Prevention of Frauds Ordinance, Section 2"
                },
                "node_3": {
                    "question": "Were there two witnesses who signed?",
                    "yes_path": "node_4",
                    "no_path": "OUTCOME_INVALID_WITNESSES",
                    "legal_basis": "Prevention of Frauds Ordinance, Section 2"
                },
                "node_4": {
                    "question": "Has the deed been registered at the Land Registry?",
                    "yes_path": "OUTCOME_VALID",
                    "no_path": "OUTCOME_PARTIAL",
                    "legal_basis": "Registration of Documents Ordinance, Section 7"
                }
            },
            "outcomes": {
                "OUTCOME_INVALID_WRITING": {
                    "result": "INVALID - Transfer is void",
                    "explanation": "The Prevention of Frauds Ordinance requires all land transfers to be in writing. An oral agreement to transfer land is not enforceable.",
                    "next_steps": "Execute a proper written deed with notarial attestation."
                },
                "OUTCOME_INVALID_NOTARY": {
                    "result": "INVALID - Transfer is void",
                    "explanation": "Without notarial attestation, the deed is not valid under the Prevention of Frauds Ordinance.",
                    "next_steps": "Have the deed properly attested by a licensed notary public."
                },
                "OUTCOME_INVALID_WITNESSES": {
                    "result": "INVALID - Transfer is void",
                    "explanation": "The law requires two witnesses for a valid deed.",
                    "next_steps": "Re-execute the deed with two witnesses present."
                },
                "OUTCOME_PARTIAL": {
                    "result": "PARTIALLY VALID - Valid between parties only",
                    "explanation": "The transfer is valid between the seller and buyer, but does not affect third parties until registered.",
                    "next_steps": "Register the deed at the Land Registry immediately to protect against third party claims."
                },
                "OUTCOME_VALID": {
                    "result": "VALID - Transfer is complete and enforceable",
                    "explanation": "All legal requirements have been met. The transfer is valid against all parties.",
                    "next_steps": "Retain the registered deed safely. Consider obtaining title insurance."
                }
            }
        }
    ]
    
    return {
        "metadata": {
            "name": "Sri Lankan Property Law Reasoning Dataset (Seed)",
            "version": "1.0-seed",
            "created_at": datetime.now().isoformat(),
            "description": "Manually created seed dataset for legal reasoning",
            "author": "LegalVision Project - S. Sivanuja",
            "total_entries": len(seed_entries)
        },
        "reasoning_entries": seed_entries,
        "decision_trees": decision_trees,
        "statistics": {"manual_entries": len(seed_entries)}
    }


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    print("\n" + "=" * 70)
    print("🏛️  LEGAL REASONING DATASET GENERATOR")
    print("    LegalVision Project - Sivanuja's Reasoning Module")
    print("=" * 70)
    
    # Check for API key
    if not OPENAI_API_KEY:
        print("\n ⚠️  No OpenAI API key found!")
        print("    Creating manual seed dataset instead...")
        
        dataset = create_manual_seed_dataset()
        
        # Save manual dataset
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        with open(OUTPUT_DIR / "legal_reasoning_dataset_seed.json", 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Seed dataset saved to: {OUTPUT_DIR / 'legal_reasoning_dataset_seed.json'}")
        print(f"   Entries: {len(dataset['reasoning_entries'])}")
        print(f"   Decision Trees: {len(dataset['decision_trees'])}")
        
        print("\n📝 To generate full dataset with GPT-4o:")
        print("   1. Set OPENAI_API_KEY in .env file")
        print("   2. Run this script again")
        
        return
    
    # Build full dataset with GPT-4o
    print(f"\n✓ OpenAI API key found")
    print(f"  Model: {MODEL}")
    
    # Get user input for dataset size
    try:
        entries_per_topic = int(input("\nEntries per topic (recommended 5-10): ") or "5")
    except ValueError:
        entries_per_topic = 5
    
    # Build dataset
    builder = LegalReasoningDatasetBuilder(OPENAI_API_KEY)
    dataset = builder.build_dataset(
        entries_per_topic=entries_per_topic,
        include_decision_trees=True
    )
    
    # Save dataset
    builder.save_dataset()
    
    # Print summary
    print("\n" + "=" * 70)
    print("GENERATION COMPLETE")
    print("=" * 70)
    print(f"Total reasoning entries: {len(dataset['reasoning_entries'])}")
    print(f"Total decision trees: {len(dataset['decision_trees'])}")
    print(f"Output directory: {OUTPUT_DIR.absolute()}")
    print("\nGenerated files:")
    print("  - legal_reasoning_dataset_complete.json (full dataset)")
    print("  - reasoning_entries.json (entries only)")
    print("  - decision_trees.json (trees only)")
    print("  - finetuning_data.jsonl (OpenAI fine-tuning format)")
    print("  - conversational_data.json (chatbot format)")
    print("  - generation_stats.json (statistics)")


if __name__ == "__main__":
    main()
