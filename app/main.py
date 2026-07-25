from fastapi import FastAPI
app=FastAPI(
    title="helios",
    description="Distributed LLM Gateway"
)

@app.get("/")
def root():
    return{
        "Project":"Helios",
        "Status":"Running"
    }

