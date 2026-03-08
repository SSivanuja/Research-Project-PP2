"""
Knowledge Graph Entity Extraction - Accuracy Evaluation Script
Author: S. Sharan
Project: LegalVision (25-26J-127)

This script evaluates the accuracy of the deed extraction pipeline by comparing
extracted data against manually annotated ground truth.

Usage:
    python kg_accuracy_evaluation.py
    
    Or with custom paths:
    python kg_accuracy_evaluation.py --ground_truth ./path/to/ground_truth.json --extracted ./path/to/extracted.json

Output:
    - Console report with accuracy metrics
    - kg_evaluation_report.json with detailed results
"""

import json
import os
import argparse
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict


# ============= CONFIGURATION =============
DEFAULT_PATHS = {
    "ground_truth": "./test_data/ground_truth_deeds.json",
    "extracted": "./test_data/extracted_deeds.json",
    "output_report": "./kg_evaluation_report.json"
}


# ============= DATA STRUCTURES =============
@dataclass
class EntityMetrics:
    """Stores evaluation metrics for a single entity type"""
    entity_type: str
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    
    @property
    def precision(self) -> float:
        denom = self.true_positives + self.false_positives
        return self.true_positives / denom if denom > 0 else 0.0
    
    @property
    def recall(self) -> float:
        denom = self.true_positives + self.false_negatives
        return self.true_positives / denom if denom > 0 else 0.0
    
    @property
    def f1_score(self) -> float:
        if self.precision + self.recall == 0:
            return 0.0
        return 2 * (self.precision * self.recall) / (self.precision + self.recall)
    
    @property
    def support(self) -> int:
        return self.true_positives + self.false_negatives
    
    def to_dict(self) -> Dict:
        return {
            "entity_type": self.entity_type,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1_score": round(self.f1_score, 4),
            "support": self.support
        }


# ============= HELPER FUNCTIONS =============

def normalize_string(s: Any) -> str:
    """Normalize string for comparison"""
    if s is None:
        return ""
    return str(s).lower().strip()


def get_nested_value(data: Dict, path: str) -> Any:
    """Get value from nested dictionary using dot notation"""
    if not data:
        return None
    
    keys = path.split('.')
    current = data
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current


def compare_simple_value(extracted: Any, ground_truth: Any) -> Tuple[bool, str]:
    """Compare simple values (strings, numbers)"""
    if extracted is None and ground_truth is None:
        return True, "both_null"
    if extracted is None:
        return False, "missing"
    if ground_truth is None:
        return False, "extra"
    
    ext_norm = normalize_string(extracted)
    gt_norm = normalize_string(ground_truth)
    
    if ext_norm == gt_norm:
        return True, "exact_match"
    if ext_norm in gt_norm or gt_norm in ext_norm:
        return True, "partial_match"
    return False, "mismatch"


def compare_list_values(extracted: List, ground_truth: List) -> Tuple[int, int, int]:
    """
    Compare lists and return (matches, extra, missing)
    """
    if not extracted and not ground_truth:
        return 0, 0, 0
    
    ext_set = set(normalize_string(x) for x in (extracted or []))
    gt_set = set(normalize_string(x) for x in (ground_truth or []))
    
    matches = len(ext_set & gt_set)
    extra = len(ext_set - gt_set)
    missing = len(gt_set - ext_set)
    
    return matches, extra, missing


def compare_party_lists(extracted: List[Dict], ground_truth: List[Dict]) -> Tuple[int, int, int]:
    """Compare party lists by name"""
    if not extracted and not ground_truth:
        return 0, 0, 0
    
    def get_names(party_list):
        names = set()
        for p in (party_list or []):
            if isinstance(p, dict) and 'name' in p:
                names.add(normalize_string(p['name']))
            elif isinstance(p, str):
                names.add(normalize_string(p))
        return names
    
    ext_names = get_names(extracted)
    gt_names = get_names(ground_truth)
    
    # Check for partial matches too
    matches = 0
    matched_gt = set()
    
    for ext_name in ext_names:
        for gt_name in gt_names:
            if gt_name not in matched_gt:
                if ext_name == gt_name or ext_name in gt_name or gt_name in ext_name:
                    matches += 1
                    matched_gt.add(gt_name)
                    break
    
    extra = len(ext_names) - matches
    missing = len(gt_names) - matches
    
    return max(matches, 0), max(extra, 0), max(missing, 0)


# ============= MAIN EVALUATION LOGIC =============

def evaluate_document(extracted: Dict, ground_truth: Dict) -> Dict[str, EntityMetrics]:
    """Evaluate a single document's extraction against ground truth"""
    
    metrics = {}
    
    # Define entity mappings: (extracted_path, ground_truth_path, entity_name, comparison_type)
    entity_mappings = [
        # Instrument fields
        ("instrument.code_number", "instrument.code_number", "code_number", "simple"),
        ("instrument.type", "instrument.type", "deed_type", "simple"),
        ("instrument.date", "instrument.date", "deed_date", "simple"),
        ("instrument.consideration_lkr", "instrument.consideration_lkr", "consideration", "simple"),
        
        # Party fields
        ("parties.vendors", "parties.vendors", "vendors", "party_list"),
        ("parties.vendees", "parties.vendees", "vendees", "party_list"),
        ("parties.donors", "parties.donors", "donors", "party_list"),
        ("parties.donees", "parties.donees", "donees", "party_list"),
        ("parties.mortgagors", "parties.mortgagors", "mortgagors", "party_list"),
        ("parties.mortgagees", "parties.mortgagees", "mortgagees", "party_list"),
        ("parties.lessors", "parties.lessors", "lessors", "party_list"),
        ("parties.lessees", "parties.lessees", "lessees", "party_list"),
        
        # Property fields
        ("property.plan_no", "property.plan_no", "plan_number", "simple"),
        ("property.lots", "property.lots", "lot_numbers", "list"),
        ("property.extent", "property.extent", "extent", "simple"),
        ("property.boundaries.north", "property.boundaries.north", "boundary_north", "simple"),
        ("property.boundaries.east", "property.boundaries.east", "boundary_east", "simple"),
        ("property.boundaries.south", "property.boundaries.south", "boundary_south", "simple"),
        ("property.boundaries.west", "property.boundaries.west", "boundary_west", "simple"),
        
        # Administrative fields
        ("administrative.district", "administrative.district", "district", "simple"),
        ("administrative.province", "administrative.province", "province", "simple"),
        ("administrative.registry_office", "administrative.registry_office", "registry_office", "simple"),
        
        # IDs
        ("ids.nic_numbers", "ids.nic_numbers", "nic_numbers", "list"),
        
        # Prior deeds
        ("prior_deeds", "prior_deeds", "prior_deeds", "prior_deed_list"),
    ]
    
    for ext_path, gt_path, entity_name, comp_type in entity_mappings:
        if entity_name not in metrics:
            metrics[entity_name] = EntityMetrics(entity_type=entity_name)
        
        ext_value = get_nested_value(extracted, ext_path)
        gt_value = get_nested_value(ground_truth, gt_path)
        
        if comp_type == "simple":
            # Skip if both are None/empty
            if gt_value is None and ext_value is None:
                continue
            
            match, match_type = compare_simple_value(ext_value, gt_value)
            
            if gt_value is not None:  # There's something to find
                if match:
                    metrics[entity_name].true_positives += 1
                else:
                    metrics[entity_name].false_negatives += 1
                    if ext_value is not None:
                        metrics[entity_name].false_positives += 1
            elif ext_value is not None:  # Extracted something that shouldn't exist
                metrics[entity_name].false_positives += 1
                
        elif comp_type == "list":
            matches, extra, missing = compare_list_values(ext_value, gt_value)
            metrics[entity_name].true_positives += matches
            metrics[entity_name].false_positives += extra
            metrics[entity_name].false_negatives += missing
            
        elif comp_type == "party_list":
            matches, extra, missing = compare_party_lists(ext_value, gt_value)
            metrics[entity_name].true_positives += matches
            metrics[entity_name].false_positives += extra
            metrics[entity_name].false_negatives += missing
            
        elif comp_type == "prior_deed_list":
            # Handle prior deeds which might be list of dicts or list of strings
            ext_refs = []
            gt_refs = []
            
            for item in (ext_value or []):
                if isinstance(item, dict):
                    ext_refs.append(item.get('reference', ''))
                else:
                    ext_refs.append(str(item))
            
            for item in (gt_value or []):
                if isinstance(item, dict):
                    gt_refs.append(item.get('reference', ''))
                else:
                    gt_refs.append(str(item))
            
            matches, extra, missing = compare_list_values(ext_refs, gt_refs)
            metrics[entity_name].true_positives += matches
            metrics[entity_name].false_positives += extra
            metrics[entity_name].false_negatives += missing
    
    return metrics


def calculate_aggregate_metrics(all_metrics: Dict[str, EntityMetrics]) -> Dict:
    """Calculate micro and macro averages"""
    
    total_tp = sum(m.true_positives for m in all_metrics.values())
    total_fp = sum(m.false_positives for m in all_metrics.values())
    total_fn = sum(m.false_negatives for m in all_metrics.values())
    
    # Micro average
    micro_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    micro_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    micro_f1 = 2 * (micro_precision * micro_recall) / (micro_precision + micro_recall) if (micro_precision + micro_recall) > 0 else 0
    
    # Macro average (only for entities with support > 0)
    valid_metrics = [m for m in all_metrics.values() if m.support > 0]
    macro_precision = sum(m.precision for m in valid_metrics) / len(valid_metrics) if valid_metrics else 0
    macro_recall = sum(m.recall for m in valid_metrics) / len(valid_metrics) if valid_metrics else 0
    macro_f1 = sum(m.f1_score for m in valid_metrics) / len(valid_metrics) if valid_metrics else 0
    
    return {
        "micro": {
            "precision": round(micro_precision, 4),
            "recall": round(micro_recall, 4),
            "f1_score": round(micro_f1, 4)
        },
        "macro": {
            "precision": round(macro_precision, 4),
            "recall": round(macro_recall, 4),
            "f1_score": round(macro_f1, 4)
        },
        "totals": {
            "true_positives": total_tp,
            "false_positives": total_fp,
            "false_negatives": total_fn
        }
    }


def analyze_quality_scores(documents: List[Dict]) -> Dict:
    """Analyze quality score distribution"""
    
    distribution = {"EXCELLENT": 0, "GOOD": 0, "REVIEW": 0, "POOR": 0}
    scores = []
    
    for doc in documents:
        ext_data = doc.get("extracted_data", doc)
        if "quality" in ext_data:
            score = ext_data["quality"].get("score", 0)
            rating = ext_data["quality"].get("rating", "UNKNOWN")
            scores.append(score)
            if rating in distribution:
                distribution[rating] += 1
    
    return {
        "distribution": distribution,
        "average_score": round(sum(scores) / len(scores), 2) if scores else 0,
        "min_score": min(scores) if scores else 0,
        "max_score": max(scores) if scores else 0,
        "total_evaluated": len(scores)
    }


# ============= MAIN EVALUATION RUNNER =============

def run_evaluation(ground_truth_path: str, extracted_path: str, output_path: str):
    """Main evaluation function"""
    
    print("=" * 70)
    print("KNOWLEDGE GRAPH MODULE - ENTITY EXTRACTION ACCURACY EVALUATION")
    print("=" * 70)
    print(f"Evaluation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Load data
    print(f"Loading ground truth from: {ground_truth_path}")
    with open(ground_truth_path, 'r') as f:
        ground_truth_data = json.load(f)
    
    print(f"Loading extracted data from: {extracted_path}")
    with open(extracted_path, 'r') as f:
        extracted_data = json.load(f)
    
    gt_documents = ground_truth_data.get("documents", [])
    ext_documents = extracted_data.get("documents", [])
    
    print(f"\nGround Truth Documents: {len(gt_documents)}")
    print(f"Extracted Documents: {len(ext_documents)}")
    print()
    
    # Create lookup by file_id
    gt_lookup = {doc["file_id"]: doc["ground_truth"] for doc in gt_documents}
    ext_lookup = {doc["file_id"]: doc["extracted_data"] for doc in ext_documents}
    
    # Evaluate each document
    aggregate_metrics = {}
    document_results = []
    
    print("Evaluating documents...")
    print("-" * 70)
    
    for file_id in gt_lookup:
        if file_id not in ext_lookup:
            print(f"  {file_id}: NOT FOUND in extracted data")
            continue
        
        gt_doc = gt_lookup[file_id]
        ext_doc = ext_lookup[file_id]
        
        doc_metrics = evaluate_document(ext_doc, gt_doc)
        
        # Merge into aggregate
        for entity_name, metrics in doc_metrics.items():
            if entity_name not in aggregate_metrics:
                aggregate_metrics[entity_name] = EntityMetrics(entity_type=entity_name)
            aggregate_metrics[entity_name].true_positives += metrics.true_positives
            aggregate_metrics[entity_name].false_positives += metrics.false_positives
            aggregate_metrics[entity_name].false_negatives += metrics.false_negatives
        
        # Calculate document-level F1
        doc_tp = sum(m.true_positives for m in doc_metrics.values())
        doc_fp = sum(m.false_positives for m in doc_metrics.values())
        doc_fn = sum(m.false_negatives for m in doc_metrics.values())
        doc_f1 = 2 * doc_tp / (2 * doc_tp + doc_fp + doc_fn) if (2 * doc_tp + doc_fp + doc_fn) > 0 else 0
        
        print(f"  {file_id}: F1 = {doc_f1:.4f} (TP:{doc_tp}, FP:{doc_fp}, FN:{doc_fn})")
        
        document_results.append({
            "file_id": file_id,
            "f1_score": round(doc_f1, 4),
            "true_positives": doc_tp,
            "false_positives": doc_fp,
            "false_negatives": doc_fn
        })
    
    # Calculate aggregates
    aggregate = calculate_aggregate_metrics(aggregate_metrics)
    
    # Print results
    print()
    print("=" * 70)
    print("ENTITY-LEVEL ACCURACY")
    print("=" * 70)
    print(f"{'Entity Type':<20} {'Precision':>10} {'Recall':>10} {'F1 Score':>10} {'Support':>10}")
    print("-" * 70)
    
    # Sort by entity name
    for entity_name in sorted(aggregate_metrics.keys()):
        m = aggregate_metrics[entity_name]
        if m.support > 0:  # Only show entities with data
            print(f"{entity_name:<20} {m.precision:>10.4f} {m.recall:>10.4f} {m.f1_score:>10.4f} {m.support:>10}")
    
    print("-" * 70)
    print(f"{'MICRO AVERAGE':<20} {aggregate['micro']['precision']:>10.4f} {aggregate['micro']['recall']:>10.4f} {aggregate['micro']['f1_score']:>10.4f}")
    print(f"{'MACRO AVERAGE':<20} {aggregate['macro']['precision']:>10.4f} {aggregate['macro']['recall']:>10.4f} {aggregate['macro']['f1_score']:>10.4f}")
    
    # Quality analysis
    quality_analysis = analyze_quality_scores(ext_documents)
    
    print()
    print("=" * 70)
    print("QUALITY SCORE DISTRIBUTION")
    print("=" * 70)
    
    total_quality = quality_analysis["total_evaluated"]
    for rating, count in quality_analysis["distribution"].items():
        pct = (count / total_quality * 100) if total_quality > 0 else 0
        print(f"{rating:<12}: {count:>3} ({pct:>5.1f}%)")
    
    print(f"\nAverage Quality Score: {quality_analysis['average_score']:.1f} / 100")
    
    # Summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total Documents Evaluated: {len(document_results)}")
    print(f"Overall Extraction Accuracy (Micro F1): {aggregate['micro']['f1_score']:.2%}")
    print(f"Overall Extraction Accuracy (Macro F1): {aggregate['macro']['f1_score']:.2%}")
    print(f"Total True Positives: {aggregate['totals']['true_positives']}")
    print(f"Total False Positives: {aggregate['totals']['false_positives']}")
    print(f"Total False Negatives: {aggregate['totals']['false_negatives']}")
    
    # Save report
    report = {
        "evaluation_date": datetime.now().isoformat(),
        "ground_truth_file": ground_truth_path,
        "extracted_file": extracted_path,
        "total_documents": len(document_results),
        "entity_metrics": {k: v.to_dict() for k, v in aggregate_metrics.items()},
        "aggregate_metrics": aggregate,
        "quality_analysis": quality_analysis,
        "document_results": document_results
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to: {output_path}")
    
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Knowledge Graph extraction accuracy")
    parser.add_argument("--ground_truth", type=str, default=DEFAULT_PATHS["ground_truth"],
                       help="Path to ground truth JSON file")
    parser.add_argument("--extracted", type=str, default=DEFAULT_PATHS["extracted"],
                       help="Path to extracted data JSON file")
    parser.add_argument("--output", type=str, default=DEFAULT_PATHS["output_report"],
                       help="Path for output report JSON")
    
    args = parser.parse_args()
    
    # Check if files exist
    if not os.path.exists(args.ground_truth):
        print(f"Error: Ground truth file not found: {args.ground_truth}")
        print("Please ensure test_data/ground_truth_deeds.json exists")
        exit(1)
    
    if not os.path.exists(args.extracted):
        print(f"Error: Extracted data file not found: {args.extracted}")
        print("Please ensure test_data/extracted_deeds.json exists")
        exit(1)
    
    run_evaluation(args.ground_truth, args.extracted, args.output)
