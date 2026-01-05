#!/usr/bin/env python3
"""
Evaluation Module for AML Name Origin Classifier
Calculates Top-K accuracy, Mean Reciprocal Rank (MRR), and F1 scores
"""

import json
from typing import List, Dict, Tuple
from collections import defaultdict
from name_classifier import classifier


def load_test_dataset(filepath: str = "test_dataset.json") -> List[Dict]:
    """Load test dataset from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_top_k_accuracy(predictions: List[Dict], k: int = 1) -> float:
    """
    Calculate Top-K accuracy.
    
    Args:
        predictions: List of prediction results with ground_truth and predicted_countries
        k: Number of top predictions to consider
    
    Returns:
        Accuracy as float between 0 and 1
    """
    correct = 0
    total = len(predictions)
    
    for pred in predictions:
        ground_truth = set(pred['ground_truth'])
        predicted = pred['predicted_countries'][:k]
        
        # Check if any ground truth country appears in top-K predictions
        if any(country in ground_truth for country in predicted):
            correct += 1
    
    return correct / total if total > 0 else 0.0


def calculate_mrr(predictions: List[Dict]) -> float:
    """
    Calculate Mean Reciprocal Rank (MRR).
    
    MRR measures how high the correct answer ranks on average.
    Formula: (1/N) × Σ(1/rank_i) where rank_i is position of first correct answer
    
    Args:
        predictions: List of prediction results
    
    Returns:
        MRR score between 0 and 1
    """
    reciprocal_ranks = []
    
    for pred in predictions:
        ground_truth = set(pred['ground_truth'])
        predicted = pred['predicted_countries']
        
        # Find rank of first correct prediction
        rank = None
        for i, country in enumerate(predicted, start=1):
            if country in ground_truth:
                rank = i
                break
        
        if rank:
            reciprocal_ranks.append(1.0 / rank)
        else:
            reciprocal_ranks.append(0.0)
    
    return sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0


def calculate_per_country_metrics(predictions: List[Dict]) -> Dict[str, Dict]:
    """
    Calculate precision, recall, and F1 score per country.
    
    Args:
        predictions: List of prediction results
    
    Returns:
        Dictionary with per-country metrics
    """
    # Count true positives, false positives, false negatives per country
    stats = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0})
    
    for pred in predictions:
        ground_truth = set(pred['ground_truth'])
        predicted = set(pred['predicted_countries'])
        
        for country in ground_truth:
            if country in predicted:
                stats[country]['tp'] += 1
            else:
                stats[country]['fn'] += 1
        
        for country in predicted:
            if country not in ground_truth:
                stats[country]['fp'] += 1
    
    # Calculate metrics per country
    metrics = {}
    for country, counts in stats.items():
        tp = counts['tp']
        fp = counts['fp']
        fn = counts['fn']
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        metrics[country] = {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'support': tp + fn  # Number of true instances
        }
    
    return metrics


def calculate_confidence_calibration(predictions: List[Dict], bins: int = 10) -> Dict:
    """
    Calculate Expected Calibration Error (ECE).
    
    Measures whether reported confidence matches actual accuracy.
    
    Args:
        predictions: List of prediction results with confidence scores
        bins: Number of confidence bins
    
    Returns:
        Dictionary with calibration metrics
    """
    bin_edges = [i / bins for i in range(bins + 1)]
    bin_accuracies = [[] for _ in range(bins)]
    bin_confidences = [[] for _ in range(bins)]
    
    for pred in predictions:
        confidence = pred['confidence']
        ground_truth = set(pred['ground_truth'])
        predicted_top = pred['predicted_countries'][0] if pred['predicted_countries'] else None
        
        # Determine which bin this prediction falls into
        bin_idx = min(int(confidence * bins), bins - 1)
        
        # Check if prediction is correct
        is_correct = 1.0 if predicted_top in ground_truth else 0.0
        
        bin_accuracies[bin_idx].append(is_correct)
        bin_confidences[bin_idx].append(confidence)
    
    # Calculate ECE
    ece = 0.0
    total_samples = len(predictions)
    
    calibration_data = []
    for i in range(bins):
        if bin_accuracies[i]:
            avg_accuracy = sum(bin_accuracies[i]) / len(bin_accuracies[i])
            avg_confidence = sum(bin_confidences[i]) / len(bin_confidences[i])
            bin_size = len(bin_accuracies[i])
            
            ece += (bin_size / total_samples) * abs(avg_confidence - avg_accuracy)
            
            calibration_data.append({
                'confidence_range': f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}",
                'avg_confidence': avg_confidence,
                'avg_accuracy': avg_accuracy,
                'count': bin_size
            })
    
    return {
        'ece': ece,
        'calibration_data': calibration_data
    }


def evaluate_classifier(test_dataset: List[Dict]) -> Dict:
    """
    Run full evaluation on the classifier.
    
    Args:
        test_dataset: List of test cases with ground truth
    
    Returns:
        Dictionary with all evaluation metrics
    """
    print("=" * 70)
    print("AML Name Origin Classifier - Evaluation")
    print("=" * 70)
    print(f"\nEvaluating on {len(test_dataset)} test cases...")
    
    # Run predictions
    predictions = []
    for i, test_case in enumerate(test_dataset):
        if (i + 1) % 20 == 0:
            print(f"  Progress: {i + 1}/{len(test_dataset)}")
        
        result = classifier.classify(test_case['first_name'], test_case['last_name'])
        
        predictions.append({
            'name': f"{test_case['first_name']} {test_case['last_name']}",
            'ground_truth': test_case['ground_truth'],
            'predicted_countries': [country for country, _ in result['results']],
            'confidence': result['confidence'],
            'category': test_case.get('category', 'unknown')
        })
    
    print(f"  Completed: {len(test_dataset)}/{len(test_dataset)}\n")
    
    # Calculate metrics
    top1_accuracy = calculate_top_k_accuracy(predictions, k=1)
    top3_accuracy = calculate_top_k_accuracy(predictions, k=3)
    mrr = calculate_mrr(predictions)
    per_country = calculate_per_country_metrics(predictions)
    calibration = calculate_confidence_calibration(predictions)
    
    # Calculate per-category accuracy
    categories = defaultdict(list)
    for pred in predictions:
        categories[pred['category']].append(pred)
    
    category_accuracy = {}
    for category, preds in categories.items():
        category_accuracy[category] = calculate_top_k_accuracy(preds, k=1)
    
    return {
        'total_tests': len(test_dataset),
        'top1_accuracy': top1_accuracy,
        'top3_accuracy': top3_accuracy,
        'mrr': mrr,
        'per_country_metrics': per_country,
        'calibration': calibration,
        'category_accuracy': category_accuracy,
        'predictions': predictions
    }


def print_evaluation_report(results: Dict):
    """Print a formatted evaluation report."""
    print("=" * 70)
    print("EVALUATION RESULTS")
    print("=" * 70)
    
    print(f"\n📊 Overall Metrics:")
    print(f"  Total Test Cases: {results['total_tests']}")
    print(f"  Top-1 Accuracy:   {results['top1_accuracy']:.2%} (Target: ≥85%)")
    print(f"  Top-3 Accuracy:   {results['top3_accuracy']:.2%} (Target: ≥92%)")
    print(f"  Mean Reciprocal Rank: {results['mrr']:.3f} (Target: ≥0.88)")
    
    # Status indicators
    top1_status = "✓" if results['top1_accuracy'] >= 0.85 else "✗"
    top3_status = "✓" if results['top3_accuracy'] >= 0.92 else "✗"
    mrr_status = "✓" if results['mrr'] >= 0.88 else "✗"
    
    print(f"\n  Status: Top-1 {top1_status} | Top-3 {top3_status} | MRR {mrr_status}")
    
    print(f"\n📈 Per-Category Accuracy (Top-1):")
    for category, accuracy in sorted(results['category_accuracy'].items()):
        print(f"  {category:25s}: {accuracy:.2%}")
    
    print(f"\n🎯 Per-Country Metrics (F1 Score):")
    sorted_countries = sorted(results['per_country_metrics'].items(), 
                             key=lambda x: x[1]['f1'], reverse=True)
    for country, metrics in sorted_countries:
        support = metrics['support']
        print(f"  {country:10s}: F1={metrics['f1']:.3f}  "
              f"Precision={metrics['precision']:.3f}  "
              f"Recall={metrics['recall']:.3f}  "
              f"(n={support})")
    
    print(f"\n📉 Confidence Calibration:")
    print(f"  Expected Calibration Error (ECE): {results['calibration']['ece']:.4f} (Target: ≤0.05)")
    ece_status = "✓" if results['calibration']['ece'] <= 0.05 else "✗"
    print(f"  Status: {ece_status}")
    
    print(f"\n  Calibration Details:")
    for bin_data in results['calibration']['calibration_data']:
        print(f"    Confidence {bin_data['confidence_range']}: "
              f"Avg Conf={bin_data['avg_confidence']:.3f}, "
              f"Avg Acc={bin_data['avg_accuracy']:.3f}, "
              f"Count={bin_data['count']}")
    
    print("\n" + "=" * 70)
    
    # Error analysis
    print("\n🔍 Error Analysis (First 10 misclassifications):")
    misclassifications = [p for p in results['predictions'] 
                         if not any(c in p['ground_truth'] for c in p['predicted_countries'][:1])]
    
    for i, pred in enumerate(misclassifications[:10]):
        print(f"  {i+1}. {pred['name']}")
        print(f"     Ground Truth: {pred['ground_truth']}")
        print(f"     Predicted: {pred['predicted_countries'][:3]}")
        print(f"     Confidence: {pred['confidence']:.2%}")
        print(f"     Category: {pred['category']}")
    
    if len(misclassifications) > 10:
        print(f"  ... and {len(misclassifications) - 10} more errors")
    
    print("\n" + "=" * 70)


def main():
    """Main evaluation function."""
    # Load test dataset
    test_dataset = load_test_dataset()
    
    # Run evaluation
    results = evaluate_classifier(test_dataset)
    
    # Print report
    print_evaluation_report(results)
    
    # Save results to file
    output_file = "evaluation_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        # Remove predictions from saved results (too verbose)
        save_results = {k: v for k, v in results.items() if k != 'predictions'}
        json.dump(save_results, f, indent=2)
    
    print(f"\n✓ Detailed results saved to: {output_file}")
    print("")


if __name__ == "__main__":
    main()

