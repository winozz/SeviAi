"""
Hierarchical Hybrid Chatbot
Combines Naive Bayes (fast) + Neural Network (accurate)
Strategy: Use NB first, fallback to NN if confidence is low
"""

import json
import os
import random
import re
import pickle
import numpy as np
from typing import Tuple, Optional
import joblib

import nltk
from nltk.stem import WordNetLemmatizer

# Import advanced NLU engine
try:
    from .nlu_engine import AdvancedNLUEngine
    NLU_AVAILABLE = True
except ImportError:
    NLU_AVAILABLE = False

# TensorFlow imports (optional - graceful fallback if not available)
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, Dropout, Embedding, GlobalAveragePooling1D
    from tensorflow.keras.preprocessing.text import Tokenizer
    from tensorflow.keras.preprocessing.sequence import pad_sequences
    from sklearn.preprocessing import LabelEncoder
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("[WARNING] TensorFlow not available - Neural Network features disabled")
    print("          Run with Python 3.11 or 3.12 for TensorFlow support")

# Download NLTK resources
for resource in ['punkt_tab', 'wordnet']:
    try:
        nltk.data.find(f'tokenizers/{resource}')
    except LookupError:
        nltk.download(resource, quiet=True)

lemmatizer = WordNetLemmatizer()

class NaiveBayesModel:
    """Fast Naive Bayes model"""

    def __init__(self, model_path: str):
        self.pipeline = joblib.load(model_path)
        self.name = "Naive Bayes"

    def predict(self, text: str) -> Tuple[str, float]:
        """
        Predict intent and confidence

        Returns:
            (intent, confidence)
        """
        clean_text = self._preprocess(text)
        intent = self.pipeline.predict([clean_text])[0]
        proba = self.pipeline.predict_proba([clean_text])[0]
        confidence = float(np.max(proba))
        return intent, confidence

    @staticmethod
    def _preprocess(text: str) -> str:
        """Preprocess text"""
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", "", text)
        tokens = nltk.word_tokenize(text)
        return " ".join([lemmatizer.lemmatize(t) for t in tokens])


class NeuralNetworkModel:
    """Accurate Neural Network model (requires TensorFlow)"""

    CONFIDENCE_THRESHOLD = 0.5
    VOCAB_SIZE = 1000
    MAX_LEN = 20
    EMBEDDING_DIM = 64

    def __init__(self, model_dir: str):
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow required for Neural Network model")

        self.model = tf.keras.models.load_model(os.path.join(model_dir, "nn_model.h5"))
        with open(os.path.join(model_dir, "nn_tokenizer.pkl"), "rb") as f:
            self.tokenizer = pickle.load(f)
        with open(os.path.join(model_dir, "nn_label_encoder.pkl"), "rb") as f:
            self.label_encoder = pickle.load(f)
        self.name = "Neural Network"

    def predict(self, text: str) -> Tuple[str, float]:
        """
        Predict intent and confidence

        Returns:
            (intent, confidence)
        """
        clean_text = self._preprocess(text)
        seq = self.tokenizer.texts_to_sequences([clean_text])
        padded = pad_sequences(seq, maxlen=self.MAX_LEN, padding="post")

        proba = self.model.predict(padded, verbose=0)[0]
        confidence = float(np.max(proba))
        intent_idx = int(np.argmax(proba))
        intent = self.label_encoder.classes_[intent_idx]

        return intent, confidence

    @staticmethod
    def _preprocess(text: str) -> str:
        """Preprocess text"""
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", "", text)
        tokens = nltk.word_tokenize(text)
        return " ".join([lemmatizer.lemmatize(t) for t in tokens])


class HybridChatbot:
    """
    Hierarchical Hybrid Chatbot
    Strategy: Use fast NB first, fallback to accurate NN if uncertain
    """

    NB_CONFIDENCE_THRESHOLD = 0.55  # If NB confidence > 55%, use it
    NN_CONFIDENCE_THRESHOLD = 0.50  # NN minimum confidence threshold
    FALLBACK_INTENT = "nlu_fallback"

    def __init__(self, model_dir: str, responses_path: str):
        """
        Initialize hybrid chatbot with both models

        Args:
            model_dir: Directory containing trained models
            responses_path: Path to responses JSON
        """
        print("\n" + "=" * 60)
        print("  HIERARCHICAL HYBRID CHATBOT INITIALIZATION")
        print("=" * 60)

        # Load both models
        print("\n[1/4] Loading Naive Bayes (Fast)...")
        try:
            self.nb_model = NaiveBayesModel(
                os.path.join(model_dir, "CvSU_classifier.pkl")
            )
            print("[OK] Naive Bayes loaded")
        except Exception as e:
            print(f"[FAILED] Failed to load NB: {e}")
            self.nb_model = None

        print("\n[2/4] Loading Neural Network (Accurate)...")
        if not TF_AVAILABLE:
            print("[WARNING] TensorFlow not available - NN disabled")
            print("          Install Python 3.11/3.12 + TensorFlow to enable NN")
            self.nn_model = None
        else:
            try:
                self.nn_model = NeuralNetworkModel(model_dir)
                print("[OK] Neural Network loaded")
            except Exception as e:
                print(f"[WARNING] Could not load NN: {e}")
                print("          Run 'python train_hybrid.py' to train the NN model")
                self.nn_model = None

        # Load responses
        print("\n[3/4] Loading responses...")
        with open(responses_path, "r", encoding="utf-8") as f:
            self.responses_map = json.load(f)
        print(f"[OK] Loaded {len(self.responses_map)} intent responses")

        # Initialize conversation tracking
        self.conversation_history = {}
        self.model_usage_stats = {
            "naive_bayes_used": 0,
            "neural_network_used": 0,
            "fallback_used": 0,
            "nlu_enhanced": 0
        }

        # Initialize NLU engine for advanced understanding
        if NLU_AVAILABLE:
            self.nlu_engine = AdvancedNLUEngine()
            print("[OK] Advanced NLU Engine loaded")
        else:
            self.nlu_engine = None
            print("[WARNING] Advanced NLU Engine not available")

        print("\n[4/4] Initialization complete")
        print("=" * 60)
        print(f"Strategy: NB threshold = {self.NB_CONFIDENCE_THRESHOLD:.0%}")
        print(f"         NN threshold = {self.NN_CONFIDENCE_THRESHOLD:.0%}")
        print("=" * 60 + "\n")

    def predict(self, user_input: str, user_id: str = None) -> Tuple[str, str, float, str, dict]:
        """
        Hierarchical prediction with NLU enhancements: NB first, then NN if needed

        Returns:
            (intent, response, confidence, model_used, nlu_data)
        """
        nlu_data = {}

        # Step 1: Try fast Naive Bayes
        if self.nb_model:
            nb_intent, nb_confidence = self.nb_model.predict(user_input)

            # Apply NLU enhancements if available
            if self.nlu_engine and user_id:
                nlu_result = self.nlu_engine.enhance_prediction(
                    user_input, nb_intent, nb_confidence, user_id
                )
                nb_intent = nlu_result["intent"]
                nb_confidence = nlu_result["confidence"]
                nlu_data = nlu_result
                self.model_usage_stats["nlu_enhanced"] += 1

            # If confident enough, use NB result
            if nb_confidence >= self.NB_CONFIDENCE_THRESHOLD:
                response = random.choice(self.responses_map[nb_intent])
                self.model_usage_stats["naive_bayes_used"] += 1
                return nb_intent, response, nb_confidence, "Naive Bayes (NLU Enhanced)", nlu_data

        # Step 2: Fallback to Neural Network if available
        if self.nn_model:
            nn_intent, nn_confidence = self.nn_model.predict(user_input)

            # Check if NN confidence is acceptable
            if nn_confidence >= self.NN_CONFIDENCE_THRESHOLD:
                response = random.choice(self.responses_map.get(
                    nn_intent, self.responses_map[self.FALLBACK_INTENT]
                ))
                self.model_usage_stats["neural_network_used"] += 1
                return nn_intent, response, nn_confidence, "Neural Network", nlu_data

        # Step 3: Use fallback response
        response = random.choice(self.responses_map[self.FALLBACK_INTENT])
        self.model_usage_stats["fallback_used"] += 1
        return self.FALLBACK_INTENT, response, 0.0, "Fallback", nlu_data

    def chat(
        self,
        user_input: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Tuple[str, str, float, str, dict]:
        """
        Chat with conversation tracking and NLU enhancements

        Returns:
            (intent, response, confidence, model_used, nlu_data)
        """
        intent, response, confidence, model_used, nlu_data = self.predict(user_input, user_id)

        # Track conversation
        if user_id:
            if user_id not in self.conversation_history:
                self.conversation_history[user_id] = []

            self.conversation_history[user_id].append({
                "user_message": user_input,
                "bot_response": response,
                "intent": intent,
                "confidence": confidence,
                "model_used": model_used,
                "entities": nlu_data.get("entities", {}),
                "is_follow_up": nlu_data.get("is_follow_up", False)
            })

        return intent, response, confidence, model_used, nlu_data

    def get_usage_stats(self) -> dict:
        """Get model usage statistics"""
        total = sum(self.model_usage_stats.values())
        if total == 0:
            return self.model_usage_stats.copy()

        return {
            "total_predictions": total,
            "naive_bayes_used": self.model_usage_stats["naive_bayes_used"],
            "naive_bayes_percentage": (
                self.model_usage_stats["naive_bayes_used"] / total * 100
            ),
            "neural_network_used": self.model_usage_stats["neural_network_used"],
            "neural_network_percentage": (
                self.model_usage_stats["neural_network_used"] / total * 100
            ),
            "fallback_used": self.model_usage_stats["fallback_used"],
            "fallback_percentage": (
                self.model_usage_stats["fallback_used"] / total * 100
            )
        }

    def get_history(self) -> dict:
        """Get conversation history"""
        return self.conversation_history.copy()

    def clear_history(self, user_id: Optional[str] = None):
        """Clear conversation history"""
        if user_id and user_id in self.conversation_history:
            del self.conversation_history[user_id]
        elif not user_id:
            self.conversation_history.clear()

    def get_all_intents(self) -> list:
        """Get list of all available intents"""
        return list(self.responses_map.keys())

    def get_intent_details(self, intent_tag: str) -> Optional[dict]:
        """Get details about a specific intent"""
        if intent_tag not in self.responses_map:
            return None

        return {
            "tag": intent_tag,
            "response_count": len(self.responses_map[intent_tag]),
            "sample_responses": self.responses_map[intent_tag][:3]
        }

    @property
    def model_name(self) -> str:
        """Model name"""
        return "Hybrid Chatbot (NB + NN + NLU)"

    @property
    def accuracy(self) -> float:
        """Model accuracy (from training)"""
        return 0.9559

    @property
    def total_intents(self) -> int:
        """Total number of intents"""
        return len(self.responses_map)

    @property
    def total_patterns(self) -> int:
        """Approximate total patterns"""
        return sum(len(responses) for responses in self.responses_map.values())

    @property
    def model_size_kb(self) -> float:
        """Approximate model size in KB"""
        return 79.5

    @property
    def system_instructions(self) -> str:
        """System instructions for the chatbot"""
        return """You are Sevi, the CvSU Virtual Assistant - a helpful, friendly guide for Cavite State University.

CORE PERSONALITY:
- Professional yet approachable
- Patient and empathetic
- Always respectful of Filipino culture
- Proactive in offering additional help

BEHAVIOR GUIDELINES:
1. Intent Recognition: Use the classified intent to provide relevant information
2. Fallback Handling: When confidence is low, politely ask for clarification
3. Tone: Warm, encouraging, supportive of student goals
4. Context Awareness: Remember user's intent to provide follow-up suggestions"""


class NeuralNetworkTrainer:
    """Train neural network model for intent classification"""

    VOCAB_SIZE = 1000
    MAX_LEN = 20
    EMBEDDING_DIM = 64
    EPOCHS = 100
    BATCH_SIZE = 8

    @staticmethod
    def train(intents_path: str, output_dir: str = "models"):
        """Train neural network on intents"""
        print("\n" + "=" * 60)
        print("  NEURAL NETWORK TRAINING")
        print("=" * 60)

        # Load intents
        print("\n[1/5] Loading intents...")
        with open(intents_path, "r", encoding="utf-8") as f:
            intents_data = json.load(f)

        patterns = []
        labels = []
        for intent in intents_data["intents"]:
            tag = intent["tag"]
            for pattern in intent["patterns"]:
                patterns.append(NeuralNetworkTrainer._preprocess(pattern))
                labels.append(tag)

        print(f"[OK] Loaded {len(patterns)} patterns from {len(intents_data['intents'])} intents")

        # Tokenization
        print("\n[2/5] Tokenizing patterns...")
        tokenizer = Tokenizer(num_words=NeuralNetworkTrainer.VOCAB_SIZE, oov_token="<OOV>")
        tokenizer.fit_on_texts(patterns)
        sequences = tokenizer.texts_to_sequences(patterns)
        padded = pad_sequences(sequences, maxlen=NeuralNetworkTrainer.MAX_LEN, padding="post")
        print(f"[OK] Tokenized {len(padded)} sequences")

        # Label encoding
        print("\n[3/5] Encoding labels...")
        label_encoder = LabelEncoder()
        label_encoder.fit(labels)
        encoded_labels = label_encoder.transform(labels)
        num_classes = len(label_encoder.classes_)
        y = tf.keras.utils.to_categorical(encoded_labels, num_classes=num_classes)
        print(f"[OK] Encoded {num_classes} intent classes")

        # Build model
        print("\n[4/5] Building neural network...")
        model = Sequential([
            Embedding(
                input_dim=NeuralNetworkTrainer.VOCAB_SIZE,
                output_dim=NeuralNetworkTrainer.EMBEDDING_DIM,
                input_length=NeuralNetworkTrainer.MAX_LEN,
                name="embedding"
            ),
            GlobalAveragePooling1D(name="pooling"),
            Dense(128, activation="relu", name="dense_1"),
            Dropout(0.4, name="dropout_1"),
            Dense(64, activation="relu", name="dense_2"),
            Dropout(0.3, name="dropout_2"),
            Dense(num_classes, activation="softmax", name="output")
        ], name="IntentClassifier")

        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss="categorical_crossentropy",
            metrics=["accuracy"]
        )

        print(model.summary())

        # Train
        print("\n[5/5] Training model...")
        history = model.fit(
            padded, y,
            epochs=NeuralNetworkTrainer.EPOCHS,
            batch_size=NeuralNetworkTrainer.BATCH_SIZE,
            validation_split=0.2,
            verbose=1
        )

        # Save
        print("\n" + "=" * 60)
        os.makedirs(output_dir, exist_ok=True)

        model.save(os.path.join(output_dir, "nn_model.h5"))
        with open(os.path.join(output_dir, "nn_tokenizer.pkl"), "wb") as f:
            pickle.dump(tokenizer, f)
        with open(os.path.join(output_dir, "nn_label_encoder.pkl"), "wb") as f:
            pickle.dump(label_encoder, f)

        # Stats
        final_acc = history.history["accuracy"][-1]
        final_val_acc = history.history["val_accuracy"][-1]

        print(f"[OK] Model saved to {output_dir}")
        print(f"  Training Accuracy: {final_acc:.2%}")
        print(f"  Validation Accuracy: {final_val_acc:.2%}")
        print("=" * 60 + "\n")

        return model, tokenizer, label_encoder

    @staticmethod
    def _preprocess(text: str) -> str:
        """Preprocess text"""
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", "", text)
        tokens = nltk.word_tokenize(text)
        return " ".join([lemmatizer.lemmatize(t) for t in tokens])

