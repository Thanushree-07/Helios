import random
from locust import HttpUser, task, between

API_KEY = "thanu"  # match whatever your .env actually uses

# A pool of distinct "base" questions — simulates real variety in traffic
BASE_QUESTIONS = [
    "What is Python used for?",
    "How does a circuit breaker pattern work?",
    "What causes earthquakes?",
    "Explain how Redis caching works",
    "What is the difference between TCP and UDP?",
    "How do neural networks learn?",
    "What is Docker used for?",
    "Explain the CAP theorem",
]

# Paraphrased versions of SOME of the above — simulates Quora-style
# "same question, different wording" traffic that semantic cache should catch
PARAPHRASES = {
    "What is Python used for?": "What are common uses of the Python language?",
    "How does a circuit breaker pattern work?": "Can you explain the circuit breaker design pattern?",
    "What causes earthquakes?": "Why do earthquakes happen?",
    "What is Docker used for?": "What problems does Docker solve?",
}


class HeliosUser(HttpUser):
    wait_time = between(0.5, 2)  # simulates real users pausing between requests

    @task(5)
    def ask_new_or_repeated_question(self):
        """70% of traffic: a mix of brand-new and exact-repeat questions."""
        prompt = random.choice(BASE_QUESTIONS)
        self._send(prompt)

    @task(2)
    def ask_paraphrased_question(self):
        """20% of traffic: reworded versions of questions already asked."""
        original = random.choice(list(PARAPHRASES.keys()))
        prompt = PARAPHRASES[original]
        self._send(prompt)

    def _send(self, prompt):
        self.client.post(
            "/chat",
            json={"prompt": prompt},
            headers={"X-API-Key": API_KEY},
        )