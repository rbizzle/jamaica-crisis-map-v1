# Jamaica Crisis Map - Hurricane Melissa

AI-powered semantic search system for disaster response imagery from Hurricane Melissa's impact on Jamaica.

## Features

- 🗺️ **Semantic Image Search**: Search satellite imagery using natural language queries
- 🤖 **CLIP AI Model**: Advanced image understanding with OpenAI's CLIP
- 🔍 **Geographic Filtering**: Region-of-Interest (ROI) based search
- 📊 **Real NOAA Data**: Hurricane Melissa emergency response imagery
- ⚡ **Cloud-Native**: Deployed on Google Cloud Run with Firestore & ChromaDB

## Architecture

### Backend (Python/Flask)
- **Flask API** with CORS support
- **CLIP Model** (sentence-transformers/clip-ViT-B-32) for semantic search
- **ChromaDB** for vector similarity search
- **Firestore** for metadata storage
- **Rate limiting** and security features
- **Docker containerized** for Cloud Run

### Data Sources
- NOAA Emergency Response Imagery (Hurricane Melissa, Oct 2025)
- High-resolution aerial photography from Jamaica
- Tile server: `stormscdn.ngs.noaa.gov`

## API Endpoints

### `GET /health`
Health check with component status

### `POST /search_images`
Semantic search for disaster imagery
```json
{
  "query": "damaged buildings and flooding",
  "k": 10,
  "roi": {
    "west": -78.0,
    "south": 17.5,
    "east": -76.0,
    "north": 18.7
  }
}
```

### `POST /index_tile`
Index new imagery tiles (requires authentication)
```json
{
  "image_id": "melissa_20251031_001",
  "tile_url": "https://stormscdn.ngs.noaa.gov/...",
  "bounds": {
    "west": -77.39,
    "south": 18.17,
    "east": -77.38,
    "north": 18.18
  },
  "timestamp": "2025-10-31T14:00:00Z"
}
```

### `DELETE /delete_image/<image_id>`
Delete indexed image (requires authentication)

### `GET /stats`
System statistics

## Deployment

### Prerequisites
- Google Cloud Platform account
- gcloud CLI installed
- Docker

### Setup

1. **Build Docker image:**
```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/melissa-backend
```

2. **Deploy to Cloud Run:**
```bash
gcloud run deploy melissa-backend \
  --image gcr.io/YOUR_PROJECT_ID/melissa-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars INDEX_TOKEN=your-secret-token \
  --memory 4Gi \
  --cpu 2 \
  --timeout 350
```

3. **Enable Firestore:**
```bash
gcloud firestore databases create --location=us-central1
```

## Local Development

1. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set environment variables:**
```bash
export INDEX_TOKEN="your-secret-token"
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
```

4. **Run locally:**
```bash
python main.py
```

## Testing

### Index tiles:
```bash
python test_index.py
```

### Search images:
```bash
python test_search.py
```

## Environment Variables

- `INDEX_TOKEN`: Secret token for admin endpoints
- `PORT`: Server port (default: 8080)
- `CHROMA_DIR`: ChromaDB storage path
- `HF_HOME`: Hugging Face cache directory
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to GCP service account key

## Security Features

- ✅ URL validation (SSRF protection)
- ✅ Rate limiting
- ✅ Input sanitization
- ✅ Token-based authentication
- ✅ CORS configuration
- ✅ Request size limits

## Tech Stack

- **Backend**: Python 3.11, Flask
- **AI/ML**: sentence-transformers, CLIP, PyTorch
- **Database**: Google Firestore, ChromaDB
- **Deployment**: Google Cloud Run, Docker
- **Image Processing**: Pillow
- **Vector Search**: ChromaDB with HNSW

## Performance

- Cold start: ~10-15s (CLIP model pre-loaded in image)
- Search latency: ~200-500ms
- Concurrent requests: Up to 80
- Memory: 4GB
- CPU: 2 cores

## License

Private - All Rights Reserved

## Contact

For access or inquiries, contact the repository owner.

---

Built for disaster response and emergency management in Jamaica 🇯🇲
