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
import urllib.request
import urllib.error
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
    from sklearn.model_selection import train_test_split
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("[WARNING] TensorFlow not available - Neural Network features disabled")
    print("          Run with Python 3.11 or 3.12 for TensorFlow support")

# Download NLTK resources (idempotent — no-op if already present)
for resource, kind in [('punkt_tab', 'tokenizers'), ('wordnet', 'corpora')]:
    try:
        nltk.data.find(f'{kind}/{resource}')
    except (LookupError, OSError):
        nltk.download(resource, quiet=True)

lemmatizer = WordNetLemmatizer()
_NON_ALPHA_RE = r"[^a-z0-9\s]"

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
        text = re.sub(_NON_ALPHA_RE, "", text)
        tokens = nltk.word_tokenize(text)
        return " ".join([lemmatizer.lemmatize(t) for t in tokens])


class NeuralNetworkModel:
    """Accurate Neural Network model (requires TensorFlow)"""

    DEFAULT_CONFIDENCE_THRESHOLD = 0.50
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

        thresholds_path = os.path.join(model_dir, "nn_thresholds.json")
        if os.path.exists(thresholds_path):
            with open(thresholds_path, "r", encoding="utf-8") as f:
                self.adaptive_thresholds: dict = json.load(f)
            print(f"[OK] Loaded adaptive thresholds for {len(self.adaptive_thresholds)} intents")
        else:
            self.adaptive_thresholds = {}

    def get_threshold(self, intent: str) -> float:
        """Return the calibrated confidence threshold for a given intent."""
        return self.adaptive_thresholds.get(intent, self.DEFAULT_CONFIDENCE_THRESHOLD)

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
        text = re.sub(_NON_ALPHA_RE, "", text)
        tokens = nltk.word_tokenize(text)
        return " ".join([lemmatizer.lemmatize(t) for t in tokens])


class LocalLLM:
    """
    Thin wrapper around a locally-hosted LLM served via Ollama
    (http://localhost:11434).  Used as the final fallback when both
    NB and NN are below their confidence thresholds.

    To use a different local backend (llama.cpp server, LM Studio, etc.)
    just point OLLAMA_BASE_URL / OLLAMA_MODEL to the compatible endpoint.

    Falls back gracefully to None if the server is unreachable so the
    rest of the chatbot pipeline is unaffected.
    """

    # Override with env vars: OLLAMA_BASE_URL, OLLAMA_MODEL
    DEFAULT_BASE_URL = "http://localhost:11434"
    DEFAULT_MODEL = "llama3"
    TIMEOUT_SECONDS = 15

    def __init__(
        self,
        base_url: str = None,
        model: str = None,
        system_prompt: str = "",
    ):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", self.DEFAULT_BASE_URL)).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", self.DEFAULT_MODEL)
        self.system_prompt = system_prompt
        self.available = self._probe()

    def _probe(self) -> bool:
        """Return True if the Ollama server is reachable."""
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3):
                return True
        except Exception:
            return False

    def generate(self, user_message: str, conversation_context: list = None) -> Optional[str]:
        """
        Send a message to the local LLM and return its reply, or None on error.

        Args:
            user_message: The user's raw input.
            conversation_context: Optional list of prior {"role", "content"} dicts
                                  for multi-turn context (last N turns).
        """
        if not self.available:
            return None

        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        if conversation_context:
            messages.extend(conversation_context[-6:])  # last 3 turns
        messages.append({"role": "user", "content": user_message})

        payload = json.dumps({
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.4, "num_predict": 300},
        }).encode("utf-8")

        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/chat",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.TIMEOUT_SECONDS) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("message", {}).get("content", "").strip() or None
        except Exception:
            return None


class HybridChatbot:
    """
    Hierarchical Hybrid Chatbot
    Strategy: Use fast NB first, fallback to accurate NN if uncertain
    """

    NB_CONFIDENCE_THRESHOLD = 0.55  # If NB confidence > 55%, use it; otherwise defer to NN
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

        # Initialize local LLM for deep-fallback (fires only when NB+NN both fail)
        print("\n[4/5] Initialising local LLM fallback (Ollama)...")
        self.llm = LocalLLM(system_prompt=self._system_prompt_text())
        if self.llm.available:
            print(f"[OK] Local LLM ready  model={self.llm.model}  url={self.llm.base_url}")
        else:
            print("[WARNING] Local LLM not reachable — deep-fallback disabled")
            print("          Start Ollama and run: ollama pull llama3")

        self.model_usage_stats["llm_fallback_used"] = 0

        print("\n[5/5] Initialization complete")
        print("=" * 60)
        print(f"Strategy: NB threshold = {self.NB_CONFIDENCE_THRESHOLD:.0%}")
        print("         NN threshold = adaptive per-intent")
        print(f"         LLM fallback = {'enabled' if self.llm.available else 'disabled'}")
        print("=" * 60 + "\n")

    @staticmethod
    def _system_prompt_text() -> str:
        """Compact system prompt passed to the local LLM for deep-fallback answers."""
        return (
            "You are Sevi, the CvSU Virtual Assistant for Cavite State University. "
            "Answer questions about academic programs, admissions, fees, scholarships, "
            "campus services, and university policies concisely and accurately. "
            "If you are unsure, say so and direct the user to the relevant CvSU office. "
            "Never fabricate names, figures, deadlines, or official policies. "
            "Respond in the same language the user uses (English or Filipino/Taglish)."
        )

    def _nb_result(self, user_input: str, user_id: str) -> Tuple[Optional[str], float, dict]:
        """Run NB + optional NLU enhancement. Returns (intent, confidence, nlu_data) or (None, 0, {})."""
        if not self.nb_model:
            return None, 0.0, {}
        intent, confidence = self.nb_model.predict(user_input)
        nlu_data = {}
        if self.nlu_engine and user_id:
            result = self.nlu_engine.enhance_prediction(user_input, intent, confidence, user_id)
            intent = result["intent"]
            confidence = result["confidence"]
            nlu_data = result
            self.model_usage_stats["nlu_enhanced"] += 1
        return intent, confidence, nlu_data

    def _nn_result(self, user_input: str) -> Tuple[Optional[str], float]:
        """Run NN. Returns (intent, confidence) or (None, 0)."""
        if not self.nn_model:
            return None, 0.0
        return self.nn_model.predict(user_input)

    def _llm_context(self, user_id: Optional[str]) -> list:
        """Build the last-3-turns conversation context for the LLM."""
        if not user_id or user_id not in self.conversation_history:
            return []
        context = []
        for turn in self.conversation_history[user_id][-3:]:
            context.append({"role": "user", "content": turn["user_message"]})
            context.append({"role": "assistant", "content": turn["bot_response"]})
        return context

    def predict(self, user_input: str, user_id: str = None) -> Tuple[str, str, float, str, dict]:
        """
        Hierarchical prediction: NB → NN → Local LLM → static fallback.

        Returns:
            (intent, response, confidence, model_used, nlu_data)
        """
        # Step 1: Naive Bayes (+ optional NLU enhancement)
        nb_intent, nb_confidence, nlu_data = self._nb_result(user_input, user_id)
        if nb_intent and nb_confidence >= self.NB_CONFIDENCE_THRESHOLD:
            self.model_usage_stats["naive_bayes_used"] += 1
            return nb_intent, random.choice(self.responses_map[nb_intent]), nb_confidence, "Naive Bayes (NLU Enhanced)", nlu_data

        # Step 2: Neural Network with adaptive per-intent threshold
        nn_intent, nn_confidence = self._nn_result(user_input)
        if nn_intent and nn_confidence >= self.nn_model.get_threshold(nn_intent):
            response = random.choice(self.responses_map.get(nn_intent, self.responses_map[self.FALLBACK_INTENT]))
            self.model_usage_stats["neural_network_used"] += 1
            return nn_intent, response, nn_confidence, "Neural Network", nlu_data

        # Step 3: Local LLM — fires only when NB+NN are both below threshold
        if self.llm and self.llm.available:
            llm_reply = self.llm.generate(user_input, conversation_context=self._llm_context(user_id))
            if llm_reply:
                self.model_usage_stats["llm_fallback_used"] += 1
                return self.FALLBACK_INTENT, llm_reply, 0.0, "Local LLM", nlu_data

        # Step 4: Static fallback
        self.model_usage_stats["fallback_used"] += 1
        return self.FALLBACK_INTENT, random.choice(self.responses_map[self.FALLBACK_INTENT]), 0.0, "Fallback", nlu_data

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
                "session_id": session_id,
                "entities": nlu_data.get("entities", {}),
                "is_follow_up": nlu_data.get("is_follow_up", False),
            })

        return intent, response, confidence, model_used, nlu_data

    def get_usage_stats(self) -> dict:
        """Get model usage statistics"""
        total = sum(self.model_usage_stats.values())
        if total == 0:
            return self.model_usage_stats.copy()

        def pct(key: str) -> float:
            return self.model_usage_stats[key] / total * 100

        return {
            "total_predictions": total,
            "naive_bayes_used": self.model_usage_stats["naive_bayes_used"],
            "naive_bayes_percentage": pct("naive_bayes_used"),
            "neural_network_used": self.model_usage_stats["neural_network_used"],
            "neural_network_percentage": pct("neural_network_used"),
            "llm_fallback_used": self.model_usage_stats["llm_fallback_used"],
            "llm_fallback_percentage": pct("llm_fallback_used"),
            "fallback_used": self.model_usage_stats["fallback_used"],
            "fallback_percentage": pct("fallback_used"),
            "nlu_enhanced": self.model_usage_stats["nlu_enhanced"],
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

1. IDENTITY AND SCOPE
- You serve prospective students, current students, parents, faculty, and the general public.
- You cover academic programs, admissions, campus services, scholarships, fees, schedules, policies, and general information about CvSU's main campus in Indang and its satellite campuses (Imus, Rosario, Silang, Naic, Trece Martires, Tanza, General Trias, Carmona, Cavite City, Bacoor, and others).
- You do NOT process enrollment, payments, or official document requests. Always redirect high-stakes actions (enrollment, grade disputes, document authentication) to the proper office.

2. CORE PERSONALITY
- Professional yet approachable; warm and respectful of Filipino culture ("Iskolar para sa Bayan").
- Patient and empathetic - many users are first-generation applicants or parents unfamiliar with university processes. Avoid jargon without explanation.
- Proactive in offering next steps and pointing to verification.

3. RETRIEVAL AND VERIFICATION PROTOCOL
Before answering a factual question:
- Classify the query: (a) general/stable, (b) time-sensitive, (c) campus-specific, (d) personal/transactional.
- Time-sensitive items (deadlines, fees, schedules, CvSUAT dates) must be flagged for verification with the relevant office. Qualify with "as of [date], please verify with [office]."
- For any specific number, date, name, or requirement, cite the source or qualify clearly.
- Disambiguate campus before giving program-specific or fee-specific answers - CvSU Indang and CvSU Imus may have very different offerings.

4. CONFIDENCE TIERS - never blur these
- High confidence: from official, recently verified CvSU sources. State plainly.
- Medium confidence: from official sources but possibly outdated. State with date qualifier and recommend verification.
- Low confidence: from secondary sources, inference, or older data. State as such and direct the user to the relevant office.
- No information: admit the gap honestly. Never fabricate. Provide the contact path of who would know.

5. DISAMBIGUATION
When a query is ambiguous, ask one targeted clarifying question, e.g.:
- "CvSU has multiple campuses. Which one are you asking about?"
- "Are you asking as a freshman applicant, transferee, or graduate student?"
- "Which academic year - 2025-2026 or 2026-2027?"
Limit to one clarifying question per turn unless absolutely necessary.

6. RESPONSE STRUCTURE
- Direct answer first, supporting details second, caveats and verification reminders last.
- Include contact info for the specific office when relevant.
- Short answers for simple lookups; longer structured answers for process questions.
- Offer next steps: "Is there anything else I can help you with?"

7. LANGUAGE
- Primary: English (professional). Respond in the language the user uses; if they mix Tagalog and English (Taglish), respond in kind.
- Use formal Filipino academic terminology when discussing official terms (e.g., "Pagsusulit sa Pagpasok," "Rehistrar").

8. PRIVACY AND DATA HANDLING (RA 10173)
- Never request or store personal information (full name, student number, contact details) unless the platform explicitly supports secure data handling.
- Never speculate about specific students' grades, status, or records.
- Redirect all individual student inquiries to the registrar or guidance office.

9. ESCALATION PATHWAYS - surface the right office
- Admissions questions -> Office of Admissions, specific campus
- Enrollment issues -> Registrar, specific campus
- Financial concerns -> Cashier and Scholarship Office (note RA 10931 free higher education subsidy where applicable)
- Academic concerns -> department chair or college dean
- Student welfare -> Office of Student Affairs and Services (OSAS)
- Online system issues -> Management Information Systems (MIS) office
- Complaints/appeals -> Campus Administrator or University President's Office

10. REFUSAL AND REDIRECTION
Decline to:
- Predict admission outcomes for specific applicants.
- Compare CvSU unfavorably to other institutions in misleading ways.
- Give legal interpretations of university policies (refer to the official policy documents).
- Provide unofficial workarounds to academic requirements.
- Share contact details of individual faculty without official verification.

11. PROHIBITED
- Do NOT fabricate tuition figures, professor names, deadlines, course codes, or passing rates.
- Do NOT promise services beyond CvSU's scope.
- Do NOT provide personal opinions on university policies.
- Do NOT give a generic "CvSU" answer without first asking which campus when the campus matters.

12. META
You are a helpful starting point and information aggregator, not the final authority. For anything consequential - enrollment, scholarships, document requirements - empower the user to verify with the proper CvSU office, and provide the path to that verification."""


class NeuralNetworkTrainer:
    """Train neural network model for intent classification."""

    VOCAB_SIZE = 1000
    MAX_LEN = 20
    EMBEDDING_DIM = 64
    MAX_EPOCHS = 10000
    BATCH_SIZE = 8
    EARLY_STOPPING_PATIENCE = 150
    LR_REDUCE_PATIENCE = 50
    LR_REDUCE_FACTOR = 0.5
    LR_MIN = 1e-6

    @staticmethod
    def train(intents_path: str, output_dir: str = "models"):
        """Train neural network on intents with early stopping up to 10,000 epochs."""
        print("\n" + "=" * 60)
        print("  NEURAL NETWORK TRAINING  (max 10 000 epochs)")
        print("=" * 60)

        gpus = tf.config.list_physical_devices("GPU")
        print(f"\n[GPU] {'Using: ' + gpus[0].name if gpus else 'No GPU detected — training on CPU'}")

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

        print("\n[2/5] Tokenizing patterns...")
        tokenizer = Tokenizer(num_words=NeuralNetworkTrainer.VOCAB_SIZE, oov_token="<OOV>")
        tokenizer.fit_on_texts(patterns)
        sequences = tokenizer.texts_to_sequences(patterns)
        padded = pad_sequences(sequences, maxlen=NeuralNetworkTrainer.MAX_LEN, padding="post")
        print(f"[OK] Tokenized {len(padded)} sequences")

        print("\n[3/5] Encoding labels...")
        label_encoder = LabelEncoder()
        label_encoder.fit(labels)
        encoded_labels = label_encoder.transform(labels)
        num_classes = len(label_encoder.classes_)
        y = tf.keras.utils.to_categorical(encoded_labels, num_classes=num_classes)
        print(f"[OK] Encoded {num_classes} intent classes")

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

        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor="val_loss",
                patience=NeuralNetworkTrainer.EARLY_STOPPING_PATIENCE,
                restore_best_weights=True,
                verbose=1,
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor="val_loss",
                factor=NeuralNetworkTrainer.LR_REDUCE_FACTOR,
                patience=NeuralNetworkTrainer.LR_REDUCE_PATIENCE,
                min_lr=NeuralNetworkTrainer.LR_MIN,
                verbose=1,
            ),
        ]

        x_train, x_val, y_train, y_val = train_test_split(
            padded, y, test_size=0.2, random_state=42, stratify=encoded_labels
        )

        print(f"\n[5/5] Training model (max {NeuralNetworkTrainer.MAX_EPOCHS} epochs, "
              f"early stop patience={NeuralNetworkTrainer.EARLY_STOPPING_PATIENCE})...")
        history = model.fit(
            x_train, y_train,
            epochs=NeuralNetworkTrainer.MAX_EPOCHS,
            batch_size=NeuralNetworkTrainer.BATCH_SIZE,
            validation_data=(x_val, y_val),
            callbacks=callbacks,
            verbose=1,
        )

        actual_epochs = len(history.history["accuracy"])
        print(f"\n[OK] Stopped at epoch {actual_epochs}/{NeuralNetworkTrainer.MAX_EPOCHS}")

        print("\n[+] Computing per-class confidence calibration...")
        all_proba = model.predict(padded, verbose=0)
        per_class_scores: dict = {}
        for i, label_idx in enumerate(encoded_labels):
            label = label_encoder.classes_[label_idx]
            conf = float(all_proba[i, label_idx])
            per_class_scores.setdefault(label, []).append(conf)

        adaptive_thresholds = {
            label: round(min(max(float(np.percentile(scores, 80)), 0.35), 0.85), 4)
            for label, scores in per_class_scores.items()
        }

        print("\n" + "=" * 60)
        os.makedirs(output_dir, exist_ok=True)

        model.save(os.path.join(output_dir, "nn_model.h5"))
        with open(os.path.join(output_dir, "nn_tokenizer.pkl"), "wb") as f:
            pickle.dump(tokenizer, f)
        with open(os.path.join(output_dir, "nn_label_encoder.pkl"), "wb") as f:
            pickle.dump(label_encoder, f)
        with open(os.path.join(output_dir, "nn_thresholds.json"), "w", encoding="utf-8") as f:
            json.dump(adaptive_thresholds, f, indent=2, ensure_ascii=False)

        best_epoch = int(np.argmin(history.history["val_loss"]))
        best_val_acc = history.history["val_accuracy"][best_epoch]
        final_acc = history.history["accuracy"][best_epoch]

        print(f"[OK] Model saved to {output_dir}")
        print(f"  Training Accuracy:   {final_acc:.2%}  (epoch {best_epoch + 1})")
        print(f"  Validation Accuracy: {best_val_acc:.2%}  (best epoch)")
        print(f"  Epochs run:          {actual_epochs}")
        print(f"  Adaptive thresholds: {len(adaptive_thresholds)} intents calibrated")
        print("=" * 60 + "\n")

        return model, tokenizer, label_encoder, adaptive_thresholds

    @staticmethod
    def _preprocess(text: str) -> str:
        """Preprocess text."""
        text = text.lower()
        text = re.sub(_NON_ALPHA_RE, "", text)
        tokens = nltk.word_tokenize(text)
        return " ".join([lemmatizer.lemmatize(t) for t in tokens])

