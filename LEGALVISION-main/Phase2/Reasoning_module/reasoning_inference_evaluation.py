"""
Model Inference and Human Evaluation Framework - Explainable Legal Reasoning Module
Author: S. Sivanuja
Project: LegalVision (25-26J-127)

This script provides:
1. Model inference for generating responses to test questions
2. Human evaluation scoring framework
3. Inter-rater reliability calculation
4. Training loss analysis

Run this after fine-tuning to test the model and collect human evaluations.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import statistics

# Try to import ML libraries
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("Warning: PyTorch/Transformers not installed. Using sample data mode.")

try:
    from unsloth import FastLanguageModel
    UNSLOTH_AVAILABLE = True
except ImportError:
    UNSLOTH_AVAILABLE = False


# ============= CONFIGURATION =============
CONFIG = {
    "model_path": "./legalvision_lora",  # Path to fine-tuned LoRA weights
    "base_model": "unsloth/Meta-Llama-3.1-8B-bnb-4bit",
    "max_new_tokens": 1024,
    "temperature": 0.3,
    "test_questions_file": "./test_questions.json",
    "output_dir": "./evaluation_outputs"
}


# ============= DATA STRUCTURES =============

@dataclass
class HumanEvaluation:
    """Stores human evaluation scores for a single response"""
    question_id: str
    evaluator_id: str
    legal_accuracy: float = 0.0      # 1-5 scale
    practical_usefulness: float = 0.0  # 1-5 scale
    clarity: float = 0.0              # 1-5 scale
    appropriate_caveats: float = 0.0  # 1-5 scale
    would_recommend: float = 0.0      # 1-5 scale
    comments: str = ""
    
    @property
    def overall_score(self) -> float:
        return (self.legal_accuracy + self.practical_usefulness + 
                self.clarity + self.appropriate_caveats + 
                self.would_recommend) / 5


@dataclass
class TrainingMetrics:
    """Stores training metrics for analysis"""
    epoch: int
    train_loss: float
    eval_loss: Optional[float] = None
    learning_rate: float = 0.0
    gpu_memory_gb: float = 0.0


# ============= MODEL INFERENCE =============

class LegalReasoningInference:
    """Handles model loading and inference"""
    
    def __init__(self, model_path: str = None, base_model: str = None):
        self.model = None
        self.tokenizer = None
        self.model_loaded = False
        
        if UNSLOTH_AVAILABLE and model_path and os.path.exists(model_path):
            try:
                self.model, self.tokenizer = FastLanguageModel.from_pretrained(
                    model_name=model_path,
                    max_seq_length=2048,
                    dtype=None,
                    load_in_4bit=True,
                )
                FastLanguageModel.for_inference(self.model)
                self.model_loaded = True
                print(f"Model loaded from: {model_path}")
            except Exception as e:
                print(f"Could not load model: {e}")
        elif TORCH_AVAILABLE and base_model:
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(base_model)
                self.model = AutoModelForCausalLM.from_pretrained(
                    base_model,
                    torch_dtype=torch.float16,
                    device_map="auto"
                )
                self.model_loaded = True
                print(f"Base model loaded: {base_model}")
            except Exception as e:
                print(f"Could not load model: {e}")
    
    def generate_response(self, question: str, system_prompt: str = None) -> str:
        """Generate a response for a given question"""
        
        if not self.model_loaded:
            return self._get_sample_response(question)
        
        # Format prompt
        if system_prompt is None:
            system_prompt = """You are a legal expert specializing in Sri Lankan property law. 
Provide clear, accurate legal analysis using the IRAC format (Issue, Rule, Application, Conclusion).
Always cite relevant statutes and explain your reasoning step by step."""
        
        # Llama 3 chat template
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>

{question}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
        
        # Generate
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=CONFIG["max_new_tokens"],
                temperature=CONFIG["temperature"],
                do_sample=True,
                top_p=0.9,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract just the assistant's response
        if "<|start_header_id|>assistant<|end_header_id|>" in response:
            response = response.split("<|start_header_id|>assistant<|end_header_id|>")[-1]
        
        return response.strip()
    
    def _get_sample_response(self, question: str) -> str:
        """Return sample response when model not available"""
        # This would be replaced with actual model output
        sample_responses = {
            "transfer": """**Issue:** What are the requirements for valid property transfer?

**Rule:** Under the Prevention of Frauds Ordinance and Registration of Documents Ordinance, property transfers must be in writing, notarized, and registered.

**Application:** The transfer requires:
1. Written deed document
2. Attestation by licensed Notary Public
3. Signatures of parties and witnesses
4. Registration within 3 months

**Conclusion:** A valid transfer requires written documentation, notarization, and registration.""",
            
            "prescription": """**Issue:** What constitutes valid prescriptive title claim?

**Rule:** The Prescription Ordinance requires 10 years of adverse possession.

**Application:** The possession must be:
1. Continuous for 10 years
2. Adverse to the true owner
3. Open and notorious
4. Exclusive

**Conclusion:** 10 years of uninterrupted adverse possession establishes prescriptive title.""",
            
            "default": """**Issue:** Legal question analysis required.

**Rule:** Relevant Sri Lankan statutes apply.

**Application:** Based on the facts and applicable law, the legal analysis proceeds through established principles.

**Conclusion:** The answer depends on specific circumstances and applicable statutory provisions."""
        }
        
        question_lower = question.lower()
        if "transfer" in question_lower or "sale" in question_lower:
            return sample_responses["transfer"]
        elif "prescription" in question_lower or "possession" in question_lower:
            return sample_responses["prescription"]
        else:
            return sample_responses["default"]


# ============= HUMAN EVALUATION FRAMEWORK =============

class HumanEvaluationCollector:
    """Collects and analyzes human evaluation scores"""
    
    def __init__(self):
        self.evaluations: List[HumanEvaluation] = []
    
    def add_evaluation(self, evaluation: HumanEvaluation):
        """Add a human evaluation"""
        self.evaluations.append(evaluation)
    
    def get_evaluations_for_question(self, question_id: str) -> List[HumanEvaluation]:
        """Get all evaluations for a specific question"""
        return [e for e in self.evaluations if e.question_id == question_id]
    
    def calculate_inter_rater_reliability(self, question_id: str) -> Dict[str, float]:
        """
        Calculate inter-rater reliability metrics for a question
        Uses correlation and agreement percentage
        """
        evals = self.get_evaluations_for_question(question_id)
        
        if len(evals) < 2:
            return {"error": "Need at least 2 evaluators"}
        
        metrics = {}
        dimensions = ["legal_accuracy", "practical_usefulness", "clarity", 
                     "appropriate_caveats", "would_recommend"]
        
        # Calculate average score difference
        total_diff = 0
        count = 0
        
        for i, e1 in enumerate(evals):
            for e2 in evals[i+1:]:
                for dim in dimensions:
                    diff = abs(getattr(e1, dim) - getattr(e2, dim))
                    total_diff += diff
                    count += 1
        
        avg_diff = total_diff / count if count > 0 else 0
        
        # Calculate agreement (within 1 point)
        agreements = 0
        total_comparisons = 0
        
        for i, e1 in enumerate(evals):
            for e2 in evals[i+1:]:
                for dim in dimensions:
                    if abs(getattr(e1, dim) - getattr(e2, dim)) <= 1:
                        agreements += 1
                    total_comparisons += 1
        
        agreement_rate = agreements / total_comparisons if total_comparisons > 0 else 0
        
        metrics["average_score_difference"] = round(avg_diff, 2)
        metrics["agreement_rate"] = round(agreement_rate, 2)
        metrics["num_evaluators"] = len(evals)
        
        return metrics
    
    def get_aggregate_scores(self) -> Dict[str, Dict[str, float]]:
        """Get aggregate scores across all evaluations"""
        if not self.evaluations:
            return {}
        
        dimensions = ["legal_accuracy", "practical_usefulness", "clarity", 
                     "appropriate_caveats", "would_recommend", "overall_score"]
        
        result = {}
        for dim in dimensions:
            scores = [getattr(e, dim) if dim != "overall_score" else e.overall_score 
                     for e in self.evaluations]
            result[dim] = {
                "mean": round(statistics.mean(scores), 2),
                "std": round(statistics.stdev(scores), 2) if len(scores) > 1 else 0,
                "min": round(min(scores), 2),
                "max": round(max(scores), 2)
            }
        
        return result


# ============= TRAINING ANALYSIS =============

def analyze_training_metrics(metrics: List[TrainingMetrics]) -> Dict:
    """Analyze training metrics to identify issues"""
    
    if not metrics:
        return {"error": "No training metrics provided"}
    
    analysis = {
        "total_epochs": len(metrics),
        "initial_loss": metrics[0].train_loss,
        "final_loss": metrics[-1].train_loss,
        "loss_reduction": round(metrics[0].train_loss - metrics[-1].train_loss, 4),
        "loss_reduction_pct": round((metrics[0].train_loss - metrics[-1].train_loss) / metrics[0].train_loss * 100, 1),
        "best_epoch": 1,
        "best_eval_loss": metrics[0].eval_loss if metrics[0].eval_loss else metrics[0].train_loss,
        "training_stable": True,
        "overfitting_detected": False
    }
    
    # Find best epoch
    for i, m in enumerate(metrics):
        loss = m.eval_loss if m.eval_loss else m.train_loss
        if loss < analysis["best_eval_loss"]:
            analysis["best_eval_loss"] = loss
            analysis["best_epoch"] = i + 1
    
    # Check for overfitting (eval loss increasing while train loss decreasing)
    if len(metrics) >= 2:
        for i in range(1, len(metrics)):
            if metrics[i].eval_loss and metrics[i-1].eval_loss:
                if metrics[i].eval_loss > metrics[i-1].eval_loss and metrics[i].train_loss < metrics[i-1].train_loss:
                    analysis["overfitting_detected"] = True
                    break
    
    # Check for training instability (large loss spikes)
    losses = [m.train_loss for m in metrics]
    if len(losses) >= 2:
        max_change = max(abs(losses[i] - losses[i-1]) for i in range(1, len(losses)))
        if max_change > 0.5:  # Threshold for instability
            analysis["training_stable"] = False
    
    return analysis


# ============= SAMPLE DATA GENERATION =============

def create_sample_evaluation_data():
    """Create sample evaluation data for demonstration"""
    
    # Sample training metrics
    training_metrics = [
        TrainingMetrics(epoch=1, train_loss=1.824, eval_loss=1.652, learning_rate=2e-4, gpu_memory_gb=11.2),
        TrainingMetrics(epoch=2, train_loss=1.156, eval_loss=1.289, learning_rate=1.33e-4, gpu_memory_gb=11.4),
        TrainingMetrics(epoch=3, train_loss=0.782, eval_loss=1.124, learning_rate=6.67e-5, gpu_memory_gb=11.3),
    ]
    
    # Sample human evaluations (2 evaluators, 5 questions)
    human_evaluations = [
        # Evaluator 1
        HumanEvaluation("Q001", "E1", 4.5, 4.0, 5.0, 4.0, 4.5, "Clear IRAC format, accurate citations"),
        HumanEvaluation("Q002", "E1", 4.0, 4.5, 4.5, 3.5, 4.0, "Good explanation of prescription"),
        HumanEvaluation("Q003", "E1", 4.0, 4.0, 4.5, 4.0, 4.0, "Bim Saviya well explained"),
        HumanEvaluation("Q004", "E1", 4.5, 4.5, 4.0, 4.0, 4.5, "Correct partition law analysis"),
        HumanEvaluation("Q005", "E1", 3.5, 4.0, 4.0, 3.5, 3.5, "Could use more detail on remedies"),
        # Evaluator 2
        HumanEvaluation("Q001", "E2", 4.0, 4.5, 4.5, 4.0, 4.0, "Good but could cite more sections"),
        HumanEvaluation("Q002", "E2", 4.5, 4.0, 4.0, 4.0, 4.5, "Accurate prescription analysis"),
        HumanEvaluation("Q003", "E2", 3.5, 4.0, 4.5, 3.5, 4.0, "Needs more comparison detail"),
        HumanEvaluation("Q004", "E2", 4.5, 4.0, 4.5, 4.5, 4.5, "Excellent partition explanation"),
        HumanEvaluation("Q005", "E2", 4.0, 3.5, 4.0, 4.0, 4.0, "Adequate mortgage default analysis"),
    ]
    
    return training_metrics, human_evaluations


# ============= MAIN EVALUATION RUNNER =============

def run_inference_evaluation():
    """Run inference evaluation with sample or real data"""
    
    print("=" * 70)
    print("MODEL INFERENCE AND HUMAN EVALUATION FRAMEWORK")
    print("=" * 70)
    print(f"Evaluation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Load model (or use sample mode)
    print("Initializing model...")
    inference = LegalReasoningInference(
        model_path=CONFIG["model_path"],
        base_model=CONFIG["base_model"]
    )
    
    if not inference.model_loaded:
        print("Running in sample data mode (model not loaded)")
    print()
    
    # Sample test questions
    test_questions = [
        "What are the legal requirements for a valid sale deed in Sri Lanka?",
        "How many years of possession are required for prescriptive title?",
        "What is Bim Saviya and how does it differ from deeds registration?",
        "Can co-owners compel partition through courts?",
        "What happens if a mortgagor defaults on a mortgage?"
    ]
    
    # Generate responses
    print("=" * 70)
    print("MODEL INFERENCE RESULTS")
    print("=" * 70)
    
    responses = []
    for i, question in enumerate(test_questions, 1):
        print(f"\nQ{i}: {question}")
        print("-" * 50)
        response = inference.generate_response(question)
        responses.append({"question": question, "response": response})
        print(response[:500] + "..." if len(response) > 500 else response)
    
    # Get sample evaluation data
    training_metrics, human_evaluations = create_sample_evaluation_data()
    
    # Analyze training
    print()
    print("=" * 70)
    print("TRAINING METRICS ANALYSIS")
    print("=" * 70)
    
    training_analysis = analyze_training_metrics(training_metrics)
    print(f"Total Epochs: {training_analysis['total_epochs']}")
    print(f"Initial Loss: {training_analysis['initial_loss']:.4f}")
    print(f"Final Loss: {training_analysis['final_loss']:.4f}")
    print(f"Loss Reduction: {training_analysis['loss_reduction_pct']:.1f}%")
    print(f"Best Epoch: {training_analysis['best_epoch']}")
    print(f"Training Stable: {'Yes' if training_analysis['training_stable'] else 'No'}")
    print(f"Overfitting Detected: {'Yes' if training_analysis['overfitting_detected'] else 'No'}")
    
    # Analyze human evaluations
    print()
    print("=" * 70)
    print("HUMAN EVALUATION RESULTS")
    print("=" * 70)
    
    collector = HumanEvaluationCollector()
    for eval in human_evaluations:
        collector.add_evaluation(eval)
    
    aggregate = collector.get_aggregate_scores()
    
    print(f"{'Dimension':<25} {'Mean':>8} {'Std':>8} {'Min':>8} {'Max':>8}")
    print("-" * 60)
    for dim, stats in aggregate.items():
        dim_name = dim.replace("_", " ").title()
        print(f"{dim_name:<25} {stats['mean']:>8.2f} {stats['std']:>8.2f} {stats['min']:>8.2f} {stats['max']:>8.2f}")
    
    # Inter-rater reliability
    print()
    print("=" * 70)
    print("INTER-RATER RELIABILITY")
    print("=" * 70)
    
    for q_id in ["Q001", "Q002", "Q003", "Q004", "Q005"]:
        irr = collector.calculate_inter_rater_reliability(q_id)
        print(f"{q_id}: Agreement Rate = {irr.get('agreement_rate', 0)*100:.0f}%, Avg Diff = {irr.get('average_score_difference', 0):.2f}")
    
    # Save results
    report = {
        "evaluation_date": datetime.now().isoformat(),
        "model_loaded": inference.model_loaded,
        "responses": responses,
        "training_analysis": training_analysis,
        "human_evaluation_aggregate": aggregate,
        "training_metrics": [
            {"epoch": m.epoch, "train_loss": m.train_loss, "eval_loss": m.eval_loss}
            for m in training_metrics
        ]
    }
    
    with open("inference_evaluation_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print()
    print(f"Report saved to: inference_evaluation_report.json")
    
    return report


if __name__ == "__main__":
    run_inference_evaluation()
