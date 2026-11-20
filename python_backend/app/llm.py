from huggingface_hub import InferenceClient
from .config import HF_TOKEN, HF_MODEL, HF_PROVIDER, HF_TEMPERATURE, HF_MAX_TOKENS

class HuggingFaceLLMService:
    """Optional hosted inference adapter. It never computes or changes claim amounts."""
    def __init__(self):
        self.enabled = bool(HF_TOKEN)
        self.client = InferenceClient(provider=HF_PROVIDER, api_key=HF_TOKEN) if self.enabled else None

    def explain(self, claim_summary: str, deterministic_result: dict) -> str | None:
        if not self.enabled:
            return None
        prompt = (
            "You are an audit explaination assistant. Do not change the decision or amounts. "
            "Summarize the deterministic result in concise plain English.\n"
            f"Claim: {claim_summary}\nResult: {deterministic_result}"
        )
        try:
            response = self.client.chat_completion(
                model=HF_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=HF_TEMPERATURE,
                max_tokens=HF_MAX_TOKENS,
            )
            return response.choices[0].message.content
        except Exception:
            # Provider/model errors must not block deterministic policy evaluation.
            return None
