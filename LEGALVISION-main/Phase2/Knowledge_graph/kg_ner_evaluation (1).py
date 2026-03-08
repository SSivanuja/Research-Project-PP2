"""
SpaCy NER Model - Accuracy Evaluation Script
Author: S. Sharan
Project: LegalVision (25-26J-127)

This script evaluates the custom SpaCy NER model by comparing predictions
against manually annotated ground truth.

Usage:
    python kg_ner_evaluation.py
    
    Or with SpaCy model:
    python kg_ner_evaluation.py --model ./deed_ner_model1
    
    Or with custom test data:
    python kg_ner_evaluation.py --test_data ./path/to/annotations.json

Output:
    - Console report with per-label metrics
    - ner_evaluation_report.json with detailed results
"""

import json
import os
import argparse
from datetime import datetime
from typing import Dict, List, Tuple, Any, Set
from dataclasses import dataclass
from collections import defaultdict

# Try to import spacy
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("Note: SpaCy not installed. Will use simulated predictions for demo.")


# ============= CONFIGURATION =============
DEFAULT_PATHS = {
    "test_data": "./test_data/ner_test_annotations.json",
    "model_path": "./deed_ner_model1",
    "output_report": "./ner_evaluation_report.json"
}


# ============= DATA STRUCTURES =============
@dataclass
class NERMetrics:
    """Stores metrics for a single entity label"""
    label: str
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
            "label": self.label,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1_score": round(self.f1_score, 4),
            "support": self.support
        }


# ============= NER MODEL WRAPPER =============
class NERPredictor:
    """Wrapper for SpaCy NER model or simulated predictions"""
    
    def __init__(self, model_path: str = None):
        self.nlp = None
        self.model_loaded = False
        
        if SPACY_AVAILABLE and model_path and os.path.exists(model_path):
            try:
                self.nlp = spacy.load(model_path)
                self.model_loaded = True
                print(f"Loaded SpaCy model from: {model_path}")
            except Exception as e:
                print(f"Could not load SpaCy model: {e}")
    
    def predict(self, text: str) -> List[Dict]:
        """
        Get NER predictions for text
        Returns list of {"start": int, "end": int, "label": str, "text": str}
        """
        if self.model_loaded:
            doc = self.nlp(text)
            return [
                {
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "label": ent.label_,
                    "text": ent.text
                }
                for ent in doc.ents
            ]
        else:
            # Return simulated predictions for demo
            return self._simulate_predictions(text)
    
    def _simulate_predictions(self, text: str) -> List[Dict]:
        """
        Simulate NER predictions based on keyword patterns
        This demonstrates realistic extraction behavior with some errors
        """
        predictions = []
        text_lower = text.lower()
        
        # Pattern-based extraction (simulating SpaCy behavior)
        patterns = [
            # Vendor patterns
            (r"vendor[s]?\s+(?:namely\s+)?([A-Z][A-Z\s]+?)(?:\s+of|\s+bearing|\s+NIC)", "PARTY_VENDOR"),
            (r"seller[s]?\s+([A-Z][A-Z\s]+?)(?:\s+of|\s+and)", "PARTY_VENDOR"),
            
            # Vendee patterns  
            (r"vendee[s]?\s+(?:namely\s+)?([A-Z][A-Z\s]+?)(?:\s+of|\s+bearing)", "PARTY_VENDEE"),
            (r"buyer[s]?\s+([A-Z][A-Z\s]+?)(?:\s+of)", "PARTY_VENDEE"),
            
            # Donor patterns
            (r"donor[s]?\s+(?:namely\s+)?([A-Z][A-Z\s]+?)(?:\s+of|\s+in)", "PARTY_DONOR"),
            (r"gift\s+from\s+([A-Z][A-Z\s]+?)(?:\s+mother|\s+father|\s+to)", "PARTY_DONOR"),
            
            # Donee patterns
            (r"donee[s]?\s+(?:namely\s+)?([A-Z][A-Z\s]+?)(?:\s+of|\s+bearing)", "PARTY_DONEE"),
            (r"(?:son|daughter)\s+([A-Z][A-Z\s]+?)(?:\s+and|\s+all|\s+of)", "PARTY_DONEE"),
            
            # Mortgagor patterns
            (r"mortgagor[s]?\s+(?:namely\s+)?([A-Z][A-Z\s]+?)(?:\s+of|\s+in)", "PARTY_MORTGAGOR"),
            
            # Mortgagee patterns
            (r"mortgagee[s]?\s+(?:namely\s+)?([A-Z][A-Z\s]+?)(?:\s+having|\s+for)", "PARTY_MORTGAGEE"),
            
            # Lessor patterns
            (r"lessor[s]?\s+(?:namely\s+)?([A-Z][A-Z\s]+?)(?:\s+of|\s+and)", "PARTY_LESSOR"),
            (r"owner\s+namely\s+([A-Z][A-Z\s]+?)(?:\s+of|\s+as)", "PARTY_LESSOR"),
            
            # Lessee patterns
            (r"lessee[s]?\s+(?:namely\s+)?([A-Z][A-Z\s]+?)(?:\s+of|\s+for)", "PARTY_LESSEE"),
            (r"tenant\s+namely\s+([A-Z][A-Z\s]+?)(?:\s+for)", "PARTY_LESSEE"),
        ]
        
        import re
        for pattern, label in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                name = match.group(1).strip()
                # Find actual position in original text
                start_search = text.upper().find(name.upper())
                if start_search >= 0:
                    predictions.append({
                        "start": start_search,
                        "end": start_search + len(name),
                        "label": label,
                        "text": text[start_search:start_search + len(name)]
                    })
        
        return predictions


# ============= EVALUATION FUNCTIONS =============

def entity_to_tuple(entity: Dict) -> Tuple[int, int, str]:
    """Convert entity dict to comparable tuple"""
    return (entity["start"], entity["end"], entity["label"])


def evaluate_sample(predictions: List[Dict], ground_truth: List[Dict], 
                   tolerance: int = 5) -> Dict[str, NERMetrics]:
    """
    Evaluate predictions against ground truth for a single sample
    
    Args:
        predictions: List of predicted entities
        ground_truth: List of ground truth entities
        tolerance: Character tolerance for boundary matching
    
    Returns:
        Dict of label -> NERMetrics
    """
    metrics = {}
    
    # Get all labels
    all_labels = set()
    for ent in ground_truth:
        all_labels.add(ent["label"])
    for ent in predictions:
        all_labels.add(ent["label"])
    
    # Initialize metrics for all labels
    for label in all_labels:
        metrics[label] = NERMetrics(label=label)
    
    # Match predictions to ground truth
    matched_gt = set()
    matched_pred = set()
    
    for i, pred in enumerate(predictions):
        for j, gt in enumerate(ground_truth):
            if j in matched_gt:
                continue
            
            # Check if same label and overlapping/close boundaries
            if pred["label"] == gt["label"]:
                # Check boundary overlap with tolerance
                start_match = abs(pred["start"] - gt["start"]) <= tolerance
                end_match = abs(pred["end"] - gt["end"]) <= tolerance
                
                # Or check text overlap
                pred_text = pred.get("text", "").lower()
                gt_text = gt.get("text", "").lower()
                text_match = pred_text in gt_text or gt_text in pred_text
                
                if (start_match and end_match) or text_match:
                    metrics[pred["label"]].true_positives += 1
                    matched_gt.add(j)
                    matched_pred.add(i)
                    break
    
    # Count false positives (predictions not matched)
    for i, pred in enumerate(predictions):
        if i not in matched_pred:
            metrics[pred["label"]].false_positives += 1
    
    # Count false negatives (ground truth not matched)
    for j, gt in enumerate(ground_truth):
        if j not in matched_gt:
            metrics[gt["label"]].false_negatives += 1
    
    return metrics


def merge_metrics(all_metrics: List[Dict[str, NERMetrics]]) -> Dict[str, NERMetrics]:
    """Merge metrics from multiple samples"""
    merged = {}
    
    for sample_metrics in all_metrics:
        for label, metrics in sample_metrics.items():
            if label not in merged:
                merged[label] = NERMetrics(label=label)
            merged[label].true_positives += metrics.true_positives
            merged[label].false_positives += metrics.false_positives
            merged[label].false_negatives += metrics.false_negatives
    
    return merged


def calculate_aggregate(metrics: Dict[str, NERMetrics]) -> Dict:
    """Calculate micro and macro averages"""
    
    total_tp = sum(m.true_positives for m in metrics.values())
    total_fp = sum(m.false_positives for m in metrics.values())
    total_fn = sum(m.false_negatives for m in metrics.values())
    
    # Micro average
    micro_p = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    micro_r = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    micro_f1 = 2 * micro_p * micro_r / (micro_p + micro_r) if (micro_p + micro_r) > 0 else 0
    
    # Macro average
    valid = [m for m in metrics.values() if m.support > 0]
    macro_p = sum(m.precision for m in valid) / len(valid) if valid else 0
    macro_r = sum(m.recall for m in valid) / len(valid) if valid else 0
    macro_f1 = sum(m.f1_score for m in valid) / len(valid) if valid else 0
    
    return {
        "micro": {"precision": round(micro_p, 4), "recall": round(micro_r, 4), "f1_score": round(micro_f1, 4)},
        "macro": {"precision": round(macro_p, 4), "recall": round(macro_r, 4), "f1_score": round(macro_f1, 4)},
        "totals": {"true_positives": total_tp, "false_positives": total_fp, "false_negatives": total_fn}
    }


# ============= MAIN EVALUATION RUNNER =============

def run_evaluation(test_data_path: str, model_path: str, output_path: str):
    """Main evaluation function"""
    
    print("=" * 70)
    print("SPACY NER MODEL - ACCURACY EVALUATION")
    print("=" * 70)
    print(f"Evaluation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Load test data
    print(f"Loading test annotations from: {test_data_path}")
    with open(test_data_path, 'r') as f:
        test_data = json.load(f)
    
    samples = test_data.get("test_samples", [])
    print(f"Test samples loaded: {len(samples)}")
    print()
    
    # Initialize predictor
    predictor = NERPredictor(model_path)
    if not predictor.model_loaded:
        print("Running with simulated predictions (model not loaded)")
    print()
    
    # Evaluate each sample
    all_sample_metrics = []
    sample_results = []
    
    print("Evaluating samples...")
    print("-" * 70)
    
    for sample in samples:
        sample_id = sample["id"]
        text = sample["text"]
        ground_truth = sample["entities"]
        
        # Get predictions
        predictions = predictor.predict(text)
        
        # Evaluate
        sample_metrics = evaluate_sample(predictions, ground_truth)
        all_sample_metrics.append(sample_metrics)
        
        # Calculate sample F1
        tp = sum(m.true_positives for m in sample_metrics.values())
        fp = sum(m.false_positives for m in sample_metrics.values())
        fn = sum(m.false_negatives for m in sample_metrics.values())
        f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) > 0 else 0
        
        print(f"  {sample_id}: F1={f1:.4f} (TP:{tp}, FP:{fp}, FN:{fn}) | GT:{len(ground_truth)} Pred:{len(predictions)}")
        
        sample_results.append({
            "sample_id": sample_id,
            "ground_truth_count": len(ground_truth),
            "prediction_count": len(predictions),
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "f1_score": round(f1, 4)
        })
    
    # Merge all metrics
    merged_metrics = merge_metrics(all_sample_metrics)
    aggregate = calculate_aggregate(merged_metrics)
    
    # Print results
    print()
    print("=" * 70)
    print("PER-LABEL ACCURACY")
    print("=" * 70)
    print(f"{'Entity Label':<20} {'Precision':>10} {'Recall':>10} {'F1 Score':>10} {'Support':>10}")
    print("-" * 70)
    
    for label in sorted(merged_metrics.keys()):
        m = merged_metrics[label]
        print(f"{label:<20} {m.precision:>10.4f} {m.recall:>10.4f} {m.f1_score:>10.4f} {m.support:>10}")
    
    print("-" * 70)
    print(f"{'MICRO AVERAGE':<20} {aggregate['micro']['precision']:>10.4f} {aggregate['micro']['recall']:>10.4f} {aggregate['micro']['f1_score']:>10.4f}")
    print(f"{'MACRO AVERAGE':<20} {aggregate['macro']['precision']:>10.4f} {aggregate['macro']['recall']:>10.4f} {aggregate['macro']['f1_score']:>10.4f}")
    
    print()
    print("=" * 70)
    print("CONFUSION MATRIX SUMMARY")
    print("=" * 70)
    print(f"Total True Positives:  {aggregate['totals']['true_positives']}")
    print(f"Total False Positives: {aggregate['totals']['false_positives']}")
    print(f"Total False Negatives: {aggregate['totals']['false_negatives']}")
    
    # Analysis
    print()
    print("=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    
    valid_metrics = {k: v for k, v in merged_metrics.items() if v.support > 0}
    if valid_metrics:
        best = max(valid_metrics.items(), key=lambda x: x[1].f1_score)
        worst = min(valid_metrics.items(), key=lambda x: x[1].f1_score)
        print(f"Best Performing:  {best[0]} (F1: {best[1].f1_score:.4f})")
        print(f"Needs Improvement: {worst[0]} (F1: {worst[1].f1_score:.4f})")
    
    # Summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total Samples Evaluated: {len(samples)}")
    print(f"Model Loaded: {'Yes' if predictor.model_loaded else 'No (using simulated predictions)'}")
    print(f"Overall Accuracy (Micro F1): {aggregate['micro']['f1_score']:.2%}")
    print(f"Overall Accuracy (Macro F1): {aggregate['macro']['f1_score']:.2%}")
    
    # Save report
    report = {
        "evaluation_date": datetime.now().isoformat(),
        "test_data_file": test_data_path,
        "model_path": model_path,
        "model_loaded": predictor.model_loaded,
        "total_samples": len(samples),
        "label_metrics": {k: v.to_dict() for k, v in merged_metrics.items()},
        "aggregate_metrics": aggregate,
        "sample_results": sample_results
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to: {output_path}")
    
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate SpaCy NER model accuracy")
    parser.add_argument("--test_data", type=str, default=DEFAULT_PATHS["test_data"],
                       help="Path to test annotations JSON file")
    parser.add_argument("--model", type=str, default=DEFAULT_PATHS["model_path"],
                       help="Path to SpaCy model directory")
    parser.add_argument("--output", type=str, default=DEFAULT_PATHS["output_report"],
                       help="Path for output report JSON")
    
    args = parser.parse_args()
    
    # Check if test data exists
    if not os.path.exists(args.test_data):
        print(f"Error: Test data file not found: {args.test_data}")
        print("Please ensure test_data/ner_test_annotations.json exists")
        exit(1)
    
    run_evaluation(args.test_data, args.model, args.output)
