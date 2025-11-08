import os
import io
import json
import logging
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from functools import wraps

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from PIL import Image

from flask import Flask, request, jsonify, Request, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import firebase_admin
from firebase_admin import credentials, firestore

import chromadb
from sentence_transformers import SentenceTransformer


# -------------------- LOGGING SETUP --------------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# -------------------- CONFIG --------------------

class Config:
    # Chroma storage
    CHROMA_DIR = os.environ.get("CHROMA_DIR", "/app/chroma_db")
    
    # CLIP model
    CLIP_MODEL_NAME = "sentence-transformers/clip-ViT-B-32"
    HF_HOME = os.environ.get("HF_HOME", "/app/hf_cache")
    
    # Authentication
    INDEX_TOKEN = os.environ.get("INDEX_TOKEN", "change-me")
    
    # Firestore
    COLLECTION_NAME = "satellite_images"
    
    # Security
    ALLOWED_DOMAINS = [
        "storms.ngs.noaa.gov",
        "stormscdn.ngs.noaa.gov",
        "noaa.gov",
        "storage.googleapis.com",
        "picsum.photos"  # For testing
    ]
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Search limits
    MAX_RESULTS = 100
    DEFAULT_K = 10
    ROI_MULTIPLIER = 3
    
    # Request timeouts
    DOWNLOAD_TIMEOUT = 20
    MAX_RETRIES = 3
    
    # Rate limiting
    RATE_LIMIT_SEARCH = "100 per hour"
    RATE_LIMIT_INDEX = "1000 per hour"
    
    # Geo bounds validation
    MIN_LAT = -90
    MAX_LAT = 90
    MIN_LON = -180
    MAX_LON = 180


# -------------------- INIT FIREBASE --------------------

def init_firebase():
    """Initialize Firebase Admin SDK."""
    if not firebase_admin._apps:
        try:
            firebase_admin.initialize_app()
            logger.info("Firebase initialized with default credentials")
        except Exception as e:
            logger.warning(f"Default Firebase init failed: {e}, trying credentials file")
            cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            if not cred_path:
                raise RuntimeError(
                    "GOOGLE_APPLICATION_CREDENTIALS env var not set and default app init failed."
                )
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized with credentials file")

init_firebase()
db = firestore.client()


# -------------------- INIT CHROMA + CLIP --------------------

os.makedirs(Config.HF_HOME, exist_ok=True)
os.makedirs(Config.CHROMA_DIR, exist_ok=True)

logger.info("Initializing ChromaDB...")
chroma_client = chromadb.PersistentClient(path=Config.CHROMA_DIR)
chroma_collection = chroma_client.get_or_create_collection(Config.COLLECTION_NAME)
logger.info(f"ChromaDB initialized with {chroma_collection.count()} records")

logger.info("Loading CLIP model...")
clip_model = SentenceTransformer(
    Config.CLIP_MODEL_NAME,
    cache_folder=Config.HF_HOME
)
logger.info("CLIP model loaded successfully")


# -------------------- HTTP SESSION WITH RETRY --------------------

def create_session() -> requests.Session:
    """Create a requests session with retry logic."""
    session = requests.Session()
    retry = Retry(
        total=Config.MAX_RETRIES,
        backoff_factor=0.3,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

http_session = create_session()


# -------------------- FLASK APP --------------------

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per day"],
    storage_uri="memory://"
)


# -------------------- VALIDATION --------------------

class ValidationError(Exception):
    """Custom validation error."""
    pass


def validate_bounds(bounds: Dict[str, float]) -> None:
    """Validate geographic bounds."""
    required_keys = ["west", "south", "east", "north"]
    for key in required_keys:
        if key not in bounds:
            raise ValidationError(f"Missing bounds.{key}")
    
    west, south, east, north = bounds["west"], bounds["south"], bounds["east"], bounds["north"]
    
    if not (Config.MIN_LON <= west <= Config.MAX_LON):
        raise ValidationError(f"Invalid west longitude: {west}")
    if not (Config.MIN_LON <= east <= Config.MAX_LON):
        raise ValidationError(f"Invalid east longitude: {east}")
    if not (Config.MIN_LAT <= south <= Config.MAX_LAT):
        raise ValidationError(f"Invalid south latitude: {south}")
    if not (Config.MIN_LAT <= north <= Config.MAX_LAT):
        raise ValidationError(f"Invalid north latitude: {north}")
    
    if west >= east:
        raise ValidationError("west must be less than east")
    if south >= north:
        raise ValidationError("south must be less than north")


def validate_url(url: str) -> None:
    """Validate URL is from allowed domains (SSRF protection)."""
    if not url.startswith(("http://", "https://")):
        raise ValidationError("URL must start with http:// or https://")
    
    if not any(domain in url for domain in Config.ALLOWED_DOMAINS):
        raise ValidationError(
            f"URL domain not allowed. Allowed domains: {Config.ALLOWED_DOMAINS}"
        )


def validate_image_id(image_id: str) -> None:
    """Validate image_id format."""
    if not image_id or len(image_id) > 200:
        raise ValidationError("image_id must be 1-200 characters")
    
    # Prevent path traversal and injection
    if any(char in image_id for char in ['/', '\\', '\x00', '\n', '\r']):
        raise ValidationError("image_id contains invalid characters")


def validate_k(k: int) -> int:
    """Validate and normalize k parameter."""
    try:
        k = int(k)
    except (ValueError, TypeError):
        raise ValidationError("k must be an integer")
    
    if k < 1:
        raise ValidationError("k must be at least 1")
    if k > Config.MAX_RESULTS:
        raise ValidationError(f"k cannot exceed {Config.MAX_RESULTS}")
    
    return k


# -------------------- AUTHENTICATION --------------------

def require_auth(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get("X-Index-Token") or \
                request.headers.get("Authorization", "").replace("Bearer ", "").strip()
        
        if not token or token != Config.INDEX_TOKEN:
            logger.warning(f"Unauthorized access attempt from {get_remote_address()}")
            return jsonify({"error": "unauthorized"}), 401
        
        return f(*args, **kwargs)
    return decorated_function


# -------------------- HELPERS --------------------

def url_hash(url: str) -> str:
    """Generate a hash of a URL for duplicate detection."""
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def download_image(url: str) -> Image.Image:
    """Download an image from a URL into a PIL Image."""
    logger.info(f"Downloading image from {url}")
    
    try:
        resp = http_session.get(url, timeout=Config.DOWNLOAD_TIMEOUT)
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        raise Exception(f"Timeout downloading image from {url}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to download image: {str(e)}")
    
    try:
        image_bytes = io.BytesIO(resp.content)
        img = Image.open(image_bytes).convert("RGB")
        logger.info(f"Image downloaded successfully, size: {img.size}")
        return img
    except Exception as e:
        raise Exception(f"Failed to open image: {str(e)}")


def encode_image(img: Image.Image) -> List[float]:
    """Generate a CLIP embedding for an image."""
    logger.info("Encoding image with CLIP")
    start_time = datetime.now()
    
    embedding = clip_model.encode(img, normalize_embeddings=True)
    
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"Image encoded in {elapsed:.2f}s")
    
    return embedding.tolist()


def encode_text(text: str) -> List[float]:
    """Generate a CLIP embedding for text."""
    logger.info(f"Encoding text query: '{text}'")
    start_time = datetime.now()
    
    embedding = clip_model.encode(text, normalize_embeddings=True)
    
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"Text encoded in {elapsed:.2f}s")
    
    return embedding.tolist()


def check_duplicate_url(tile_url: str) -> Optional[str]:
    """Check if URL already exists in Firestore."""
    url_hash_value = url_hash(tile_url)
    
    try:
        docs = db.collection(Config.COLLECTION_NAME).where("url_hash", "==", url_hash_value).limit(1).get()
        if docs:
            existing_id = docs[0].id
            logger.info(f"Found duplicate URL, existing image_id: {existing_id}")
            return existing_id
    except Exception as e:
        logger.error(f"Error checking for duplicate URL: {e}")
    
    return None


def upsert_firestore_doc(meta: Dict[str, Any]) -> None:
    """Create/overwrite a Firestore document for a tile."""
    image_id = meta["image_id"]
    
    try:
        db.collection(Config.COLLECTION_NAME).document(image_id).set(meta)
        logger.info(f"Firestore document upserted: {image_id}")
    except Exception as e:
        logger.error(f"Failed to upsert Firestore document: {e}")
        raise


def upsert_chroma_record(meta: Dict[str, Any], embedding: List[float]) -> None:
    """Add/update a record in Chroma."""
    image_id = meta["image_id"]
    
    # ChromaDB doesn't accept None values in metadata - filter them out
    clean_meta = {k: v for k, v in meta.items() if v is not None}
    
    try:
        # Try upsert first (ChromaDB 0.4.0+)
        chroma_collection.upsert(
            ids=[image_id],
            embeddings=[embedding],
            metadatas=[clean_meta],
        )
        logger.info(f"Chroma record upserted: {image_id}")
    except AttributeError:
        # Fallback for older ChromaDB versions
        logger.warning("Chroma upsert not available, using delete+add")
        try:
            chroma_collection.delete(ids=[image_id])
        except Exception as e:
            logger.debug(f"Delete failed (record may not exist): {e}")
        
        chroma_collection.add(
            ids=[image_id],
            embeddings=[embedding],
            metadatas=[clean_meta],
        )
        logger.info(f"Chroma record added: {image_id}")
    except Exception as e:
        logger.error(f"Failed to upsert Chroma record: {e}")
        raise


def rollback_index(image_id: str) -> None:
    """Rollback indexing operation if something fails."""
    logger.warning(f"Rolling back index for {image_id}")
    
    try:
        db.collection(Config.COLLECTION_NAME).document(image_id).delete()
        logger.info(f"Firestore document deleted: {image_id}")
    except Exception as e:
        logger.error(f"Failed to delete Firestore document during rollback: {e}")
    
    try:
        chroma_collection.delete(ids=[image_id])
        logger.info(f"Chroma record deleted: {image_id}")
    except Exception as e:
        logger.error(f"Failed to delete Chroma record during rollback: {e}")


def check_firestore_health() -> bool:
    """Check Firestore connectivity."""
    try:
        # Try to read a single document
        db.collection(Config.COLLECTION_NAME).limit(1).get()
        return True
    except Exception as e:
        logger.error(f"Firestore health check failed: {e}")
        return False


def check_chroma_health() -> bool:
    """Check ChromaDB status."""
    try:
        chroma_collection.count()
        return True
    except Exception as e:
        logger.error(f"ChromaDB health check failed: {e}")
        return False


# -------------------- ROUTES --------------------

@app.before_request
def before_request():
    """Log request details."""
    g.start_time = datetime.now()
    logger.info(f"{request.method} {request.path} from {get_remote_address()}")


@app.after_request
def after_request(response):
    """Log response details."""
    if hasattr(g, 'start_time'):
        elapsed = (datetime.now() - g.start_time).total_seconds()
        logger.info(f"{request.method} {request.path} completed in {elapsed:.2f}s with status {response.status_code}")
    return response


@app.errorhandler(ValidationError)
def handle_validation_error(e):
    """Handle validation errors."""
    logger.warning(f"Validation error: {str(e)}")
    return jsonify({"error": str(e)}), 400


@app.errorhandler(413)
def handle_request_too_large(e):
    """Handle request too large errors."""
    logger.warning("Request entity too large")
    return jsonify({"error": "Request too large"}), 413


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint with component status."""
    firestore_ok = check_firestore_health()
    chroma_ok = check_chroma_health()
    
    status = "ok" if (firestore_ok and chroma_ok) else "degraded"
    status_code = 200 if status == "ok" else 503
    
    return jsonify({
        "status": status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "components": {
            "firestore": "ok" if firestore_ok else "error",
            "chromadb": "ok" if chroma_ok else "error",
            "clip_model": "loaded",
        },
        "metrics": {
            "total_images": chroma_collection.count(),
        }
    }), status_code


@app.route("/index_tile", methods=["POST"])
@require_auth
@limiter.limit(Config.RATE_LIMIT_INDEX)
def index_tile():
    """
    Admin endpoint to index a single NOAA tile by URL.

    Headers:
      X-Index-Token: <INDEX_TOKEN>   (or Authorization: Bearer <INDEX_TOKEN>)

    Body JSON example:
    {
      "image_id": "melissa_1102A_0001",
      "tile_url": "https://storms.ngs.noaa.gov/.../tile/19/123456/789012.png",
      "thumb_url": null,
      "bounds": {
        "west": -77.50,
        "south": 18.00,
        "east": -77.40,
        "north": 18.05
      },
      "timestamp": "2025-11-02T10:21:00Z",
      "metadata": {
        "mission": "melissa",
        "disaster_type": "hurricane"
      }
    }
    """
    try:
        data = request.get_json() or {}
        
        # Validate required fields
        required_fields = ["image_id", "tile_url", "bounds"]
        for f in required_fields:
            if f not in data:
                raise ValidationError(f"Missing field: {f}")
        
        image_id = data["image_id"]
        tile_url = data["tile_url"]
        bounds = data["bounds"]
        timestamp = data.get("timestamp")
        thumb_url = data.get("thumb_url")
        extra_metadata = data.get("metadata", {})
        
        # Validate inputs
        validate_image_id(image_id)
        validate_url(tile_url)
        validate_bounds(bounds)
        
        if thumb_url:
            validate_url(thumb_url)
        
        # Check for duplicate URL
        existing_id = check_duplicate_url(tile_url)
        if existing_id and existing_id != image_id:
            logger.warning(f"Duplicate URL detected, existing ID: {existing_id}")
            return jsonify({
                "warning": "URL already indexed",
                "existing_image_id": existing_id,
                "action": "skipped"
            }), 200
        
        # Compute center point
        center_lat = (bounds["south"] + bounds["north"]) / 2.0
        center_lon = (bounds["west"] + bounds["east"]) / 2.0
        
        # Download and encode image
        img = download_image(tile_url)
        embedding = encode_image(img)
        
        # Prepare metadata
        meta = {
            "image_id": image_id,
            "tile_url": tile_url,
            "thumb_url": thumb_url,
            "url_hash": url_hash(tile_url),
            "west": bounds["west"],
            "south": bounds["south"],
            "east": bounds["east"],
            "north": bounds["north"],
            "center_lat": center_lat,
            "center_lon": center_lon,
            "timestamp": timestamp,
            "indexed_at": datetime.utcnow().isoformat() + "Z",
            **extra_metadata
        }
        
        # Index with rollback on failure
        try:
            upsert_firestore_doc(meta)
            upsert_chroma_record(meta, embedding)
        except Exception as e:
            logger.error(f"Indexing failed, rolling back: {e}")
            rollback_index(image_id)
            raise
        
        logger.info(f"Successfully indexed: {image_id}")
        return jsonify({
            "status": "indexed",
            "image_id": image_id,
            "center": {"lat": center_lat, "lon": center_lon}
        }), 201
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Index operation failed: {e}", exc_info=True)
        return jsonify({"error": f"Failed to index tile: {str(e)}"}), 500


@app.route("/search_images", methods=["POST"])
@limiter.limit(Config.RATE_LIMIT_SEARCH)
def search_images():
    """
    Semantic search endpoint.

    Body JSON:
    {
      "query": "flooded roads near Mandeville",
      "k": 10,
      "roi": {
        "west": -78.0,
        "south": 17.5,
        "east": -76.0,
        "north": 18.7
      }
    }
    """
    try:
        data = request.get_json() or {}
        query = data.get("query", "").strip()
        
        if not query:
            raise ValidationError("query is required")
        
        if len(query) > 500:
            raise ValidationError("query too long (max 500 characters)")
        
        k = validate_k(data.get("k", Config.DEFAULT_K))
        roi = data.get("roi")
        
        # Validate ROI if provided
        if roi:
            validate_bounds(roi)
        
        # Encode query
        q_emb = encode_text(query)
        
        # Determine how many results to fetch
        fetch_count = k * Config.ROI_MULTIPLIER if roi else k
        fetch_count = min(fetch_count, Config.MAX_RESULTS)
        
        # Query ChromaDB
        logger.info(f"Querying ChromaDB for '{query}' with k={fetch_count}")
        result = chroma_collection.query(
            query_embeddings=[q_emb],
            n_results=fetch_count,
            include=["metadatas", "distances"],
        )
        
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        
        hits = []
        for meta, dist in zip(metadatas, distances):
            # ROI filtering
            if roi:
                lat = meta.get("center_lat")
                lon = meta.get("center_lon")
                if lat is None or lon is None:
                    continue
                
                if not (roi["south"] <= lat <= roi["north"]):
                    continue
                if not (roi["west"] <= lon <= roi["east"]):
                    continue
            
            hits.append({
                "image_id": meta.get("image_id"),
                "tile_url": meta.get("tile_url"),
                "thumb_url": meta.get("thumb_url"),
                "center": {
                    "lat": meta.get("center_lat"),
                    "lon": meta.get("center_lon"),
                },
                "bounds": {
                    "west": meta.get("west"),
                    "south": meta.get("south"),
                    "east": meta.get("east"),
                    "north": meta.get("north"),
                },
                "timestamp": meta.get("timestamp"),
                "distance": dist,
                "similarity": 1 - dist,  # Convert distance to similarity score
            })
            
            # Stop once we have enough results
            if len(hits) >= k:
                break
        
        logger.info(f"Returning {len(hits)} results for query '{query}'")
        
        return jsonify({
            "query": query,
            "results": hits,
            "count": len(hits),
            "requested": k
        }), 200
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Search operation failed: {e}", exc_info=True)
        return jsonify({"error": f"Search failed: {str(e)}"}), 500


@app.route("/delete_image/<image_id>", methods=["DELETE"])
@require_auth
def delete_image(image_id: str):
    """Delete an indexed image."""
    try:
        validate_image_id(image_id)
        
        # Delete from Firestore
        db.collection(Config.COLLECTION_NAME).document(image_id).delete()
        logger.info(f"Deleted from Firestore: {image_id}")
        
        # Delete from ChromaDB
        chroma_collection.delete(ids=[image_id])
        logger.info(f"Deleted from ChromaDB: {image_id}")
        
        return jsonify({"status": "deleted", "image_id": image_id}), 200
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Delete operation failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/stats", methods=["GET"])
def stats():
    """Get system statistics."""
    try:
        total_images = chroma_collection.count()
        
        # Get sample of recent images
        recent_docs = db.collection(Config.COLLECTION_NAME)\
            .order_by("indexed_at", direction=firestore.Query.DESCENDING)\
            .limit(5)\
            .get()
        
        recent_images = [doc.to_dict().get("image_id") for doc in recent_docs]
        
        return jsonify({
            "total_images": total_images,
            "recent_images": recent_images,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 200
        
    except Exception as e:
        logger.error(f"Stats operation failed: {e}")
        return jsonify({"error": str(e)}), 500


# Entry point for Cloud Run / gunicorn
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
