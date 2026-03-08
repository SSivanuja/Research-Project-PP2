"""
Initial Accuracy Evaluation Script - Explainable Legal Reasoning Module
Author: S. Sivanuja
Project: LegalVision (25-26J-127)

This script evaluates the accuracy of the fine-tuned legal reasoning model.
It tests:
1. Legal reasoning accuracy (correct conclusions)
2. IRAC format compliance
3. Chain-of-Thought quality
4. Statute citation accuracy
5. Response relevance

Run this script after fine-tuning to evaluate model performance.
"""

import json
import re
import os
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict

# ============= CONFIGURATION =============
CONFIG = {
    "model_responses_file": "./model_responses.json",
    "ground_truth_file": "./ground_truth_answers.json",
    "output_report": "./reasoning_evaluation_report.json"
}

# ============= DATA STRUCTURES =============

@dataclass
class ReasoningEvaluation:
    """Stores evaluation for a single response"""
    question_id: str
    topic: str
    is_correct: bool = False
    is_partially_correct: bool = False
    irac_score: Dict[str, float] = field(default_factory=dict)
    cot_score: float = 0.0
    citation_accuracy: float = 0.0
    relevance_score: float = 0.0
    errors: List[str] = field(default_factory=list)


@dataclass 
class IRACComponents:
    """IRAC analysis components"""
    has_issue: bool = False
    has_rule: bool = False
    has_application: bool = False
    has_conclusion: bool = False
    issue_quality: float = 0.0
    rule_quality: float = 0.0
    application_quality: float = 0.0
    conclusion_quality: float = 0.0


# ============= EVALUATION FUNCTIONS =============

def check_irac_format(response: str) -> IRACComponents:
    """
    Check if response follows IRAC format
    Returns component presence and quality scores
    """
    irac = IRACComponents()
    response_lower = response.lower()
    
    # Check for Issue identification
    issue_patterns = [
        r'\b(issue|question|problem|matter at hand)\b',
        r'\b(whether|if|can|does|is it)\b.*\?',
        r'the (legal |)issue (is|here)',
    ]
    for pattern in issue_patterns:
        if re.search(pattern, response_lower):
            irac.has_issue = True
            irac.issue_quality = 0.8  # Base score, can be refined
            break
    
    # Check for Rule statement
    rule_patterns = [
        r'\b(according to|under|pursuant to)\b',
        r'\b(section|act|ordinance|law)\b.*\d+',
        r'\b(the (law|rule|principle) (states|provides|requires))\b',
        r'\b(legal (principle|requirement|provision))\b',
    ]
    for pattern in rule_patterns:
        if re.search(pattern, response_lower):
            irac.has_rule = True
            irac.rule_quality = 0.8
            break
    
    # Check for Application
    application_patterns = [
        r'\b(in this case|here|applying|applied to)\b',
        r'\b(the facts (show|indicate|suggest))\b',
        r'\b(therefore|thus|consequently|as a result)\b',
        r'\b(given (that|the facts))\b',
    ]
    for pattern in application_patterns:
        if re.search(pattern, response_lower):
            irac.has_application = True
            irac.application_quality = 0.8
            break
    
    # Check for Conclusion
    conclusion_patterns = [
        r'\b(therefore|thus|in conclusion|accordingly)\b',
        r'\b(the (answer|conclusion|result) is)\b',
        r'\b(it (can be|is) concluded)\b',
        r'\b(yes|no),?\s*(the|this|it)\b',
    ]
    for pattern in conclusion_patterns:
        if re.search(pattern, response_lower):
            irac.has_conclusion = True
            irac.conclusion_quality = 0.8
            break
    
    return irac


def evaluate_chain_of_thought(response: str) -> Dict[str, Any]:
    """
    Evaluate the quality of Chain-of-Thought reasoning
    """
    metrics = {
        "has_reasoning_steps": False,
        "step_count": 0,
        "logical_flow": 0.0,
        "legal_basis_cited": False,
        "conclusion_supported": False,
        "overall_score": 0.0
    }
    
    # Look for numbered steps or clear reasoning progression
    step_patterns = [
        r'(?:step|first|second|third|finally|\d+[\.\)]\s)',
        r'(?:firstly|secondly|thirdly|lastly)',
        r'(?:to begin|next|then|after that)',
    ]
    
    steps_found = 0
    for pattern in step_patterns:
        matches = re.findall(pattern, response.lower())
        steps_found += len(matches)
    
    if steps_found > 0:
        metrics["has_reasoning_steps"] = True
        metrics["step_count"] = min(steps_found, 5)  # Cap at 5
    
    # Check for logical connectors (indicates flow)
    logical_connectors = [
        r'\b(because|since|therefore|thus|hence|consequently)\b',
        r'\b(this means|as a result|it follows that)\b',
    ]
    
    connector_count = 0
    for pattern in logical_connectors:
        connector_count += len(re.findall(pattern, response.lower()))
    
    metrics["logical_flow"] = min(connector_count / 3, 1.0)  # Normalize
    
    # Check for legal citations
    legal_patterns = [
        r'\b(section|act|ordinance)\b.*\d+',
        r'\b(according to|under|pursuant to)\b',
    ]
    
    for pattern in legal_patterns:
        if re.search(pattern, response.lower()):
            metrics["legal_basis_cited"] = True
            break
    
    # Calculate overall score
    score = 0.0
    if metrics["has_reasoning_steps"]:
        score += 0.3 * min(metrics["step_count"] / 4, 1.0)
    score += 0.3 * metrics["logical_flow"]
    if metrics["legal_basis_cited"]:
        score += 0.2
    score += 0.2  # Base score for having a response
    
    metrics["overall_score"] = round(score, 2)
    
    return metrics


def check_statute_citations(response: str, expected_statutes: List[str]) -> Dict[str, Any]:
    """
    Check accuracy of statute citations
    """
    metrics = {
        "citations_found": [],
        "correct_citations": 0,
        "incorrect_citations": 0,
        "missing_citations": 0,
        "accuracy": 0.0
    }
    
    # Common Sri Lankan legal statutes to look for
    statute_patterns = [
        (r'prevention of frauds ordinance', 'Prevention of Frauds Ordinance'),
        (r'registration of documents ordinance', 'Registration of Documents Ordinance'),
        (r'registration of title act|bim saviya', 'Registration of Title Act'),
        (r'prescription ordinance', 'Prescription Ordinance'),
        (r'partition act', 'Partition Act'),
        (r'mortgage act', 'Mortgage Act'),
        (r'rent act', 'Rent Act'),
        (r'land development ordinance', 'Land Development Ordinance'),
        (r'notaries ordinance', 'Notaries Ordinance'),
        (r'land acquisition act', 'Land Acquisition Act'),
        (r'land reform law', 'Land Reform Law'),
        (r'trust ordinance', 'Trust Ordinance'),
    ]
    
    response_lower = response.lower()
    
    for pattern, statute_name in statute_patterns:
        if re.search(pattern, response_lower):
            metrics["citations_found"].append(statute_name)
    
    # Compare with expected
    found_set = set(metrics["citations_found"])
    expected_set = set(expected_statutes)
    
    metrics["correct_citations"] = len(found_set & expected_set)
    metrics["incorrect_citations"] = len(found_set - expected_set)
    metrics["missing_citations"] = len(expected_set - found_set)
    
    # Calculate accuracy
    total = len(expected_set)
    if total > 0:
        metrics["accuracy"] = round(metrics["correct_citations"] / total, 2)
    else:
        metrics["accuracy"] = 1.0 if len(found_set) == 0 else 0.5
    
    return metrics


def evaluate_response_relevance(response: str, question: str, keywords: List[str]) -> float:
    """
    Evaluate how relevant the response is to the question
    """
    response_lower = response.lower()
    question_lower = question.lower()
    
    score = 0.0
    
    # Check if response addresses key terms from question
    question_words = set(question_lower.split())
    response_words = set(response_lower.split())
    
    # Remove common words
    common_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 
                   'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                   'would', 'could', 'should', 'may', 'might', 'must', 'can',
                   'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
                   'what', 'how', 'when', 'where', 'who', 'which', 'why'}
    
    question_key = question_words - common_words
    overlap = len(question_key & response_words)
    
    if len(question_key) > 0:
        score += 0.4 * (overlap / len(question_key))
    
    # Check for expected keywords
    keyword_matches = sum(1 for kw in keywords if kw.lower() in response_lower)
    if len(keywords) > 0:
        score += 0.4 * (keyword_matches / len(keywords))
    
    # Check response length (too short might not be helpful)
    word_count = len(response.split())
    if word_count >= 50:
        score += 0.2
    elif word_count >= 20:
        score += 0.1
    
    return round(min(score, 1.0), 2)


def compare_answers(model_answer: str, correct_answer: str) -> Tuple[bool, bool]:
    """
    Compare model answer with correct answer
    Returns (is_correct, is_partially_correct)
    """
    model_lower = model_answer.lower().strip()
    correct_lower = correct_answer.lower().strip()
    
    # Exact match
    if model_lower == correct_lower:
        return True, False
    
    # Check for key conclusion indicators
    yes_indicators = ['yes', 'valid', 'can be', 'is required', 'must be', 'allowed']
    no_indicators = ['no', 'invalid', 'cannot', 'is not required', 'not allowed']
    
    model_is_affirmative = any(ind in model_lower for ind in yes_indicators)
    model_is_negative = any(ind in model_lower for ind in no_indicators)
    
    correct_is_affirmative = any(ind in correct_lower for ind in yes_indicators)
    correct_is_negative = any(ind in correct_lower for ind in no_indicators)
    
    # Check if general direction matches
    if model_is_affirmative == correct_is_affirmative and model_is_negative == correct_is_negative:
        return True, False
    
    # Partial credit for relevant content
    correct_keywords = set(correct_lower.split()) - {'the', 'a', 'is', 'are', 'be', 'to', 'of'}
    model_keywords = set(model_lower.split())
    
    overlap = len(correct_keywords & model_keywords)
    if len(correct_keywords) > 0 and overlap / len(correct_keywords) > 0.5:
        return False, True
    
    return False, False


# ============= SAMPLE TEST DATA =============

def create_sample_test_data():
    """Create sample test data for demonstration"""
    
    # Sample questions with ground truth
    test_questions = [
        {
            "id": "Q001",
            "topic": "Property Transfer",
            "question": "What are the legal requirements for a valid sale deed in Sri Lanka?",
            "correct_answer": "A valid sale deed requires: written document, notarized by a licensed notary, signed by parties and witnesses, registration at Land Registry within 3 months",
            "expected_statutes": ["Prevention of Frauds Ordinance", "Registration of Documents Ordinance", "Notaries Ordinance"],
            "keywords": ["notarized", "written", "registration", "witnesses", "notary"]
        },
        {
            "id": "Q002",
            "topic": "Prescription",
            "question": "How many years of possession are required to claim prescriptive title to land in Sri Lanka?",
            "correct_answer": "10 years of uninterrupted, adverse possession is required to claim prescriptive title under the Prescription Ordinance",
            "expected_statutes": ["Prescription Ordinance"],
            "keywords": ["10 years", "possession", "adverse", "uninterrupted", "prescriptive title"]
        },
        {
            "id": "Q003",
            "topic": "Title Registration",
            "question": "What is Bim Saviya and how does it differ from the traditional deeds registration system?",
            "correct_answer": "Bim Saviya is Sri Lanka's title registration system under the Registration of Title Act. Unlike deeds registration which only records transactions, title registration guarantees ownership by the state.",
            "expected_statutes": ["Registration of Title Act"],
            "keywords": ["title registration", "guarantee", "state", "ownership", "deeds registration"]
        },
        {
            "id": "Q004",
            "topic": "Partition",
            "question": "Can co-owners of land in Sri Lanka compel partition through courts?",
            "correct_answer": "Yes, any co-owner can file a partition action under the Partition Act No. 21 of 1977 to compel division of jointly owned property",
            "expected_statutes": ["Partition Act"],
            "keywords": ["co-owner", "partition", "court", "division", "jointly owned"]
        },
        {
            "id": "Q005",
            "topic": "Mortgage",
            "question": "What happens if a mortgagor defaults on a mortgage in Sri Lanka?",
            "correct_answer": "Upon default, the mortgagee can file action to recover the debt. If unpaid, they can apply for decree to sell the mortgaged property through court auction.",
            "expected_statutes": ["Mortgage Act", "Civil Procedure Code"],
            "keywords": ["default", "sale", "court", "auction", "recover", "decree"]
        }
    ]
    
    # Sample model responses (simulating fine-tuned model output)
    model_responses = [
        {
            "id": "Q001",
            "response": """The legal requirements for a valid sale deed in Sri Lanka are governed primarily by the Prevention of Frauds Ordinance and related statutes.

**Issue:** What formalities must be observed for a valid sale of immovable property?

**Rule:** According to Section 2 of the Prevention of Frauds Ordinance, no sale of land shall be valid unless it is in writing, signed by the party disposing of the property, and attested by a licensed notary public and two witnesses.

**Application:** In practice, this means:
1. First, the deed must be in written form - oral agreements are not valid for land transfers
2. Second, the document must be attested by a licensed Notary Public under the Notaries Ordinance
3. Third, the deed must be signed by the vendor and attested by at least two witnesses
4. Finally, the deed must be registered at the relevant Land Registry within 3 months under the Registration of Documents Ordinance

**Conclusion:** Therefore, a valid sale deed requires: a written document, notarization by a licensed notary, signatures of parties and witnesses, and registration within the statutory time period."""
        },
        {
            "id": "Q002",
            "response": """To claim prescriptive title to land in Sri Lanka, certain conditions must be met under the Prescription Ordinance.

**Issue:** What is the required period of possession for prescriptive title?

**Rule:** The Prescription Ordinance establishes that title by prescription requires 10 years of continuous, uninterrupted possession that is adverse to the true owner.

**Application:** The possession must be:
- Continuous and uninterrupted for the full 10-year period
- Adverse, meaning without the owner's permission
- Open and notorious, not hidden or secret
- Exclusive possession

**Conclusion:** Therefore, 10 years of adverse, uninterrupted possession is required to successfully claim prescriptive title under Sri Lankan law."""
        },
        {
            "id": "Q003",
            "response": """Bim Saviya represents a fundamental change in Sri Lanka's land registration approach.

**Issue:** How does Bim Saviya differ from traditional deeds registration?

**Rule:** The Registration of Title Act establishes the Bim Saviya system, which provides state-guaranteed title to land.

**Application:** The key differences are:
1. Deeds registration merely records that a transaction occurred - it provides evidence but not guarantee of ownership
2. Title registration under Bim Saviya provides a state guarantee of ownership
3. Under Bim Saviya, the register is conclusive proof of ownership
4. Title registration reduces fraud and simplifies property verification

**Conclusion:** Bim Saviya is a title registration system that, unlike deeds registration, provides state-guaranteed ownership certainty."""
        },
        {
            "id": "Q004",
            "response": """The right to partition jointly owned property is well-established in Sri Lankan law.

**Issue:** Can co-owners compel partition through legal action?

**Rule:** Under the Partition Act No. 21 of 1977, any co-owner has the right to seek partition of commonly held property.

**Application:** The Act provides that:
- Any co-owner, regardless of share size, may file a partition action
- The court will order either physical division or sale
- If physical division is impractical, the court orders sale and division of proceeds

**Conclusion:** Yes, any co-owner can file a partition action under the Partition Act to compel the division of jointly owned property."""
        },
        {
            "id": "Q005",
            "response": """Default on a mortgage triggers specific legal remedies for the mortgagee.

**Issue:** What are the legal consequences of mortgage default?

**Rule:** The Mortgage Act and Civil Procedure Code govern the remedies available upon default.

**Application:** Upon default:
- The mortgagee may sue to recover the debt
- If the debt remains unpaid, application can be made for sale
- The property is sold through court-supervised auction
- Sale proceeds are applied to the debt with surplus to the mortgagor

**Conclusion:** Upon default, the mortgagee can pursue court action leading to auction sale of the mortgaged property to recover the debt."""
        }
    ]
    
    return test_questions, model_responses


# ============= MAIN EVALUATION =============

def run_evaluation():
    """Main evaluation function"""
    print("=" * 70)
    print("EXPLAINABLE LEGAL REASONING MODULE - INITIAL ACCURACY EVALUATION")
    print("=" * 70)
    print(f"Evaluation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Get test data
    test_questions, model_responses = create_sample_test_data()
    
    # Initialize metrics
    evaluations = []
    topic_metrics = defaultdict(lambda: {"correct": 0, "partial": 0, "incorrect": 0, "total": 0})
    
    print(f"Evaluating {len(test_questions)} test questions...")
    print()
    
    for question, response in zip(test_questions, model_responses):
        eval_result = ReasoningEvaluation(
            question_id=question["id"],
            topic=question["topic"]
        )
        
        # 1. Check answer correctness
        is_correct, is_partial = compare_answers(
            response["response"], 
            question["correct_answer"]
        )
        eval_result.is_correct = is_correct
        eval_result.is_partially_correct = is_partial
        
        # 2. Evaluate IRAC format
        irac = check_irac_format(response["response"])
        eval_result.irac_score = {
            "issue": irac.has_issue,
            "rule": irac.has_rule,
            "application": irac.has_application,
            "conclusion": irac.has_conclusion,
            "overall": sum([irac.has_issue, irac.has_rule, irac.has_application, irac.has_conclusion]) / 4
        }
        
        # 3. Evaluate Chain-of-Thought
        cot_metrics = evaluate_chain_of_thought(response["response"])
        eval_result.cot_score = cot_metrics["overall_score"]
        
        # 4. Check statute citations
        citation_metrics = check_statute_citations(
            response["response"],
            question["expected_statutes"]
        )
        eval_result.citation_accuracy = citation_metrics["accuracy"]
        
        # 5. Evaluate relevance
        eval_result.relevance_score = evaluate_response_relevance(
            response["response"],
            question["question"],
            question["keywords"]
        )
        
        evaluations.append(eval_result)
        
        # Update topic metrics
        topic_metrics[question["topic"]]["total"] += 1
        if is_correct:
            topic_metrics[question["topic"]]["correct"] += 1
        elif is_partial:
            topic_metrics[question["topic"]]["partial"] += 1
        else:
            topic_metrics[question["topic"]]["incorrect"] += 1
    
    # Print Results
    print()
    print("=" * 70)
    print("ACCURACY BY TOPIC")
    print("=" * 70)
    print(f"{'Topic':<25} {'Correct':>10} {'Partial':>10} {'Wrong':>10} {'Accuracy':>12}")
    print("-" * 70)
    
    for topic, metrics in topic_metrics.items():
        accuracy = (metrics["correct"] + 0.5 * metrics["partial"]) / metrics["total"] if metrics["total"] > 0 else 0
        print(f"{topic:<25} {metrics['correct']:>10} {metrics['partial']:>10} {metrics['incorrect']:>10} {accuracy:>11.1%}")
    
    # Overall metrics
    total_correct = sum(1 for e in evaluations if e.is_correct)
    total_partial = sum(1 for e in evaluations if e.is_partially_correct)
    total = len(evaluations)
    overall_accuracy = (total_correct + 0.5 * total_partial) / total if total > 0 else 0
    
    print("-" * 70)
    print(f"{'OVERALL':<25} {total_correct:>10} {total_partial:>10} {total - total_correct - total_partial:>10} {overall_accuracy:>11.1%}")
    
    print()
    print("=" * 70)
    print("IRAC FORMAT COMPLIANCE")
    print("=" * 70)
    
    irac_components = ["issue", "rule", "application", "conclusion"]
    for component in irac_components:
        present = sum(1 for e in evaluations if e.irac_score.get(component, False))
        print(f"{component.capitalize():<15}: {present}/{total} ({present/total*100:.1f}%)")
    
    avg_irac = sum(e.irac_score.get("overall", 0) for e in evaluations) / total
    print(f"{'Overall IRAC':<15}: {avg_irac*100:.1f}%")
    
    print()
    print("=" * 70)
    print("CHAIN-OF-THOUGHT QUALITY")
    print("=" * 70)
    avg_cot = sum(e.cot_score for e in evaluations) / total
    print(f"Average CoT Score: {avg_cot:.2f} / 1.00")
    
    print()
    print("=" * 70)
    print("STATUTE CITATION ACCURACY")
    print("=" * 70)
    avg_citation = sum(e.citation_accuracy for e in evaluations) / total
    print(f"Average Citation Accuracy: {avg_citation*100:.1f}%")
    
    print()
    print("=" * 70)
    print("RESPONSE RELEVANCE")
    print("=" * 70)
    avg_relevance = sum(e.relevance_score for e in evaluations) / total
    print(f"Average Relevance Score: {avg_relevance*100:.1f}%")
    
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total Questions Evaluated: {total}")
    print(f"Overall Accuracy: {overall_accuracy*100:.1f}%")
    print(f"IRAC Compliance: {avg_irac*100:.1f}%")
    print(f"CoT Quality: {avg_cot*100:.1f}%")
    print(f"Citation Accuracy: {avg_citation*100:.1f}%")
    print(f"Relevance Score: {avg_relevance*100:.1f}%")
    
    # Save report
    report = {
        "evaluation_date": datetime.now().isoformat(),
        "total_questions": total,
        "overall_accuracy": round(overall_accuracy, 4),
        "topic_metrics": dict(topic_metrics),
        "irac_compliance": round(avg_irac, 4),
        "cot_quality": round(avg_cot, 4),
        "citation_accuracy": round(avg_citation, 4),
        "relevance_score": round(avg_relevance, 4),
        "per_question_results": [
            {
                "id": e.question_id,
                "topic": e.topic,
                "correct": e.is_correct,
                "partial": e.is_partially_correct,
                "irac_score": e.irac_score,
                "cot_score": e.cot_score,
                "citation_accuracy": e.citation_accuracy,
                "relevance_score": e.relevance_score
            }
            for e in evaluations
        ]
    }
    
    with open("reasoning_evaluation_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print()
    print(f"Detailed report saved to: reasoning_evaluation_report.json")
    
    return report


if __name__ == "__main__":
    run_evaluation()
