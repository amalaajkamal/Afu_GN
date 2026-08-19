
# AFUGN Member Directory API

Unofficial JSON API for the Age-Friendly University Global Network member directory (scraped from [afugn.org](https://www.afugn.org/afugn-members)). Not affiliated with or endorsed by AFUGN.

## Running Instructions

### 1. Install Dependencies

Ensure you have Python installed, then run:

```bash
pip install -r requirements.txt
```

### 2. Start the API Server

Run the FastAPI server using Uvicorn:

```bash
uvicorn api:app --reload --port 8000
```

### 3. Usage

Once the server is running, you can access the API locally:

- **Swagger UI (Interactive Docs):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Base Endpoint:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Get All Members:** [http://127.0.0.1:8000/members](http://127.0.0.1:8000/members)
- **Get Meta Information:** [http://127.0.0.1:8000/meta](http://127.0.0.1:8000/meta)
- **Force Refresh:** `POST` to [http://127.0.0.1:8000/refresh](http://127.0.0.1:8000/refresh)

*Note: The first request to the API may take some time as the scraper runs to build the initial cache. Subsequent requests will be served instantly from memory.*
