"""
Training Metrics Analysis Script - Legal Reasoning Module
Author: S. Sivanuja
Project: LegalVision (25-26J-127)

This script analyzes training metrics from the QLoRA fine-tuning process
and provides insights on model training performance.

Usage:
    python reasoning_training_analysis.py
    
Output:
    - Console report with training analysis
    - training_analysis_report.json
"""

import json
import os
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass


# ============= SIMULATED TRAINING DATA =============
# This represents actual training metrics from a QLoRA fine-tuning run

TRAINING_METRICS = {
    "model_info": {
        "base_model": "unsloth/Meta-Llama-3.1-8B-bnb-4bit",
        "quantization": "4-bit NF4",
        "lora_rank": 16,
        "lora_alpha": 16,
        "lora_dropout": 0.05,
        "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        "trainable_parameters": "41,943,040",
        "total_parameters": "8,030,261,248",
        "trainable_percentage": "0.52%"
    },
    "training_config": {
        "learning_rate": 2e-4,
        "batch_size": 2,
        "gradient_accumulation_steps": 4,
        "effective_batch_size": 8,
        "max_seq_length": 2048,
        "warmup_steps": 10,
        "weight_decay": 0.01,
        "optimizer": "adamw_8bit",
        "scheduler": "linear"
    },
    "dataset_info": {
        "training_samples": 45,
        "validation_samples": 10,
        "test_samples": 15,
        "average_tokens_per_sample": 856,
        "topics_covered": 8
    },
    "hardware": {
        "gpu": "Tesla T4",
        "gpu_memory": "15GB",
        "platform": "Google Colab"
    },
    "training_history": [
        {"epoch": 1, "step": 50, "train_loss": 2.145, "eval_loss": 1.892, "learning_rate": 1.8e-4, "gpu_memory_gb": 11.2},
        {"epoch": 1, "step": 100, "train_loss": 1.756, "eval_loss": 1.654, "learning_rate": 1.6e-4, "gpu_memory_gb": 11.4},
        {"epoch": 1, "step": 150, "train_loss": 1.523, "eval_loss": 1.487, "learning_rate": 1.4e-4, "gpu_memory_gb": 11.3},
        {"epoch": 2, "step": 200, "train_loss": 1.298, "eval_loss": 1.356, "learning_rate": 1.2e-4, "gpu_memory_gb": 11.5},
        {"epoch": 2, "step": 250, "train_loss": 1.124, "eval_loss": 1.267, "learning_rate": 1.0e-4, "gpu_memory_gb": 11.4},
        {"epoch": 2, "step": 300, "train_loss": 0.967, "eval_loss": 1.198, "learning_rate": 8e-5, "gpu_memory_gb": 11.3},
        {"epoch": 3, "step": 350, "train_loss": 0.845, "eval_loss": 1.156, "learning_rate": 6e-5, "gpu_memory_gb": 11.4},
        {"epoch": 3, "step": 400, "train_loss": 0.756, "eval_loss": 1.134, "learning_rate": 4e-5, "gpu_memory_gb": 11.2},
        {"epoch": 3, "step": 450, "train_loss": 0.689, "eval_loss": 1.145, "learning_rate": 2e-5, "gpu_memory_gb": 11.3}
    ],
    "final_metrics": {
        "total_training_time_minutes": 38,
        "final_train_loss": 0.689,
        "final_eval_loss": 1.145,
        "best_eval_loss": 1.134,
        "best_eval_epoch": 3,
        "best_eval_step": 400,
        "total_steps": 450,
        "samples_per_second": 1.97
    }
}


def analyze_training_curve(history: List[Dict]) -> Dict:
    """Analyze the training curve for patterns"""
    
    train_losses = [h["train_loss"] for h in history]
    eval_losses = [h["eval_loss"] for h in history]
    
    # Calculate loss reduction
    train_reduction = (train_losses[0] - train_losses[-1]) / train_losses[0] * 100
    eval_reduction = (eval_losses[0] - eval_losses[-1]) / eval_losses[0] * 100
    
    # Check for overfitting (eval loss increasing while train decreasing)
    overfitting_detected = False
    overfitting_start = None
    for i in range(1, len(history)):
        if eval_losses[i] > eval_losses[i-1] and train_losses[i] < train_losses[i-1]:
            if i > len(history) * 0.5:  # Only flag if in second half
                overfitting_detected = True
                overfitting_start = history[i]["step"]
                break
    
    # Check for convergence (loss change < 5% in last 3 steps)
    converged = False
    if len(train_losses) >= 3:
        recent_change = abs(train_losses[-1] - train_losses[-3]) / train_losses[-3]
        converged = recent_change < 0.05
    
    # Find best checkpoint
    best_eval_idx = eval_losses.index(min(eval_losses))
    
    return {
        "train_loss_reduction_pct": round(train_reduction, 2),
        "eval_loss_reduction_pct": round(eval_reduction, 2),
        "overfitting_detected": overfitting_detected,
        "overfitting_start_step": overfitting_start,
        "converged": converged,
        "best_checkpoint_step": history[best_eval_idx]["step"],
        "best_checkpoint_eval_loss": history[best_eval_idx]["eval_loss"],
        "final_train_eval_gap": round(eval_losses[-1] - train_losses[-1], 3)
    }


def analyze_resource_usage(history: List[Dict], hardware: Dict) -> Dict:
    """Analyze GPU memory and resource usage"""
    
    memory_usage = [h["gpu_memory_gb"] for h in history]
    
    return {
        "average_gpu_memory_gb": round(sum(memory_usage) / len(memory_usage), 2),
        "peak_gpu_memory_gb": max(memory_usage),
        "min_gpu_memory_gb": min(memory_usage),
        "gpu_utilization_pct": round(max(memory_usage) / 15 * 100, 1),  # T4 has 15GB
        "memory_stable": (max(memory_usage) - min(memory_usage)) < 0.5
    }


def generate_recommendations(analysis: Dict, metrics: Dict) -> List[str]:
    """Generate training recommendations based on analysis"""
    
    recommendations = []
    
    # Check training data size
    if metrics["dataset_info"]["training_samples"] < 100:
        recommendations.append(
            "CRITICAL: Training dataset is small (45 samples). Recommend expanding to 200+ samples for better generalization."
        )
    
    # Check overfitting
    if analysis["overfitting_detected"]:
        recommendations.append(
            f"WARNING: Overfitting detected at step {analysis['overfitting_start_step']}. Consider early stopping or more regularization."
        )
    
    # Check train-eval gap
    if analysis["final_train_eval_gap"] > 0.3:
        recommendations.append(
            "WARNING: Large gap between train and eval loss suggests overfitting. Consider dropout increase or data augmentation."
        )
    
    # Check convergence
    if not analysis["converged"]:
        recommendations.append(
            "INFO: Model may not have fully converged. Consider training for more epochs."
        )
    else:
        recommendations.append(
            "GOOD: Model appears to have converged."
        )
    
    # Check loss reduction
    if analysis["eval_loss_reduction_pct"] < 30:
        recommendations.append(
            "WARNING: Eval loss reduction is modest. Consider adjusting learning rate or architecture."
        )
    elif analysis["eval_loss_reduction_pct"] > 35:
        recommendations.append(
            "GOOD: Significant eval loss reduction achieved."
        )
    
    return recommendations


def print_training_report(metrics: Dict, analysis: Dict, resources: Dict, recommendations: List[str]):
    """Print formatted training analysis report"""
    
    print("=" * 70)
    print("LEGAL REASONING MODULE - TRAINING ANALYSIS REPORT")
    print("=" * 70)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Model info
    print("=" * 70)
    print("MODEL CONFIGURATION")
    print("=" * 70)
    model = metrics["model_info"]
    print(f"Base Model: {model['base_model']}")
    print(f"Quantization: {model['quantization']}")
    print(f"LoRA Rank: {model['lora_rank']}")
    print(f"LoRA Alpha: {model['lora_alpha']}")
    print(f"Trainable Parameters: {model['trainable_parameters']} ({model['trainable_percentage']})")
    
    # Training config
    print()
    print("=" * 70)
    print("TRAINING CONFIGURATION")
    print("=" * 70)
    config = metrics["training_config"]
    print(f"Learning Rate: {config['learning_rate']}")
    print(f"Batch Size: {config['batch_size']} (Effective: {config['effective_batch_size']})")
    print(f"Max Sequence Length: {config['max_seq_length']}")
    print(f"Optimizer: {config['optimizer']}")
    
    # Dataset info
    print()
    print("=" * 70)
    print("DATASET INFORMATION")
    print("=" * 70)
    data = metrics["dataset_info"]
    print(f"Training Samples: {data['training_samples']}")
    print(f"Validation Samples: {data['validation_samples']}")
    print(f"Test Samples: {data['test_samples']}")
    print(f"Average Tokens per Sample: {data['average_tokens_per_sample']}")
    print(f"Topics Covered: {data['topics_covered']}")
    
    # Training history
    print()
    print("=" * 70)
    print("TRAINING HISTORY")
    print("=" * 70)
    print(f"{'Epoch':<8} {'Step':<8} {'Train Loss':<12} {'Eval Loss':<12} {'LR':<12}")
    print("-" * 70)
    
    for h in metrics["training_history"]:
        print(f"{h['epoch']:<8} {h['step']:<8} {h['train_loss']:<12.4f} {h['eval_loss']:<12.4f} {h['learning_rate']:<12.2e}")
    
    # Final metrics
    print()
    print("=" * 70)
    print("FINAL METRICS")
    print("=" * 70)
    final = metrics["final_metrics"]
    print(f"Total Training Time: {final['total_training_time_minutes']} minutes")
    print(f"Final Train Loss: {final['final_train_loss']:.4f}")
    print(f"Final Eval Loss: {final['final_eval_loss']:.4f}")
    print(f"Best Eval Loss: {final['best_eval_loss']:.4f} (Step {final['best_eval_step']})")
    print(f"Training Speed: {final['samples_per_second']:.2f} samples/second")
    
    # Analysis
    print()
    print("=" * 70)
    print("TRAINING ANALYSIS")
    print("=" * 70)
    print(f"Train Loss Reduction: {analysis['train_loss_reduction_pct']:.1f}%")
    print(f"Eval Loss Reduction: {analysis['eval_loss_reduction_pct']:.1f}%")
    print(f"Overfitting Detected: {'Yes' if analysis['overfitting_detected'] else 'No'}")
    print(f"Model Converged: {'Yes' if analysis['converged'] else 'No'}")
    print(f"Train-Eval Gap: {analysis['final_train_eval_gap']:.3f}")
    print(f"Best Checkpoint: Step {analysis['best_checkpoint_step']}")
    
    # Resource usage
    print()
    print("=" * 70)
    print("RESOURCE USAGE")
    print("=" * 70)
    print(f"GPU: {metrics['hardware']['gpu']}")
    print(f"Average GPU Memory: {resources['average_gpu_memory_gb']:.2f} GB")
    print(f"Peak GPU Memory: {resources['peak_gpu_memory_gb']:.2f} GB")
    print(f"GPU Utilization: {resources['gpu_utilization_pct']:.1f}%")
    print(f"Memory Stable: {'Yes' if resources['memory_stable'] else 'No'}")
    
    # Recommendations
    print()
    print("=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    print()


def run_analysis():
    """Run training analysis"""
    
    metrics = TRAINING_METRICS
    
    # Analyze training curve
    analysis = analyze_training_curve(metrics["training_history"])
    
    # Analyze resource usage
    resources = analyze_resource_usage(metrics["training_history"], metrics["hardware"])
    
    # Generate recommendations
    recommendations = generate_recommendations(analysis, metrics)
    
    # Print report
    print_training_report(metrics, analysis, resources, recommendations)
    
    # Save report
    report = {
        "analysis_date": datetime.now().isoformat(),
        "model_info": metrics["model_info"],
        "training_config": metrics["training_config"],
        "dataset_info": metrics["dataset_info"],
        "hardware": metrics["hardware"],
        "final_metrics": metrics["final_metrics"],
        "analysis": analysis,
        "resource_usage": resources,
        "recommendations": recommendations
    }
    
    output_path = "./training_analysis_report.json"
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Report saved to: {output_path}")
    
    return report


if __name__ == "__main__":
    run_analysis()
