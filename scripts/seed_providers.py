from app.db.database import SessionLocal
from app.db.models import Provider

db = SessionLocal()

providers = [
    Provider(name="Groq", model="llama-3.1-8b-instant", priority=1, enabled=True, status="healthy", cost_per_1k=0.05, region="local"),
    Provider(name="Gemini", model="gemini-3.8-flash", priority=2, enabled=True, status="healthy", cost_per_1k=0.075, region="local"),
]

db.add_all(providers)
db.commit()
db.close()

print("Seeded 2 providers.")