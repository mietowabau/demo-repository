# 3. Worker Przetwarzający (worker.py)
# Worker działa w tle (np. wyzwalany przez wiadomości z Pub/Sub typu "Push" do ukrytego endpointu FastAPI lub jako osobny proces nasłuchujący).


from fastapi import FastAPI
from pydantic import ValidationError
from models import TargetCsvSchema, FileStatus, FileMetadata
import random

worker_app = FastAPI(title="Worker API - Data Processing")

def mock_get_from_db(file_id: int) -> FileMetadata:
    # Symulacja pobrania z bazy danych
    return FileMetadata(id=file_id, filename="data.csv", status=FileStatus.UPLOADED, uploaded_by="user1")

def mock_update_db(file_metadata: FileMetadata):
    # Symulacja aktualizacji w Cloud SQL
    print(f"[DB Update] File {file_metadata.id} status changed to {file_metadata.status.value}")

def simulate_ml_model(headers: list) -> tuple[float, dict]:
    """Symuluje odpowiedź z Vertex AI (zwraca pewność modelu i propozycję mapowania)."""
    confidence = random.uniform(0.4, 0.99)
    mapping = {"Imię": "first_name", "Nazwisko": "last_name", "Mail": "email", "Wiek": "age"}
    return confidence, mapping

@worker_app.post("/process-pubsub-message/")
async def process_file(file_id: int):
    """Ten endpoint jest wywoływany przez Pub/Sub (Event-Driven)."""
    
    # 0. Pobranie danych
    file_record = mock_get_from_db(file_id)
    print(f"Worker started processing file {file_id}")
    
    # Symulacja zawartości surowego pliku pobranego z Cloud Storage
    raw_data = {"Imię": "Jan", "Nazwisko": "Kowalski", "Mail": "jan@example.com", "Wiek": "30"}
    
    # 1. Twarda Walidacja (Reguły Statyczne)
    try:
        # Pydantic odrzuci to, bo oczekuje np. 'first_name', a dostał 'Imię'
        parsed_data = TargetCsvSchema(**raw_data)
        file_record.status = FileStatus.PROCESSED
        mock_update_db(file_record)
        return {"status": "success", "method": "strict"}
        
    except ValidationError:
        print(f"Strict validation failed for file {file_id}. Moving to ML processing...")
    
    # 2. Dopasowanie przez Machine Learning
    confidence, mapping_suggestions = simulate_ml_model(list(raw_data.keys()))
    
    if confidence > 0.85:
        # Wysoka pewność ML - mapujemy i procesujemy
        file_record.status = FileStatus.PROCESSED_BY_ML
        print(f"ML successfully mapped file {file_id} with confidence {confidence:.2f}")
    else:
        # 3. Interwencja Człowieka - Niska pewność ML
        file_record.status = FileStatus.PENDING_HUMAN_REVIEW
        file_record.ml_suggestions = mapping_suggestions
        print(f"ML confidence low ({confidence:.2f}). Forwarding file {file_id} to human review.")
        
    mock_update_db(file_record)
    return {"status": "processed", "final_state": file_record.status.value}