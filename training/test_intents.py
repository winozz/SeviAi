"""
Simple Intent Testing Script
Tests each intent with multiple queries and identifies weak areas
"""

import json
import random
import time
from collections import defaultdict

import requests

# Diverse queries for each intent
INTENT_QUERIES = {
    "greeting": [
        "Hi", "Hello", "Hey", "Good morning", "What's up", "Howdy",
        "Hey there", "Welcome", "Hello there", "Hi there",
    ],
    "goodbye": [
        "Bye", "Goodbye", "See you later", "Take care", "Farewell",
        "Exit", "Bye bye", "See you", "Until later", "Done",
    ],
    "thanks": [
        "Thanks", "Thank you", "Thanks a lot", "Appreciate it",
        "Salamat", "Thank you so much", "Thanks for helping",
    ],
    "admissions_requirements": [
        "What are admission requirements?", "How do I apply?",
        "What documents needed?", "CvSU admission process",
        "Requirements to enroll", "What do I need for CvSU?",
        "Admission checklist", "How to get admitted?",
    ],
    "admissions_exam": [
        "When is entrance exam?", "CVSUCAT schedule",
        "How to register for exam?", "When is CVSUCAT?",
        "Admission test timing", "College entrance exam",
    ],
    "enrollment_procedure": [
        "How to enroll?", "Enrollment process", "Steps to enroll",
        "How do I register?", "Enrollment procedure",
        "How to register for classes?", "What's enrollment?",
    ],
    "enrollment_schedule": [
        "When is enrollment?", "Enrollment dates", "When to enroll?",
        "Enrollment period", "When does enrollment start?",
    ],
    "courses_offered": [
        "What courses available?", "What programs?", "List of courses",
        "Available degrees", "What can I study?", "Program offerings",
    ],
    "it_cs_courses": [
        "Does CvSU have Computer Science?", "IT courses?",
        "Is there BSIT?", "Technology programs",
        "BSCS program", "Computer engineering?",
    ],
    "graduate_programs": [
        "Graduate programs?", "Masters degree?", "PhD programs?",
        "Post graduate courses?", "Masters at CvSU?",
    ],
    "tuition_fees": [
        "How much is tuition?", "School fees?", "Cost of enrollment?",
        "Tuition price?", "Is CvSU free?", "Fee breakdown?",
    ],
    "scholarship": [
        "Are there scholarships?", "Scholarship programs?",
        "Financial aid?", "CHED scholarship?", "DOST scholarship?",
    ],
    "campus_location": [
        "Where is CvSU?", "CvSU address?", "How to get there?",
        "Main campus location?", "CvSU Indang?", "Campus directions?",
    ],
    "campus_facilities": [
        "What facilities?", "Library location?", "Gym?",
        "Dormitory?", "Canteen?", "Student facilities?",
    ],
    "library": [
        "Library hours?", "CvSU library?", "Online library?",
        "Library services?", "E-library?", "How to access library?",
    ],
    "events": [
        "Upcoming events?", "CvSU events?", "School activities?",
        "Sportsfest?", "Cultural events?", "What's happening?",
    ],
    "academic_calendar": [
        "Academic calendar?", "When does school start?",
        "Semester schedule?", "Holiday schedule?", "School year dates?",
    ],
    "contact_info": [
        "How to contact CvSU?", "Phone number?", "Email?",
        "CvSU hotline?", "Contact details?", "How to reach?",
    ],
    "registrar": [
        "Registrar office?", "How to get TOR?", "Transcript?",
        "Diploma request?", "Graduation requirements?",
    ],
    "about_CvSU": [
        "What is CvSU?", "Tell me about CvSU", "History?",
        "CvSU overview?", "About Cavite State University?",
    ],
    "vision_mission": [
        "CvSU vision?", "CvSU mission?", "Core values?",
        "What does CvSU stand for?", "Goals?",
    ],
    "student_organizations": [
        "Student organizations?", "Clubs?", "How to join?",
        "Student council?", "Extracurricular?",
    ],
}

def test_intents(port=8001, queries_per_intent=5):
    """Test all intents with multiple queries"""
    base_url = f"http://127.0.0.1:{port}"

    print("\n" + "=" * 80)
    print("  INTENT TESTING - QUICK EVALUATION")
    print("=" * 80)
    print(f"\nTesting {len(INTENT_QUERIES)} intents, {queries_per_intent} queries each")
    print(f"Total requests: {len(INTENT_QUERIES) * queries_per_intent}")
    print("\nSending requests...")

    intent_results = defaultdict(lambda: {
        "total": 0,
        "correct": 0,
        "confidence_scores": [],
        "responses": []
    })

    start_time = time.time()
    request_count = 0

    for intent, query_templates in INTENT_QUERIES.items():
        for _ in range(queries_per_intent):
            query = random.choice(query_templates)

            try:
                response = requests.post(
                    f"{base_url}/chat",
                    json={"message": query, "user_id": f"test_user_{request_count}"},
                    timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    actual_intent = data.get("intent")
                    confidence = data.get("confidence", 0)

                    intent_results[intent]["total"] += 1
                    intent_results[intent]["confidence_scores"].append(confidence)
                    intent_results[intent]["responses"].append({
                        "query": query,
                        "actual_intent": actual_intent,
                        "confidence": confidence,
                        "correct": actual_intent == intent
                    })

                    if actual_intent == intent:
                        intent_results[intent]["correct"] += 1

                request_count += 1

            except Exception as e:
                print(f"  Error: {e}")

        # Progress indicator
        progress = (request_count / (len(INTENT_QUERIES) * queries_per_intent)) * 100
        print(f"  [{progress:.0f}%] Tested {intent}...", end="\r")

    elapsed = time.time() - start_time

    # Calculate overall stats
    total_requests = sum(r["total"] for r in intent_results.values())
    total_correct = sum(r["correct"] for r in intent_results.values())
    overall_accuracy = (total_correct / total_requests * 100) if total_requests > 0 else 0

    # Print results
    print("\n" + "=" * 80)
    print("  TEST RESULTS")
    print("=" * 80)

    print(f"\n[STATS] Overall:")
    print(f"   Accuracy: {overall_accuracy:.2f}% ({total_correct}/{total_requests})")
    print(f"   Time: {elapsed:.1f}s")

    print(f"\n{'Intent':<30} {'Accuracy':>12} {'Avg Conf':>12}")
    print("-" * 60)

    weak_intents = []

    for intent in sorted(intent_results.keys()):
        data = intent_results[intent]
        accuracy = (data["correct"] / data["total"] * 100) if data["total"] > 0 else 0
        avg_confidence = (sum(data["confidence_scores"]) / len(data["confidence_scores"])) if data["confidence_scores"] else 0

        status = "[OK]" if accuracy >= 80 else "[WARN]" if accuracy >= 60 else "[FAIL]"
        print(f"{intent:<30} {accuracy:>10.0f}% {status}  {avg_confidence:>10.1%}")

        if accuracy < 80:
            weak_intents.append((intent, accuracy, avg_confidence))

    # Recommendations
    print(f"\n[INFO] Analysis:")
    if weak_intents:
        print(f"\n   Weak Intents ({len(weak_intents)}):")
        for intent, acc, conf in sorted(weak_intents, key=lambda x: x[1]):
            print(f"   - {intent}: {acc:.0f}% accuracy, {conf:.1%} avg confidence")

        print(f"\n   Recommendations:")
        print(f"   1. Run: python expand_intents.py")
        print(f"   2. Add more diverse patterns for weak intents")
        print(f"   3. Retrain: python train_naive_bayes.py")
    else:
        print(f"   [OK] All intents performing well!")

    # Save detailed results
    results_file = "intent_test_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "overall_accuracy": overall_accuracy,
            "total_requests": total_requests,
            "elapsed_seconds": elapsed,
            "per_intent": {
                intent: {
                    "accuracy": data["correct"] / data["total"] * 100 if data["total"] > 0 else 0,
                    "avg_confidence": sum(data["confidence_scores"]) / len(data["confidence_scores"]) if data["confidence_scores"] else 0,
                    "sample_responses": data["responses"][:2]
                }
                for intent, data in intent_results.items()
            }
        }, f, indent=2)

    print(f"\n[SAVED] Detailed results saved to {results_file}")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    import sys

    port = sys.argv[1] if len(sys.argv) > 1 else "8001"
    queries_per_intent = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    test_intents(port=port, queries_per_intent=queries_per_intent)

