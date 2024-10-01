from supabase import create_client, Client
import os

url: str = "https://vvvlpyyvmavjdmfrkqvw.supabase.co"
key: str = os.environ.get("DB_KEY")
supabase: Client = create_client(url, key)


def upload_file_to_supabase(file, bucket_name, file_name):
    """response = supabase.storage.from_(bucket_name).upload(file_name, file)
    if response.get('error'):
        raise Exception("Error uploading file to Supabase Storage")"""
    return "https://es.wikipedia.org/wiki/Obi-Wan_Kenobi"
