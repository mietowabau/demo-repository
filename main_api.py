# 2. Główne API (main_api.py)
# Ten serwis przyjmuje pliki od użytkowników, zapisuje metadane (używając indeksów od 0) i wystawia endpointy do przeglądania wszystkich plików oraz rozwiązywania konfliktów.

from fastapi import FastAPI, UploadFile, BackgroundTasks
from models import FileMetadata, FileStatus
from typing import Dict, List

app = FastAPI(title="Main API - CSV Parser")

# Symulacja bazy danych (Cloud SQL) i storage'u. Indeksowanie zaczynamy od 0.
fake_db: Dict[int, FileMetadata] = {}
current_file_index = 0

def mock_publish_to_pubsub(file_index: int):
    """Symulacja wysłania wiadomości do Cloud Pub/Sub, która uruchomi Workera."""
    print(f"[Pub/Sub] Published event for file index {file_index}")
    # W rzeczywistości tutaj używamy biblioteki google-cloud-pubsub

@app.post("/upload/", response_model=FileMetadata)
async def upload_file(file: UploadFile, user: str, background_tasks: BackgroundTasks):
    global current_file_index
    
    # Krok 0: Upload i rejestracja pliku (z użyciem indeksu 0 dla pierwszego elementu)
    file_id = current_file_index
    
    # Symulacja zapisu do GCS
    print(f"[GCS] Saving {file.filename} to gs://bucket/raw/{file_id}_{file.filename}")
    
    new_file = FileMetadata(
        id=file_id,
        filename=file.filename,
        status=FileStatus.UPLOADED,
        uploaded_by=user
    )
    fake_db[file_id] = new_file
    
    current_file_index += 1
    
    # Asynchroniczne wysłanie zadania na kolejkę
    background_tasks.add_task(mock_publish_to_pubsub, file_id)
    
    return new_file

@app.get("/files/", response_model=List[FileMetadata])
async def list_files():
    """Współdzielony widok - każdy użytkownik widzi pliki od indeksu 0 w górę."""
    return list(fake_db.values())

@app.post("/files/{file_id}/human-review", response_model=FileMetadata)
async def human_resolution(file_id: int, manual_mapping: Dict[str, str]):
    """Endpoint do ręcznego mapowania, jeśli ML zawiódł."""
    if file_id not in fake_db:
        return {"error": "File not found"}
        
    file_record = fake_db[file_id]
    if file_record.status == FileStatus.PENDING_HUMAN_REVIEW:
        # Symulacja zatwierdzenia schematu i końcowego parsowania
        print(f"[Parser] Applying manual mapping for file {file_id}: {manual_mapping}")
        file_record.status = FileStatus.PROCESSED_MANUALLY
        file_record.ml_suggestions = None
        
    return file_record