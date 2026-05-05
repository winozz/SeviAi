#!/usr/bin/env python3
"""
Training script for Hybrid Chatbot
Trains both Naive Bayes (already exists) and Neural Network
"""

import os
import sys
from hybrid_chatbot import NeuralNetworkTrainer, HybridChatbot, TF_AVAILABLE

def main():
    """Train the hybrid model"""
    print("\n")
    print("+" + "-" * 58 + "+")
    print("|" + " " * 58 + "|")
    print("|" + "  CvSU HYBRID CHATBOT TRAINING".center(58) + "|")
    print("|" + "  Naive Bayes + Neural Network".center(58) + "|")
    print("|" + " " * 58 + "|")
    print("+" + "-" * 58 + "+")
    print()

    intents_json_path = "data/cavsu_intents.json"
    intents_db_path = "data/cavsu_intents.db"
    model_dir = "models"

    if not os.path.exists(intents_json_path) and not os.path.exists(intents_db_path):
        print(f"ERROR: No intent source found. Expected {intents_json_path} or {intents_db_path}")
        sys.exit(1)

    print(f"Intent JSON file: {intents_json_path}")
    print(f"Intent DB file:   {intents_db_path}")
    print(f"Models directory: {model_dir}")
    print()

    # Train Neural Network
    print("Step 1: Training Neural Network")
    print("-" * 60)
    if not TF_AVAILABLE:
        print("[WARNING] TensorFlow not available - skipping Neural Network training")
        model = tokenizer = label_encoder = None
    else:
        try:
            model, tokenizer, label_encoder = NeuralNetworkTrainer.train(
                intents_json_path,
                model_dir,
                intents_db_path=intents_db_path
            )
            print("[OK] Neural Network trained successfully!")
        except Exception as e:
            print(f"ERROR training neural network: {e}")
            sys.exit(1)

    # Test Hybrid Chatbot
    print("\n" + "=" * 60)
    print("Step 2: Testing Hybrid Chatbot")
    print("=" * 60)

    try:
        hybrid = HybridChatbot(model_dir, os.path.join(model_dir, "responses_map.json"))

        # Test queries
        test_queries = [
            "What are the admission requirements?",
            "Does CvSU have Computer Science?",
            "How much is tuition?",
            "Are there scholarships?",
            "Tell me about CvSU",
            "When is enrollment?",
            "What facilities does CvSU have?",
        ]

        print("\nTesting with sample queries:\n")
        print(f"{'Query':<40} {'Model':<15} {'Confidence':>10}")
        print("-" * 65)

        for query in test_queries:
            intent, response, confidence, model = hybrid.chat(query, user_id="test_user")
            print(
                f"{query[:40]:<40} {model:<15} {confidence:>9.1%}"
            )

        # Print statistics
        print("\n" + "=" * 60)
        print("Model Usage Statistics")
        print("=" * 60)

        stats = hybrid.get_usage_stats()
        print(f"\nTotal Predictions: {stats['total_predictions']}")
        print(f"  Naive Bayes:     {stats['naive_bayes_used']:3d} ({stats['naive_bayes_percentage']:5.1f}%)")
        print(f"  Neural Network:  {stats['neural_network_used']:3d} ({stats['neural_network_percentage']:5.1f}%)")
        print(f"  Fallback:        {stats['fallback_used']:3d} ({stats['fallback_percentage']:5.1f}%)")

        print("\n" + "=" * 60)
        print("[OK] Hybrid Chatbot Training Complete!")
        print("=" * 60)
        print("\nTo use the hybrid chatbot:")
        print("  1. Update app.py to use HybridChatbot")
        print("  2. Start API: python -m uvicorn app:app --host 0.0.0.0 --port 8000")
        print("  3. Chatbot will automatically use both models hierarchically")
        print()

    except Exception as e:
        print(f"ERROR testing hybrid chatbot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

