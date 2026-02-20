from fastapi import FastAPI
from fastapi import Request
import json
from helpers.search import hybrid_semantic_vector_search
from helpers.common import build_context_from_hits
from helpers.open_ai import generate_llm_response, guardrail_validate
from helpers.prompts import TECH_USER_PROMPT, FINANCE_USER_PROMPT

app = FastAPI()

@app.get("/")
def index():
    return {"response": "hello world v2"}

@app.post("/get-response")
async def get_response(request: Request):
    
    body = await request.json()
    prompt = body.get("prompt")
    prompt_type = body.get("type")

    # this block will be removed later and actual prompt variable will be used.
    # currently testing from Postman is being difficult with huge tech prompt.
    # that's why loading tech and finance user prompt from prompts.py file.
    # later, these prompts will come from copilot studio agent.
    if prompt_type == "technology":
        prompt = TECH_USER_PROMPT
    else:
        prompt = FINANCE_USER_PROMPT

    print("Performing hybrid search against search index....")
    hits = hybrid_semantic_vector_search(prompt, k=5)

    print("Building context from search result....")
    context = build_context_from_hits(hits)

    print("Generating augmented LLM response....")
    rag_answer = generate_llm_response(context=context, prompt=prompt, prompt_type=prompt_type)
    
    print("Performing guardrail validation for hallucination check....")
    validated_response = guardrail_validate(context=context, prompt=prompt, rag_answer=rag_answer)

    return validated_response