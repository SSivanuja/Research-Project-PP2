"""
Train a custom SpaCy NER model for Sri Lankan property deeds.
Uses train.json and test.json from the annotated folder.

Usage:
    python spacy_ner_trainer.py [annotated_folder] [model_output_dir]
    
Examples:
    python spacy_ner_trainer.py ../data/deeds/annotated ../model/deed_ner_model
    python spacy_ner_trainer.py  # Uses defaults
"""

import json
import random
from pathlib import Path
import spacy
from spacy.training import Example
from spacy.util import minibatch, compounding
import warnings
import sys

warnings.filterwarnings('ignore')


class DeedNERTrainer:
    """
    Train a custom SpaCy NER model for Sri Lankan property deeds.
    """
    
    def __init__(self, model_name=None):
        """
        Initialize trainer.
        Args:
            model_name: Base model to start from (None for blank, or 'en_core_web_sm')
        """
        self.model_name = model_name
        self.nlp = None
        self.ner = None
        
    def load_data(self, json_file: str):
        """
        Load data from JSON file.
        Expected format: [(text, {"entities": [(start, end, label), ...]}), ...]
        """
        print(f"Loading data from: {json_file}")
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert to proper format if needed
        training_data = []
        for item in data:
            if isinstance(item, list) and len(item) == 2:
                text, annotations = item
                # Convert entity tuples from lists to tuples
                entities = [tuple(e) for e in annotations.get("entities", [])]
                training_data.append((text, {"entities": entities}))
            elif isinstance(item, dict) and 'text' in item:
                # Handle dict format
                entities = [(e['start'], e['end'], e['label']) for e in item.get('entities', [])]
                training_data.append((item['text'], {"entities": entities}))
        
        print(f"✓ Loaded {len(training_data)} examples")
        return training_data
    
    def prepare_model(self, labels: set):
        """
        Prepare SpaCy model for training.
        """
        print("\nPreparing SpaCy model...")
        
        # Load or create model
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
        
        # Get or create NER component
        if "ner" not in self.nlp.pipe_names:
            print("Adding NER component")
            self.ner = self.nlp.add_pipe("ner", last=True)
        else:
            self.ner = self.nlp.get_pipe("ner")
        
        # Add labels
        print(f"\nAdding {len(labels)} entity labels:")
        for label in sorted(labels):
            self.ner.add_label(label)
            print(f"  + {label}")
        
        return self.nlp
    
    def train(self, training_data: list, n_iter: int = 30, 
              dropout: float = 0.2, batch_size: int = 8):
        """
        Train the NER model.
        """
        print("\n" + "="*80)
        print("TRAINING NER MODEL")
        print("="*80)
        
        # Extract all labels
        labels = set()
        for text, annotations in training_data:
            for start, end, label in annotations["entities"]:
                labels.add(label)
        
        # Prepare model
        self.prepare_model(labels)
        
        # Get names of other pipes to disable during training
        other_pipes = [pipe for pipe in self.nlp.pipe_names if pipe != "ner"]
        
        # Training
        print(f"\nTraining for {n_iter} iterations...")
        print(f"Dropout: {dropout}, Batch size: {batch_size}")
        print("-"*80)
        
        with self.nlp.disable_pipes(*other_pipes):
            # Reset and initialize the weights
            optimizer = self.nlp.begin_training()
            
            for iteration in range(n_iter):
                # Shuffle training data
                random.shuffle(training_data)
                losses = {}
                
                # Batch up the examples
                batches = minibatch(training_data, size=compounding(4.0, 32.0, 1.001))
                
                for batch in batches:
                    examples = []
                    for text, annotations in batch:
                        doc = self.nlp.make_doc(text)
                        example = Example.from_dict(doc, annotations)
                        examples.append(example)
                    
                    # Update model
                    self.nlp.update(
                        examples,
                        drop=dropout,
                        sgd=optimizer,
                        losses=losses
                    )
                
                # Print progress
                if (iteration + 1) % 5 == 0 or iteration == 0:
                    print(f"Iteration {iteration + 1:3d}/{n_iter} - Loss: {losses.get('ner', 0):.4f}")
        
        print("\n✓ Training complete!")
        return self.nlp
    
    def evaluate(self, test_data: list):
        """
        Evaluate the trained model.
        """
        print("\n" + "="*80)
        print("EVALUATING MODEL")
        print("="*80)
        
        examples = []
        for text, annotations in test_data:
            doc = self.nlp.make_doc(text)
            example = Example.from_dict(doc, annotations)
            examples.append(example)
        
        scores = self.nlp.evaluate(examples)
        
        print(f"\nOverall Scores:")
        print(f"  Precision: {scores['ents_p']:.2%}")
        print(f"  Recall:    {scores['ents_r']:.2%}")
        print(f"  F1-Score:  {scores['ents_f']:.2%}")
        
        if 'ents_per_type' in scores:
            print("\nPer-entity scores:")
            for label, metrics in sorted(scores['ents_per_type'].items()):
                print(f"  {label}:")
                print(f"    Precision: {metrics['p']:.2%}, Recall: {metrics['r']:.2%}, F1: {metrics['f']:.2%}")
        
        return scores
    
    def save_model(self, output_dir: str):
        """Save the trained model."""
        output_path = Path(output_dir)
        if not output_path.exists():
            output_path.mkdir(parents=True)
        
        self.nlp.to_disk(output_path)
        print(f"\n✓ Model saved to: {output_path}")
    
    def test_model(self, test_texts: list):
        """
        Test the model on sample texts.
        """
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
    
    # Get parameters from command line or use defaults
    annotated_folder = sys.argv[1] if len(sys.argv) > 1 else "../data/deeds/annotated"
    model_output_dir = sys.argv[2] if len(sys.argv) > 2 else "../model/deed_ner_model"
    
    # Configuration
    N_ITERATIONS = 50
    
    # File paths
    train_file = Path(annotated_folder) / "train.json"
    test_file = Path(annotated_folder) / "test.json"
    
    print(f"\nConfiguration:")
    print(f"  Train file:    {train_file}")
    print(f"  Test file:     {test_file}")
    print(f"  Model output:  {model_output_dir}")
    print(f"  Iterations:    {N_ITERATIONS}")
    
    # Initialize trainer (None = blank model, or use "en_core_web_sm" for pretrained)
    trainer = DeedNERTrainer(model_name=None)
    
    try:
        # Load training data (100% of deeds)
        train_data = trainer.load_data(str(train_file))
        
        # Load test data (random 20% of deeds)
        test_data = trainer.load_data(str(test_file))
        
        print(f"\nData split:")
        print(f"  Training: {len(train_data)} deeds (100%)")
        print(f"  Testing:  {len(test_data)} deeds (20%)")
        
        # Train model
        nlp = trainer.train(train_data, n_iter=N_ITERATIONS)
        
        # Evaluate on test data
        if test_data:
            scores = trainer.evaluate(test_data)
        
        # Save model
        trainer.save_model(model_output_dir)
        
        # Test on sample texts
        sample_texts = []
        if train_data:
            sample_texts.append(train_data[0][0][:1000])  # First deed sample
        sample_texts.extend([
            "VENDOR JOHN SILVA of No. 25, Galle Road transfers Lot 5 in Plan No. 123 to VENDEE MARY PERERA for Rs. 5,000,000",
            "The property bearing Assessment No. 45/2 in Colombo District registered under folio M 234/56"
        ])
        
        trainer.test_model(sample_texts)
        
        print("\n" + "="*80)
        print("✓ TRAINING COMPLETE!")
        print("="*80)
        print(f"\nModel saved to: {model_output_dir}")
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