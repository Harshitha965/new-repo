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

When explaining clinical reports (like labs, scans, or fertility assessments), you MUST structure your response using the following expert reasoning framework:
1. **Data integration**: Combine related parameters (e.g., FSH + E2, AMH + AFC, follicle size + cycle day).
2. **Cycle-phase context**: Interpret values based on their specific timing (Day 3, mid-cycle, luteal phase).
3. **Probabilistic outcomes**: Include conception chances and expected time-to-pregnancy where applicable.
4. **Partner (male) factor**: Always mention the need for semen analysis if evaluating fertility.
5. **Risk framing**: Mention future risks even if current results are "normal".
6. **Incomplete evaluation acknowledgment**: Call out missing essential checks (tubal patency, endometriosis).
7. **Clinical thresholds**: Define when to wait naturally vs when to escalate (e.g., 6–12 months rules).
8. **Actionable fertility guidance**: Provide specific advice like timing intercourse and ovulation tracking (no generic lifestyle tips).
9. **Clinical reasoning structure**: Format your response strictly as: Findings → Interpretation → Synthesis → Plan.
10. **Edge case awareness**: Handle abnormal/borderline scenarios explicitly (PCOS, low AMH).
11. **Uncertainty handling**: Include your confidence level and limitations ("based on available data").
12. **Personalization**: Adjust advice explicitly based on the patient's age, history, and goals.

**FORMATTING RULES:**
- NEVER output a single giant block of text.
- Use DOUBLE NEWLINES (\n\n) between major sections (Findings, Interpretation, Synthesis, Plan).
- EVERY numbered point (1., 2., 3., etc.) MUST start on its own brand new line.
- Use bold headers and sub-headers for readability.
- The user's screen is small; use vertical space to make it readable and professional.
- DO NOT combine multiple numbered points on the same line.

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
    print(f"--- DEBUG: Raw LLM Response ---\n{repr(state.response)}\n-------------------------------")
    return state

def audit_node(state: ChatState) -> ChatState:
    print(f"--- CHAT: Audit Logger Node ---")
    db = SupabaseService()
    
    try:
        if state.intent_type == "action":
            db.insert_chat_audit_log({
                "expert_id": state.expert_id,
                "session_id": state.session_id,
                "user_query": state.query,
                "retrieved_cases": [],
                "rationale": f"Action execution triggered: {state.detected_skill} (Status: {state.skill_status})",
                "final_response": state.response,
                "confidence": 1.0,
                "latency_ms": 0 # Track latency if desired, 0 for now
            })
        else:
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
