from .policy import evaluate_claim
from .llm import HuggingFaceLLMService

def run_workflow(claim):
    # LangGraph is used when installed; deterministic evaluation remains the source of truth.
    def evaluate_node(state):
        return {"result": evaluate_claim(state["claim"])}
    try:
        from langgraph.graph import StateGraph, END
        from typing_extensions import TypedDict
        class State(TypedDict):
            claim: object
            result: object
        graph = StateGraph(State)
        graph.add_node("policy_and_tools", evaluate_node)
        graph.set_entry_point("policy_and_tools")
        graph.add_edge("policy_and_tools", END)
        result = graph.compile().invoke({"claim": claim})["result"]
    except Exception:
        result = evaluate_claim(claim)

    llm = HuggingFaceLLMService()
    # LLM is deliberately advisory; the authoritative structured output remains deterministic.
    llm.explain(claim.model_dump_json(), result.model_dump(mode="json"))
    return result
