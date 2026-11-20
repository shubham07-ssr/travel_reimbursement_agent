from fastapi import FastAPI
from .schemas import Claim
from .workflow import run_workflow
from .sample_data import SAMPLE_CLAIMS

app = FastAPI(title="Travel Reimbursement Approval Agent", version="0.1.0")

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/claims/sample")
def sample_claims():
    return SAMPLE_CLAIMS

@app.post("/api/claims/evaluate")
def evaluate(claim: Claim):
    return run_workflow(claim).model_dump(mode="json")

@app.post("/api/claims/evaluate-batch")
def evaluate_batch(claims: list[Claim]):
    return [run_workflow(c).model_dump(mode="json") for c in claims]
