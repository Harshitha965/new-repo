from ...models.chat_state import ChatState
from ...services.embeddings import EmbeddingService
from ...services.supabase_client import SupabaseService
from openai import OpenAI
import os
import time

def retrieve_context_node(state: ChatState) -> ChatState:
    print(f"--- CHAT: Retrieval Node ---")
    embedder = EmbeddingService()
    db = SupabaseService()
    
    # 1. Semantic Search against Expert DNA Vault
    query_vector = embedder.get_embedding(state.query)
    results = db.expert_vault_search(query_vector, limit=3)
    
    if results:
        state.confidence = results[0].get("similarity", 0.0)
        state.retrieved_cases = results
        state.persona_mode = "primary" if state.confidence > 0.50 else "deputy"
    else:
        state.confidence = 0.0
        state.retrieved_cases = []
        state.persona_mode = "offline"
        
    return state

def reasoning_node(state: ChatState) -> ChatState:
    print(f"--- CHAT: Reasoning Node ---")
    if not state.retrieved_cases:
        state.rationale = "No relevant Master Cases found in the Logic Vault. I must decline giving clinical advice."
        return state
        
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    context = ""
    for i, r in enumerate(state.retrieved_cases):
        context += f"[Case {i+1}]: {r.get('expert_decision', '')}\n"
        
    reasoning_prompt = f"""You are the logical core of a medical Digital Twin.
Analyze the user's query against the retrieved Master Cases.
Write a strict, step-by-step 'Chain of Thought' explaining WHY the Master Cases apply to the query and what the protocol should be.
This rationale is for the tech team's audit log, not the patient.

USER QUERY: {state.query}

RETRIEVED MASTER CASES:
{context}

CHAIN OF THOUGHT RATIONALE:"""

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.0,
        messages=[{"role": "user", "content": reasoning_prompt}]
    )
    
    state.rationale = completion.choices[0].message.content
    return state

def generation_node(state: ChatState) -> ChatState:
    print(f"--- CHAT: Generation Node ---")
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    system_prompt = f"""You are Dr. Sarah Jenkins' Digital Twin, a Senior Reproductive Endocrinologist.
You must apply strict clinical safety protocols while maintaining a deeply empathetic, patient-centric bedside manner.
Instead of asking endless questions, provide direct, actionable medical guidance based ONLY on your explicit rationale.
If your rationale indicates no cases were found, you must state that you do not have human-verified guidance on this yet.

YOUR EXPLICIT RATIONALE (Audit Trace):
{state.rationale}
"""

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": state.query}
        ]
    )
    
    state.response = completion.choices[0].message.content
    return state

def audit_node(state: ChatState) -> ChatState:
    print(f"--- CHAT: Audit Logger Node ---")
    db = SupabaseService()
    
    try:
        db.insert_chat_audit_log({
            "expert_id": state.expert_id,
            "session_id": state.session_id,
            "user_query": state.query,
            "retrieved_cases": [r.get("scenario_id", "Unknown") for r in state.retrieved_cases],
            "rationale": state.rationale,
            "final_response": state.response,
            "confidence": state.confidence,
            "latency_ms": 0 # Track latency if desired, 0 for now
        })
    except Exception as e:
        print(f"Audit log failed: {e}")
        
    return state
