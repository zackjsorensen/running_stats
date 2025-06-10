from supabase import create_client, Client
from config import sb_key, sb_url

supabase: Client = create_client(sb_url, sb_key)
