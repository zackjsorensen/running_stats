from supabase import create_client, Client
from config import sb_key, sb_url
import pandas as pd


supabase: Client = create_client(sb_url, sb_key)

res = supabase.table("performance").select("*").execute()

