"""
Train a custom SpaCy NER model for Sri Lankan property deeds.
Uses train.json and test.json from the annotated folder.

Features:
- Training with loss tracking
- Loss curve visualization (saved as image)
- Comprehensive evaluation metrics
- Evaluation report (saved as JSON and TXT)

Usage:
    python spacy_ner_trainer.py [annotated_folder] [model_output_dir]
    
Examples:
    python spacy_ner_trainer.py ../data/deeds/annotated ../model/deed_ner_model
    python spacy_ner_trainer.py  # Uses defaults
"""

import json
import random
from pathlib import Path
from datetime import datetime
import spacy
from spacy.training import Example
from spacy.util import minibatch, compounding
import warnings
import sys

warnings.filterwarnings('ignore')

# Try to import matplotlib for plotting
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
    
    def convert_to_serializable(obj):
        """Convert numpy types to Python native types for JSON serialization."""
        if isinstance(obj, dict):
            return {k: convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_serializable(v) for v in obj]
        elif hasattr(obj, 'item'):  # numpy types like float32
            return obj.item()
        else:
            return obj
        
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠ matplotlib not installed. Loss curve will not be plotted.")
    print("  Install with: pip install matplotlib")


class DeedNERTrainer:
    """
    Train a custom SpaCy NER model for Sri Lankan property deeds.
    """
    
    def __init__(self, model_name=None):
        self.model_name = model_name
        self.nlp = None
        self.ner = None
        self.training_losses = []
        self.training_history = []
        
    def load_data(self, json_file: str):
        print(f"Loading data from: {json_file}")
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        training_data = []
        for item in data:
            if isinstance(item, list) and len(item) == 2:
                text, annotations = item
                entities = [tuple(e) for e in annotations.get("entities", [])]
                training_data.append((text, {"entities": entities}))
            elif isinstance(item, dict) and 'text' in item:
                entities = [(e['start'], e['end'], e['label']) for e in item.get('entities', [])]
                training_data.append((item['text'], {"entities": entities}))
        
        print(f"✓ Loaded {len(training_data)} examples")
        return training_data
    
    def prepare_model(self, labels: set):
        print("\nPreparing SpaCy model...")
        
        if self.model_name:
            try:
                print(f"Loading base model: {self.model_name}")
                self.nlp = spacy.load(self.model_name)
                print("✓ Base model loaded")
            except:
                print(f"⚠ Could not load {self.model_name}, creating blank model")
                self.nlp = spacy.blank("en")
        else:
            print("Creating blank English model")
            self.nlp = spacy.blank("en")
        
        if "ner" not in self.nlp.pipe_names:
            print("Adding NER component")
            self.ner = self.nlp.add_pipe("ner", last=True)
        else:
            self.ner = self.nlp.get_pipe("ner")
        
        print(f"\nAdding {len(labels)} entity labels:")
        for label in sorted(labels):
            self.ner.add_label(label)
            print(f"  + {label}")
        
        return self.nlp
    
    def train(self, training_data: list, n_iter: int = 30, 
              dropout: float = 0.2, batch_size: int = 8):
        print("\n" + "="*80)
        print("TRAINING NER MODEL")
        print("="*80)
        
        self.training_losses = []
        self.training_history = []
        
        labels = set()
        for text, annotations in training_data:
            for start, end, label in annotations["entities"]:
                labels.add(label)
        
        self.prepare_model(labels)
        
        other_pipes = [pipe for pipe in self.nlp.pipe_names if pipe != "ner"]
        
        print(f"\nTraining for {n_iter} iterations...")
        print(f"Dropout: {dropout}, Batch size: {batch_size}")
        print("-"*80)
        
        with self.nlp.disable_pipes(*other_pipes):
            optimizer = self.nlp.begin_training()
            
            for iteration in range(n_iter):
                random.shuffle(training_data)
                losses = {}
                
                batches = minibatch(training_data, size=compounding(4.0, 32.0, 1.001))
                
                for batch in batches:
                    examples = []
                    for text, annotations in batch:
                        doc = self.nlp.make_doc(text)
                        example = Example.from_dict(doc, annotations)
                        examples.append(example)
                    
                    self.nlp.update(examples, drop=dropout, sgd=optimizer, losses=losses)
                
                current_loss = losses.get('ner', 0)
                self.training_losses.append(current_loss)
                self.training_history.append({'iteration': iteration + 1, 'loss': current_loss})
                
                if (iteration + 1) % 5 == 0 or iteration == 0:
                    print(f"Iteration {iteration + 1:3d}/{n_iter} - Loss: {current_loss:.4f}")
        
        print("\n✓ Training complete!")
        return self.nlp
    
    def plot_loss_curve(self, output_path: str):
        if not MATPLOTLIB_AVAILABLE:
            print("⚠ Cannot plot loss curve: matplotlib not installed")
            return None
        
        if not self.training_losses:
            print("⚠ No training losses to plot")
            return None
        
        plt.figure(figsize=(12, 6))
        
        iterations = list(range(1, len(self.training_losses) + 1))
        plt.plot(iterations, self.training_losses, 'b-', linewidth=2, label='Training Loss', marker='o', markersize=3)
        
        if len(self.training_losses) >= 5:
            window_size = 5
            moving_avg = []
            for i in range(len(self.training_losses)):
                start_idx = max(0, i - window_size + 1)
                moving_avg.append(sum(self.training_losses[start_idx:i+1]) / (i - start_idx + 1))
            plt.plot(iterations, moving_avg, 'r--', linewidth=2, alpha=0.7, label=f'Moving Average ({window_size})')
        
        plt.xlabel('Iteration', fontsize=12)
        plt.ylabel('Loss', fontsize=12)
        plt.title('NER Training Loss Curve', fontsize=14, fontweight='bold')
        plt.legend(loc='upper right', fontsize=10)
        plt.grid(True, alpha=0.3)
        
        min_loss = min(self.training_losses)
        max_loss = max(self.training_losses)
        min_iter = self.training_losses.index(min_loss) + 1
        
        plt.annotate(f'Min: {min_loss:.4f} (iter {min_iter})', 
                     xy=(min_iter, min_loss),
                     xytext=(min_iter + len(self.training_losses)*0.1, min_loss + (max_loss - min_loss)*0.15),
                     arrowprops=dict(arrowstyle='->', color='green', lw=1.5),
                     fontsize=10, color='green', fontweight='bold')
        
        stats_text = f'Final Loss: {self.training_losses[-1]:.4f}\nMin Loss: {min_loss:.4f}\nMax Loss: {max_loss:.4f}'
        plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes, fontsize=9,
                 verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Loss curve saved to: {output_path}")
        return output_path
    
    def evaluate(self, test_data: list):
        print("\n" + "="*80)
        print("EVALUATING MODEL")
        print("="*80)
        
        examples = []
        for text, annotations in test_data:
            doc = self.nlp.make_doc(text)
            example = Example.from_dict(doc, annotations)
            examples.append(example)
        
        scores = self.nlp.evaluate(examples)
        
        evaluation_results = {
            'timestamp': datetime.now().isoformat(),
            'test_size': len(test_data),
            'overall': {
                'precision': scores.get('ents_p', 0),
                'recall': scores.get('ents_r', 0),
                'f1_score': scores.get('ents_f', 0),
            },
            'per_entity': {},
            'confusion_analysis': {'true_positives': 0, 'false_positives': 0, 'false_negatives': 0},
            'training_info': {
                'iterations': len(self.training_losses),
                'final_loss': self.training_losses[-1] if self.training_losses else None,
                'min_loss': min(self.training_losses) if self.training_losses else None,
                'max_loss': max(self.training_losses) if self.training_losses else None,
                'loss_reduction': (self.training_losses[0] - self.training_losses[-1]) if len(self.training_losses) > 1 else 0,
            }
        }
        
        if 'ents_per_type' in scores:
            for label, metrics in scores['ents_per_type'].items():
                evaluation_results['per_entity'][label] = {
                    'precision': metrics.get('p', 0),
                    'recall': metrics.get('r', 0),
                    'f1_score': metrics.get('f', 0),
                }
        
        for text, annotations in test_data:
            doc = self.nlp(text)
            gold_entities = set((start, end, label) for start, end, label in annotations['entities'])
            pred_entities = set((ent.start_char, ent.end_char, ent.label_) for ent in doc.ents)
            
            evaluation_results['confusion_analysis']['true_positives'] += len(gold_entities & pred_entities)
            evaluation_results['confusion_analysis']['false_positives'] += len(pred_entities - gold_entities)
            evaluation_results['confusion_analysis']['false_negatives'] += len(gold_entities - pred_entities)
        
        tp = evaluation_results['confusion_analysis']['true_positives']
        fp = evaluation_results['confusion_analysis']['false_positives']
        fn = evaluation_results['confusion_analysis']['false_negatives']
        evaluation_results['confusion_analysis']['accuracy'] = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 0
        
        self._print_evaluation_results(evaluation_results)
        return evaluation_results
    
    def _print_evaluation_results(self, results: dict):
        print(f"\n{'='*60}")
        print("OVERALL SCORES")
        print(f"{'='*60}")
        print(f"  Precision: {results['overall']['precision']:.2%}")
        print(f"  Recall:    {results['overall']['recall']:.2%}")
        print(f"  F1-Score:  {results['overall']['f1_score']:.2%}")
        
        print(f"\n{'='*60}")
        print("CONFUSION ANALYSIS")
        print(f"{'='*60}")
        ca = results['confusion_analysis']
        print(f"  True Positives:  {ca['true_positives']}")
        print(f"  False Positives: {ca['false_positives']}")
        print(f"  False Negatives: {ca['false_negatives']}")
        print(f"  Accuracy:        {ca['accuracy']:.2%}")
        
        if results['per_entity']:
            print(f"\n{'='*60}")
            print("PER-ENTITY SCORES")
            print(f"{'='*60}")
            print(f"  {'Entity':<30} {'Prec':>8} {'Recall':>8} {'F1':>8}")
            print(f"  {'-'*56}")
            for label, metrics in sorted(results['per_entity'].items()):
                print(f"  {label:<30} {metrics['precision']:>8.2%} {metrics['recall']:>8.2%} {metrics['f1_score']:>8.2%}")
        
        print(f"\n{'='*60}")
        print("TRAINING INFO")
        print(f"{'='*60}")
        ti = results['training_info']
        print(f"  Total Iterations: {ti['iterations']}")
        if ti['final_loss'] is not None:
            print(f"  Final Loss:       {ti['final_loss']:.4f}")
            print(f"  Min Loss:         {ti['min_loss']:.4f}")
            print(f"  Max Loss:         {ti['max_loss']:.4f}")
            print(f"  Loss Reduction:   {ti['loss_reduction']:.4f}")
    
    def save_evaluation_report(self, evaluation_results: dict, output_dir: str):
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        json_file = output_path / "evaluation_report.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(convert_to_serializable(evaluation_results), f, indent=2, ensure_ascii=False)
        print(f"\n✓ JSON report saved to: {json_file}")
        
        txt_file = output_path / "evaluation_report.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("NER MODEL EVALUATION REPORT\n")
            f.write("="*70 + "\n\n")
            f.write(f"Generated: {evaluation_results['timestamp']}\n")
            f.write(f"Test Size: {evaluation_results['test_size']} deeds\n\n")
            
            f.write("-"*70 + "\n")
            f.write("OVERALL SCORES\n")
            f.write("-"*70 + "\n")
            f.write(f"Precision: {evaluation_results['overall']['precision']:.2%}\n")
            f.write(f"Recall:    {evaluation_results['overall']['recall']:.2%}\n")
            f.write(f"F1-Score:  {evaluation_results['overall']['f1_score']:.2%}\n\n")
            
            f.write("-"*70 + "\n")
            f.write("CONFUSION ANALYSIS\n")
            f.write("-"*70 + "\n")
            ca = evaluation_results['confusion_analysis']
            f.write(f"True Positives:  {ca['true_positives']}\n")
            f.write(f"False Positives: {ca['false_positives']}\n")
            f.write(f"False Negatives: {ca['false_negatives']}\n")
            f.write(f"Accuracy:        {ca['accuracy']:.2%}\n\n")
            
            f.write("-"*70 + "\n")
            f.write("PER-ENTITY SCORES\n")
            f.write("-"*70 + "\n")
            f.write(f"{'Entity':<30} {'Precision':>12} {'Recall':>12} {'F1':>12}\n")
            f.write("-"*70 + "\n")
            for label, metrics in sorted(evaluation_results['per_entity'].items()):
                f.write(f"{label:<30} {metrics['precision']:>12.2%} {metrics['recall']:>12.2%} {metrics['f1_score']:>12.2%}\n")
            f.write("\n")
            
            f.write("-"*70 + "\n")
            f.write("TRAINING INFO\n")
            f.write("-"*70 + "\n")
            ti = evaluation_results['training_info']
            f.write(f"Total Iterations: {ti['iterations']}\n")
            if ti['final_loss'] is not None:
                f.write(f"Final Loss:       {ti['final_loss']:.4f}\n")
                f.write(f"Min Loss:         {ti['min_loss']:.4f}\n")
                f.write(f"Max Loss:         {ti['max_loss']:.4f}\n")
                f.write(f"Loss Reduction:   {ti['loss_reduction']:.4f}\n")
            f.write("\n" + "="*70 + "\n")
        
        print(f"✓ TXT report saved to: {txt_file}")
        
        history_file = output_path / "training_history.json"
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(convert_to_serializable({'losses': self.training_losses, 'history': self.training_history}), f, indent=2)
        print(f"✓ Training history saved to: {history_file}")
        
        return json_file, txt_file
    
    def save_model(self, output_dir: str):
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        self.nlp.to_disk(output_path)
        print(f"\n✓ Model saved to: {output_path}")
    
    def test_model(self, test_texts: list):
        print("\n" + "="*80)
        print("TESTING MODEL ON SAMPLE TEXTS")
        print("="*80)
        
        for i, text in enumerate(test_texts, 1):
            print(f"\n--- Sample {i} ---")
            preview = text[:200].replace('\n', ' ')
            print(f"Text: {preview}...")
            
            doc = self.nlp(text)
            
            if doc.ents:
                print(f"\nExtracted {len(doc.ents)} entities:")
                for ent in doc.ents:
                    print(f"  {ent.label_:25s} | {ent.text[:50]}")
            else:
                print("No entities found")


def main():
    print("="*80)
    print("SPACY NER TRAINER FOR SRI LANKAN PROPERTY DEEDS")
    print("="*80)
    
    annotated_folder = sys.argv[1] if len(sys.argv) > 1 else "../data/deeds/annotated"
    model_output_dir = sys.argv[2] if len(sys.argv) > 2 else "../model/deed_ner_model"
    
    N_ITERATIONS = 50
    
    train_file = Path(annotated_folder) / "train.json"
    test_file = Path(annotated_folder) / "test.json"
    
    print(f"\nConfiguration:")
    print(f"  Train file:    {train_file}")
    print(f"  Test file:     {test_file}")
    print(f"  Model output:  {model_output_dir}")
    print(f"  Iterations:    {N_ITERATIONS}")
    
    trainer = DeedNERTrainer(model_name=None)
    
    try:
        train_data = trainer.load_data(str(train_file))
        test_data = trainer.load_data(str(test_file))
        
        print(f"\nData split:")
        print(f"  Training: {len(train_data)} deeds (100%)")
        print(f"  Testing:  {len(test_data)} deeds (20%)")
        
        nlp = trainer.train(train_data, n_iter=N_ITERATIONS)
        
        output_path = Path(model_output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        loss_curve_path = output_path / "loss_curve.png"
        trainer.plot_loss_curve(str(loss_curve_path))
        
        evaluation_results = None
        if test_data:
            evaluation_results = trainer.evaluate(test_data)
            trainer.save_evaluation_report(evaluation_results, model_output_dir)
        
        trainer.save_model(model_output_dir)
        
        sample_texts = []
        if train_data:
            sample_texts.append(train_data[0][0][:1000])
            if len(train_data) > 1:
                sample_texts.append(train_data[1][0][:1000])
        
        sample_texts.extend([
            "VENDOR JOHN SILVA of No. 25, Galle Road transfers Lot 5 in Plan No. 123 to VENDEE MARY PERERA for Rs. 5,000,000",
            "The property bearing Assessment No. 45/2 in Colombo District registered under folio M 234/56"
        ])
        
        trainer.test_model(sample_texts)
        
        print("\n" + "="*80)
        print("✓ TRAINING COMPLETE!")
        print("="*80)
        print(f"\nAll outputs saved to: {model_output_dir}/")
        print(f"  ├── config.cfg")
        print(f"  ├── meta.json")
        print(f"  ├── ner/")
        print(f"  ├── vocab/")
        print(f"  ├── loss_curve.png")
        print(f"  ├── evaluation_report.json")
        print(f"  ├── evaluation_report.txt")
        print(f"  └── training_history.json")
        
        print("\nTo use the model:")
        print("  import spacy")
        print(f"  nlp = spacy.load('{model_output_dir}')")
        print("  doc = nlp('your deed text here')")
        print("  for ent in doc.ents:")
        print("      print(ent.text, ent.label_)")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure to run the annotator first:")
        print(f"  python annotate_deeds_from_txt.py <unprocessed_folder> {annotated_folder}")
    except Exception as e:
        print(f"\n❌ Error during training: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
