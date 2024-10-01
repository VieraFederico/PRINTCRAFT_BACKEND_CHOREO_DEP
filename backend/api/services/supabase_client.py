from supabase import create_client, Client
import os

url: str = "https://vvvlpyyvmavjdmfrkqvw.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ2dmxweXl2bWF2amRtZnJrcXZ3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcyNTg0NzYyNywiZXhwIjoyMDQxNDIzNjI3fQ.IOADPN4PKY0kRN3tPhnihJx-XrhpvhuRTeNjaqaDOeQ"
supabase: Client = create_client(url, key)

def upload_file_to_supabase(file, bucket_name, file_name):
    # response = supabase.storage.from_("images").upload(file_name, file)
    response = supabase.storage.from_(bucket_name).upload(file=file, path=file_name, file_options={"content-type": "image/jpeg"})

    if response.is_error:
        raise Exception(response.error)
    return file_name

def test_upload_file():
    # Crear un archivo de prueba
    test_file_name = "images.jpg"

    # Subir el archivo de prueba

    try:
        with open(test_file_name, 'rb') as f:
            file_url = upload_file_to_supabase(f, "images", "darthmaul")
        print(f"File uploaded successfully: {file_url}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        pass

if __name__ == "__main__":
    test_upload_file()