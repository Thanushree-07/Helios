import httpx
from fastapi import HTTPException

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3"


class LlamaProvider:
    def __init__(self):
        self.client = httpx.Client(base_url=OLLAMA_BASE_URL, timeout=30.0)

    def generate(self, prompt: str) -> str:
        try:
            response = self.client.post(
                "/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                },
            )
            response.raise_for_status()

        except httpx.ConnectError as e:
            print("OLLAMA ERROR: connection failed —", e)
            raise HTTPException(
                status_code=503,
                detail="Ollama is not reachable. Is `ollama serve` running?",
            )
        except httpx.HTTPStatusError as e:
            print("OLLAMA ERROR:", e)
            raise HTTPException(status_code=500, detail=str(e))

        data = response.json()
        return data["message"]["content"]