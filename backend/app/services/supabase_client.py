import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class SupabaseService:
    def __init__(self):
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            print("Warning: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not found in environment.")
            self.client = None
        else:
            self.client: Client = create_client(url, key)

    def insert_chunks(self, chunks: list[dict]):
        if not self.client: return
        return self.client.table("document_chunks").insert(chunks).execute()

    def semantic_search(self, embedding: list[float], limit: int = 5):
        if not self.client: return []
        response = self.client.rpc("match_chunks", {
            "query_embedding": embedding,
            "match_threshold": 0.5,
            "match_count": limit
        }).execute()
        return response.data

    def insert_expert_dna(self, data: dict):
        """Final commit of expert-verified logic into the production vault."""
        if not self.client: return
        return self.client.table("expert_dna").insert(data).execute()

    def expert_vault_search(self, embedding: list[float], limit: int = 1):
        """High-purity search against verified logic only."""
        if not self.client: return []
        response = self.client.rpc("match_expert_dna", {
            "query_embedding": embedding,
            "match_threshold": 0.40, # Lowered — short queries vs long expert paragraphs yield ~0.5-0.6 similarity
            "match_count": limit
        }).execute()
        return response.data

    def insert_chat_audit_log(self, data: dict):
        """Logs the LangGraph chat execution trace to the database."""
        if not self.client: return
        return self.client.table("chat_audit_logs").insert(data).execute()

    def get_count(self, table: str) -> int:
        """Returns the total row count for a given table."""
        if not self.client: return 0
        try:
            # We use a select with head=True to just get the count
            response = self.client.table(table).select("*", count="exact").limit(0).execute()
            return response.count if response.count is not None else 0
        except Exception as e:
            print(f"Error fetching count for {table}: {e}")
            return 0

