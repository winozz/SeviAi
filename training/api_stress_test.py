"""
API Stress Test & Intent Training
Sends diverse queries to train the model and identify weak intents
"""

import asyncio
import json
import random
import time
from collections import defaultdict
from datetime import datetime

import aiohttp
import requests

# Comprehensive query bank for all 23 intents
INTENT_QUERIES = {
    "greeting": [
        "Hi", "Hello", "Hey there", "Good morning", "Good afternoon",
        "What's up", "Howdy", "Hiya", "Welcome", "Greetings",
        "Hi there", "Hello there", "Hey", "Good day", "Kumusta",
    ],
    "goodbye": [
        "Bye", "Goodbye", "See you later", "Take care", "Farewell",
        "See you", "Bye bye", "Until next time", "Goodbye everyone", "Exit",
    ],
    "thanks": [
        "Thanks", "Thank you", "Thanks a lot", "Thank you so much", "Appreciate it",
        "Thanks for helping", "That's helpful", "Salamat", "Maraming salamat",
    ],
    "admissions_requirements": [
        "What are the admission requirements?", "What do I need to apply?",
        "How do I apply to CvSU?", "What documents are needed?",
        "Requirements for admission", "Admission process CvSU",
        "What's required to enroll?", "Documents for admission",
        "CvSU admission requirements", "How to get admitted?",
    ],
    "admissions_exam": [
        "When is the entrance exam?", "CVSUCAT schedule", "Admission test timing",
        "How to register for entrance exam?", "When is CVSUCAT?",
        "College entrance exam CvSU", "When can I take the exam?",
    ],
    "enrollment_procedure": [
        "How to enroll?", "Enrollment process", "Steps to enroll",
        "How do I register?", "Enrollment procedure CvSU",
        "What's the enrollment process?", "How to register for classes?",
    ],
    "enrollment_schedule": [
        "When is enrollment?", "Enrollment dates", "When does enrollment start?",
        "Enrollment schedule", "When to enroll?", "First semester enrollment",
    ],
    "courses_offered": [
        "What courses are offered?", "What programs are available?",
        "Available degree programs", "List of courses", "What can I study?",
        "Program offerings", "What majors does CvSU offer?",
    ],
    "it_cs_courses": [
        "Does CvSU have Computer Science?", "IT courses at CvSU",
        "Is there BSIT at CvSU?", "Technology programs", "BSCS program",
        "Computer engineering CvSU", "Does CvSU teach programming?",
    ],
    "graduate_programs": [
        "Graduate programs available?", "Masters degree at CvSU",
        "PhD programs", "Post graduate courses", "Masters programs",
        "Graduate school options", "Doctorate degrees",
    ],
    "tuition_fees": [
        "How much is tuition?", "Tuition cost", "School fees",
        "How much does it cost?", "Is CvSU free?", "Enrollment cost",
        "Fee breakdown", "Tuition price per semester",
    ],
    "scholarship": [
        "Are there scholarships?", "Scholarship programs", "Financial aid",
        "CHED scholarship", "DOST scholarship", "How to apply for scholarship?",
        "Scholarship opportunities", "Free tuition?",
    ],
    "campus_location": [
        "Where is CvSU?", "CvSU address", "How to get to CvSU?",
        "Main campus location", "CvSU Indang address", "CvSU campuses",
        "Where is CvSU located?", "Campus directions",
    ],
    "campus_facilities": [
        "What facilities does CvSU have?", "Library at CvSU", "CvSU gym",
        "Dormitory facilities", "Campus facilities", "Student facilities",
        "What's available on campus?", "Canteen location",
    ],
    "library": [
        "Library hours", "CvSU library", "Online library resources",
        "Library services", "How to access library?", "E-library",
        "Library location", "What's in the library?",
    ],
    "events": [
        "Upcoming events?", "CvSU events", "School activities",
        "CvSU anniversary", "What events are happening?", "Sportsfest",
        "Cultural events", "Seminar dates",
    ],
    "academic_calendar": [
        "Academic calendar", "School calendar", "When does school start?",
        "First day of classes", "Semester schedule", "Holiday schedule",
        "School year dates", "Academic dates",
    ],
    "contact_info": [
        "How to contact CvSU?", "CvSU phone number", "Email address",
        "CvSU hotline", "How can I reach you?", "Contact information",
        "CvSU Facebook", "Admissions contact",
    ],
    "registrar": [
        "Registrar office", "How to get TOR?", "Transcript of records",
        "Diploma request", "Graduation requirements", "Honorable dismissal",
        "Transfer credentials", "Certificate request",
    ],
    "about_CvSU": [
        "What is CvSU?", "Tell me about CvSU", "History of CvSU",
        "About Cavite State University", "CvSU overview", "What kind of school?",
    ],
    "vision_mission": [
        "CvSU vision", "CvSU mission", "Mission statement",
        "Vision and mission", "Core values", "What does CvSU stand for?",
        "Goals of CvSU", "CvSU values",
    ],
    "student_organizations": [
        "Student organizations", "Clubs and organizations", "How to join a club?",
        "Student council", "Extra curricular", "Organizations list",
        "Student activities", "Club membership",
    ],
}

class APIStressTest:
    def __init__(self, base_url="http://127.0.0.1:8001", total_requests=500):
        self.base_url = base_url
        self.total_requests = total_requests
        self.results = defaultdict(list)
        self.intent_stats = defaultdict(lambda: {"count": 0, "confidence_sum": 0, "min_conf": 1.0, "max_conf": 0.0})
        self.start_time = None

    async def send_request(self, session, query, intent_label, request_id):
        """Send async request to API"""
        try:
            async with session.post(
                f"{self.base_url}/chat",
                json={"message": query, "user_id": f"stress_test_{request_id}"},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                data = await response.json()

                result = {
                    "query": query,
                    "expected_intent": intent_label,
                    "actual_intent": data.get("intent"),
                    "confidence": data.get("confidence", 0),
                    "correct": data.get("intent") == intent_label,
                    "response_time": response.headers.get("x-process-time", "N/A"),
                }

                # Update stats
                actual = data.get("intent")
                self.intent_stats[actual]["count"] += 1
                self.intent_stats[actual]["confidence_sum"] += data.get("confidence", 0)
                self.intent_stats[actual]["min_conf"] = min(
                    self.intent_stats[actual]["min_conf"],
                    data.get("confidence", 1.0)
                )
                self.intent_stats[actual]["max_conf"] = max(
                    self.intent_stats[actual]["max_conf"],
                    data.get("confidence", 0)
                )

                self.results[intent_label].append(result)
                return result

        except Exception as e:
            return {
                "query": query,
                "expected_intent": intent_label,
                "error": str(e),
                "correct": False,
            }

    async def run_async(self, batch_size=50, delay_between_batches=1.0):
        """Run stress test with async requests"""
        print("\n" + "=" * 80)
        print("  API STRESS TEST - INTENT TRAINING")
        print("=" * 80)
        print(f"\nTarget: {self.total_requests} requests across {len(INTENT_QUERIES)} intents")
        print(f"Batch Size: {batch_size}")
        print(f"Delay Between Batches: {delay_between_batches}s")
        print("\nGenerating queries...")

        # Generate query list
        queries = []
        request_id = 0
        requests_per_intent = self.total_requests // len(INTENT_QUERIES)

        for intent, query_templates in INTENT_QUERIES.items():
            for _ in range(requests_per_intent):
                query = random.choice(query_templates)
                queries.append((query, intent, request_id))
                request_id += 1

        # Shuffle to randomize
        random.shuffle(queries)

        self.start_time = time.time()
        completed = 0

        async with aiohttp.ClientSession() as session:
            for batch_start in range(0, len(queries), batch_size):
                batch = queries[batch_start:batch_start + batch_size]

                print(f"\n[Batch {batch_start // batch_size + 1}] Sending {len(batch)} requests...", end="", flush=True)

                tasks = [
                    self.send_request(session, query, intent, req_id)
                    for query, intent, req_id in batch
                ]

                results = await asyncio.gather(*tasks)
                completed += len(results)

                # Count correct predictions
                correct = sum(1 for r in results if r.get("correct"))
                print(f" [{correct}/{len(batch)}] [OK] (Total: {completed}/{len(queries)})")

                # Delay before next batch
                if batch_start + batch_size < len(queries):
                    await asyncio.sleep(delay_between_batches)

        elapsed = time.time() - self.start_time
        return elapsed

    def print_results(self):
        """Print comprehensive test results"""
        print("\n" + "=" * 80)
        print("  STRESS TEST RESULTS")
        print("=" * 80)

        total_tests = sum(len(v) for v in self.results.values())
        total_correct = sum(
            sum(1 for r in v if r.get("correct"))
            for v in self.results.values()
        )

        accuracy = (total_correct / total_tests * 100) if total_tests > 0 else 0

        print(f"\n[STATS] Overall Performance:")
        print(f"   Total Requests: {total_tests}")
        print(f"   Correct: {total_correct}")
        print(f"   Incorrect: {total_tests - total_correct}")
        print(f"   Accuracy: {accuracy:.2f}%")
        print(f"   Time Elapsed: {self.start_time and time.time() - self.start_time or 0:.1f}s")

        print(f"\n📈 Per-Intent Results:")
        print(f"\n{'Intent':<30} {'Count':>6} {'Avg Conf':>10} {'Min Conf':>10} {'Max Conf':>10}")
        print("-" * 70)

        for intent in sorted(self.intent_stats.keys()):
            stats = self.intent_stats[intent]
            if stats["count"] > 0:
                avg_conf = stats["confidence_sum"] / stats["count"]
                print(f"{intent:<30} {stats['count']:>6} {avg_conf:>9.1%} {stats['min_conf']:>9.1%} {stats['max_conf']:>9.1%}")

        print(f"\n[WARN]️  Weak Intents (Avg Confidence < 60%):")
        weak_intents = [
            (intent, stats["confidence_sum"] / stats["count"])
            for intent, stats in self.intent_stats.items()
            if stats["count"] > 0 and stats["confidence_sum"] / stats["count"] < 0.60
        ]

        if weak_intents:
            for intent, avg_conf in sorted(weak_intents, key=lambda x: x[1]):
                print(f"   - {intent}: {avg_conf:.1%}")
        else:
            print("   [OK] All intents performing well!")

        print(f"\n[INFO] Recommendations:")
        recommendations = []

        # Accuracy threshold
        if accuracy < 90:
            recommendations.append(f"   - Expand training patterns (current accuracy: {accuracy:.1f}%)")

        # Low confidence intents
        if weak_intents:
            weak_intent_names = [i[0] for i in weak_intents]
            recommendations.append(f"   - Add more patterns for: {', '.join(weak_intent_names[:3])}")

        if recommendations:
            for rec in recommendations:
                print(rec)
        else:
            print("   [OK] Model is performing well! Consider deploying to production.")

        print("\n" + "=" * 80)

    def save_results(self, filename="stress_test_results.json"):
        """Save detailed results to file"""
        output = {
            "timestamp": datetime.now().isoformat(),
            "total_requests": sum(len(v) for v in self.results.values()),
            "accuracy": sum(
                sum(1 for r in v if r.get("correct"))
                for v in self.results.values()
            ) / max(1, sum(len(v) for v in self.results.values())),
            "intent_stats": {
                intent: {
                    "count": stats["count"],
                    "avg_confidence": stats["confidence_sum"] / stats["count"] if stats["count"] > 0 else 0,
                    "min_confidence": stats["min_conf"],
                    "max_confidence": stats["max_conf"],
                }
                for intent, stats in self.intent_stats.items()
            },
            "sample_results": {
                intent: results[:3] for intent, results in self.results.items()
            }
        }

        with open(filename, "w") as f:
            json.dump(output, f, indent=2, default=str)

        print(f"\n[SAVED] Results saved to {filename}")

def main():
    import sys

    total_requests = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    port = sys.argv[2] if len(sys.argv) > 2 else "8001"

    tester = APIStressTest(
        base_url=f"http://127.0.0.1:{port}",
        total_requests=total_requests
    )

    # Run async test
    elapsed = asyncio.run(tester.run_async(batch_size=50, delay_between_batches=0.5))

    # Print results
    tester.print_results()

    # Save detailed results
    tester.save_results()

    print(f"\n[SUCCESS] Stress test completed in {elapsed:.1f} seconds")

if __name__ == "__main__":
    main()

