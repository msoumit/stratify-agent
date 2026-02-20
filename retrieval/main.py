from fastapi import FastAPI
from fastapi import Request
import json
from helpers.search import hybrid_semantic_vector_search
from helpers.common import build_context_from_hits
from helpers.open_ai import generate_llm_response, guardrail_validate

app = FastAPI()

@app.get("/")
def index():
    return {"response": "hello world v2"}

@app.post("/get-response")
async def get_response(request: Request):
    
    body = await request.json()
    prompt = body.get("prompt")

    print("Performing hybrid search against search index....")
    hits = hybrid_semantic_vector_search(prompt, k=5)

    print("Building context from search result....")
    context = build_context_from_hits(hits)

    print("Generating augmented LLM response....")
    rag_answer = generate_llm_response(context=context, prompt=prompt)
    
    # deliberate attempt to tamper rag answer for hallucination check
    # rag_answer["answer"] = str(rag_answer["answer"]).replace("Asset", "Insurance")
    
    print("Performing guardrail validation for hallucination check....")
    validated_response = guardrail_validate(context=context, prompt=prompt, rag_answer=rag_answer)

    return validated_response