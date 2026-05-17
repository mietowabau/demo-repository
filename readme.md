[ Users (Shared View) ]
       |
       | HTTP (REST)
       v
+---------------------------------------------------+
|               MAIN API (FastAPI)                  |
|          Deployed on: GCP Cloud Run               |
+---------------------------------------------------+
       |                  |                  |
 0. Upload CSV      1. Save Metadata   2. Publish Event
       |                  |                  |
       v                  v                  v
+--------------+   +--------------+   +-----------------+
| Cloud Storage|   |  Cloud SQL   |   | Cloud Pub/Sub   |
|  (Raw CSV &  |   | (PostgreSQL) |   | (Task Queue)    |
| Processed)   |   |              |   |                 |
+--------------+   +--------------+   +-----------------+
                          ^                  |
                          | 3. Update Status | 4. Consume Event
                          |                  v
                   +---------------------------------------------------+
                   |                 WORKER (FastAPI)                  |
                   |            Deployed on: GCP Cloud Run             |
                   +---------------------------------------------------+
                                          |
                                          v
                               +---------------------+
                               | Processing Pipeline |
                               +---------------------+
                                          |
                        +-----------------+-----------------+
                        |                 |                 |
                   5. Schema Check   6. ML Matching    7. Human Review
                    (Static Rules)    (Vertex AI)       (Main API)

Aby uruchomić ten kod lokalnie, potrzebujesz zainstalowanego Pythona oraz narzędzia **Uvicorn**, które służy jako serwer do obsługi aplikacji FastAPI.

Oto instrukcja krok po kroku, jak przygotować środowisko i wystartować oba serwisy.

---

### Krok 1: Przygotowanie środowiska i instalacja

1. Stwórz nowy folder na projekt i wejdź do niego.
2. Zintegruj i zainstaluj wymagane biblioteki za pomocą terminala:

```bash
pip install fastapi uvicorn pydantic python-multipart

```

*(Uwaga: `python-multipart` jest wymagany przez FastAPI do obsługi przesyłania plików przez `UploadFile`)*.

---

### Krok 2: Struktura plików

Utwórz w swoim folderze trzy pliki i wklej do nich kod z poprzedniej wiadomości:

* `models.py`
* `main_api.py`
* `worker.py`

---

### Krok 3: Uruchomienie serwisów

Ponieważ oba serwisy (Main API i Worker) to aplikacje FastAPI, muszą działać na różnych portach sieciowych, aby nie blokować się nawzajem. Otwórz dwa osobne okna terminala.

#### Terminal 0: Uruchomienie Głównego API (Port 8000)

W pierwszym terminalu wpisz:

```bash
uvicorn main_api:app --reload --port 8000

```

#### Terminal 1: Uruchomienie Workera (Port 8001)

W drugim terminalu wpisz:

```bash
uvicorn worker:worker_app --reload --port 8001

```

> **Co oznaczają te flagi?**
> * `main_api:app` – szuka obiektu `app` w pliku `main_api.py`.
> * `--reload` – automatycznie restartuje serwer, gdy zmienisz coś w kodzie (przydatne przy deweloperce).
> * `--port` – definiuje, pod jakim adresem aplikacja będzie dostępna.
> 
> 

---

### Krok 4: Testowanie przepływu (Interfejs Swagger UI)

FastAPI automatycznie generuje genialną dokumentację interaktywną, pod którą możesz przetestować cały system bez pisania frontendu.

1. **Główne API:** Otwórz w przeglądarce adres: `[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)`
2. **Worker:** Otwórz w przeglądarce adres: `[http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)`

#### Scenariusz testowy w GUI:

* **Dodanie pliku:** W Głównym API (`port 8000`) rozwiń endpoint `POST /upload/`, kliknij *Try it out*, wpisz dowolnego użytkownika w polu `user`, załącz mały plik tekstowy (zmień mu rozszerzenie na `.csv`) i kliknij *Execute*. W odpowiedzi otrzymasz JSON z informacją o pliku o indeksie `0`.
* **Przeglądanie:** Uruchom endpoint `GET /files/`. Zobaczysz, że plik ma status `UPLOADED`.
* **Praca Workera:** Przejdź do zakładki Workera (`port 8001`). Rozwiń endpoint `POST /process-pubsub-message/`, kliknij *Try it out*, wpisz `file_id: 0` i kliknij *Execute*. W konsoli terminala Workera zobaczysz symulację działania ML, a w odpowiedzi informację o nowym statusie (np. `PENDING_HUMAN_REVIEW`).
* **Weryfikacja:** Ponownie wywołaj `GET /files/` w Głównym API. Zobaczysz zaktualizowany status oraz propozycje mapowania wyplute przez "model ML".