
from api.services.supabase_client import *
def test_upload_file():
    # Crear un archivo de prueba
    test_file_name = "images.jpg"
    bucket_name = "images"
    file_name = "darthmaul"

    # Subir el archivo de prueba
    try:
        with open(test_file_name, 'rb') as f:
            file_url = upload_file_to_supabase(f, bucket_name, "banana")
        print(f"File uploaded successfully: {file_url}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_upload_file()