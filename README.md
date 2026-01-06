# AML Name-to-Country Origin Classifier - PoC

A proof-of-concept system for predicting the likely country of origin for a person's first and last name. Designed specifically for Anti-Money Laundering (AML) compliance system.

**📋 For Production Deployment:** See [Deployment Summary](deployment_summary.md) | [OpenAPI Spec](openapi.yaml) | [Architecture Diagram](architecture_diagram.md)

## Quick Start

### Prerequisites
- Docker & Docker Compose (or Python 3.9+)
- curl (for testing)

### Option 1: Docker Compose (Recommended)

```bash
# Start the service
docker-compose up -d

# Wait for container to be healthy (10-15 seconds)
docker-compose logs -f

# Test the API
./test_api.sh

# Stop the service
docker-compose down
```

### Option 2: Manual Docker Build

```bash
# Build the image
./build.sh

# Run the container
docker run -p 5050:5050 aml-name-classifier:latest
```

### Option 3: Local Python Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Flask app
python app.py

# In another terminal, run tests
./test_api.sh
```

---

## API Documentation

### Health Check
```bash
curl http://localhost:5050/health
```

**Response (200 OK):**
```json
{
    "status": "healthy",
    "service": "AML Name Origin Classifier",
    "timestamp": "2025-12-30T12:00:00.000000"
}
```

---

### Classify Single Name

**Endpoint:** `POST /api/classify`

**Request:**
```bash
curl -X POST http://localhost:5050/api/classify \
    -H "Content-Type: application/json" \
    -d '{
        "first_name": "Vladimir",
        "last_name": "Putin"
    }'
```

**Response (200 OK):**
```json
{
    "success": true,
    "query": {
        "first_name": "Vladimir",
        "last_name": "Putin"
    },
    "results": [
        ["Russia", 0.98]
    ],
    "confidence": 0.98,
    "explanation": "Classified using n-gram and pattern analysis",
    "method": "ensemble_classification"
}
```

---

### Batch Classification

**Endpoint:** `POST /api/batch`

**Request (up to 1000 names):**
```bash
curl -X POST http://localhost:5050/api/batch \
    -H "Content-Type: application/json" \
    -d '{
        "names": [
            {"first_name": "John", "last_name": "Smith"},
            {"first_name": "Michał", "last_name": "Wilkowski"},
            {"first_name": "Ahmed", "last_name": "Al-Rashid"},
            {"first_name": "Jean", "last_name": "Dupont"}
        ]
    }'
```

**Response (200 OK):**
```json
{
    "success": true,
    "count": 4,
    "results": [
        {
            "name": "John Smith",
            "origins": [["US", 0.85], ["UK", 0.12]],
            "confidence": 0.85
        },
        {
            "name": "Michał Wilkowski",
            "origins": [["Poland", 0.96]],
            "confidence": 0.96
        },
        {
            "name": "Ahmed Al-Rashid",
            "origins": [["Arab", 0.90]],
            "confidence": 0.90
        },
        {
            "name": "Jean Dupont",
            "origins": [["France", 0.88]],
            "confidence": 0.88
        }
    ]
}
```

---

### Get API Version & Info

**Endpoint:** `GET /api/version`

```bash
curl http://localhost:5050/api/version
```

**Response:**
```json
{
    "version": "1.0.0",
    "service": "AML Name Origin Classifier PoC",
    "description": "Multi-stage pipeline for predicting country of origin from person names",
    "countries_supported": ["US", "UK", "Poland", "Russia", "Germany", "France", "Spain", "Italy", "China", "Arab"],
    "features": [
        "n-gram probability models",
        "linguistic pattern matching",
        "database lookup with fuzzy matching",
        "confidence scoring",
        "batch processing"
    ]
}
```

---

## Performance Characteristics

- **Latency:** ~5-10ms per name (single classification)
- **Throughput:** 100-200 names/sec per CPU core
- **Batch Processing:** Up to 1,000 names per request
- **Memory:** ~50MB for model initialization + minimal per-request overhead

---

## Algorithm Overview

The classifier uses a **4-stage ensemble pipeline**:

### Stage 1: Normalization
- Unicode normalization (NFC/NFD)
- Diacritic removal (é → e, ł → l, Ø → O)
- Transliteration (Cyrillic/Arabic to Latin)
- Lowercase conversion

### Stage 2: Feature Extraction
- **N-gram Models:** Character bigrams/trigrams from training data
- **Linguistic Patterns:** Suffix/prefix rules (e.g., "-ski" → Poland)
- **Phonetic Features:** Vowel/consonant patterns

### Stage 3: Multi-Model Scoring
- **N-gram Score (40%):** Probability of character sequences
- **Pattern Score (50%):** Linguistic feature matching
- **Database Score (10%):** Fuzzy matching against known names

### Stage 4: Confidence & Ranking
- Scores weighted and aggregated
- Results ranked by confidence
- Multiple origins returned when appropriate (e.g., "Mary Wang" → China + US cultural mix)

---

## Supported Countries

Current model covers origin detection for:
- **Western:** US, UK, Germany, France, Spain, Italy
- **Eastern European:** Poland, Russia
- **Asian:** China
- **Middle Eastern:** Arab countries (Saudi Arabia, UAE, Egypt, etc.)

Easy to extend: Add new country models to `name_classifier.py:load_models()`

---

## Testing

### Run Full Test Suite
```bash
./test_api.sh
```

Tests include:
- ✓ Health check
- ✓ Version endpoint
- ✓ Single name classification (8 test cases)
- ✓ Batch processing
- ✓ Error handling
- ✓ 404 handling

### Run Evaluation Metrics
```bash
python evaluate.py
```

Evaluation metrics include:
- ✓ Top-1 and Top-3 Accuracy
- ✓ Mean Reciprocal Rank (MRR)
- ✓ Per-country F1 scores
- ✓ Expected Calibration Error (ECE)
- ✓ Per-category accuracy breakdown
- ✓ Error analysis

The evaluation runs on a test dataset of 120 names across 10 categories (common Western, distinctive Polish/Russian/Arab/etc., multicultural, and typo/transliteration variants).

### Manual Testing Examples

**Polish Name:**
```bash
curl -X POST http://localhost:5050/api/classify \
    -H "Content-Type: application/json" \
    -d '{"first_name":"Michał","last_name":"Wilkowski"}'
# Expected: Poland (0.85-0.96 confidence)
```

**Russian Name:**
```bash
curl -X POST http://localhost:5050/api/classify \
    -H "Content-Type: application/json" \
    -d '{"first_name":"Vladimir","last_name":"Putin"}'
# Expected: Russia (0.90-0.98 confidence)
```

**Multicultural Name:**
```bash
curl -X POST http://localhost:5050/api/classify \
    -H "Content-Type: application/json" \
    -d '{"first_name":"Mary","last_name":"Wang"}'
# Expected: Multiple results (China primary, US secondary)
```

**Typo Tolerance:**
```bash
curl -X POST http://localhost:5050/api/classify \
    -H "Content-Type: application/json" \
    -d '{"first_name":"Wladimir","last_name":"Puttin"}'
# Expected: Russia (via fuzzy matching)
```

---

## Architecture & Design

### File Structure
```
aml-name-origin/
├── Dockerfile                      # Container definition
├── docker-compose.yml              # Multi-container orchestration
├── requirements.txt                # Python dependencies
├── app.py                          # Flask API server
├── name_classifier.py              # Core classification logic
├── evaluate.py                     # Evaluation metrics module
├── test_dataset.json               # Test dataset (120 names)
├── build.sh                        # Docker build script
├── test_api.sh                     # API test suite
├── curl_samples.sh                 # cURL command examples
├── readme.md                       # This file
├── design.md                       # Algorithm design document
├── openapi.yaml                    # OpenAPI 3.0 API specification
├── deployment_summary.md           # Executive deployment summary ⭐
└── architecture_diagram.md         # Visual architecture diagrams
```

### Key Components

**NameOriginClassifier** (name_classifier.py)
- Multi-stage ML pipeline
- N-gram probability models for 10+ countries
- Linguistic pattern matching
- Fuzzy name database lookup
- Confidence scoring

**Flask API** (app.py)
- RESTful endpoints for single & batch classification
- Health checks and statistics
- Request logging
- Error handling

**Docker Setup**
- Lightweight Python 3.9-slim base image
- Health checks enabled
- Port 5050 exposed
- Ready for Kubernetes deployment

---

## Accuracy & Validation

### Performance Targets
- **Top-1 Accuracy:** ≥85% (correct country in first result)
- **Top-3 Accuracy:** ≥92% (correct country in top 3)
- **Confidence Calibration:** ±5% (reported confidence matches actual accuracy)

### Handling Edge Cases

**Multiple Origins:**
- Returns ranked list with confidence scores
- Example: "Smith" → US (0.45), UK (0.40), Canada (0.10)

**Typos & Transliteration:**
- Fuzzy matching with Levenshtein distance ≤2
- Handles Russian (Vladimir/Wladimir) and Arabic (Ahmed/Ahmad) variants

**Multicultural Names:**
- Component-based analysis (first name 30%, last name 70% weight)
- Example: "Mary Wang" → China (0.68), USA (0.20)

---

## Production Deployment Architecture

### 📋 Documentation

For comprehensive deployment architecture in enterprise on-premise environments, see:

- **[OpenAPI Specification](openapi.yaml)** - Complete API contract (OpenAPI 3.0)
- **[Architecture Diagrams](architecture_diagram.md)** - Visual reference with:
  - High-level system architecture
  - Request flow diagrams
  - Scaling architecture
  - Blue-green deployment flow
  - Monitoring & observability flow
  - Security layers

### Key Highlights

**Latency Targets:**
- Single classification: P95 < 15ms, P99 < 30ms
- Batch (100 names): P95 < 150ms

**Scaling:**
- Minimum: 3 replicas (high availability)
- Maximum: 20 replicas (auto-scaling on CPU/memory)
- Per-pod capacity: 100-200 req/s

**Security:**
- TLS 1.3 for data in transit
- AES-256 encryption for PII at rest
- JWT authentication via API Gateway
- Comprehensive audit logging

**Auditability:**
- Every request logged to PostgreSQL
- Explainable decisions (component scores, matched patterns)
- 90-day PII retention
- Compliance reports

---

## Deployment

### Suggestions for Production Deployment

**Kubernetes (Recommended):**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aml-name-classifier
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: classifier
        image: aml-name-classifier:latest
        ports:
        - containerPort: 5050
        livenessProbe:
          httpGet:
            path: /health
            port: 5050
          initialDelaySeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5050
          initialDelaySeconds: 5
```

**Docker Swarm:**
```bash
docker service create \
  --name aml-classifier \
  --replicas 3 \
  -p 5050:5050 \
  aml-name-classifier:latest
```

### Scalability
- Stateless design (each instance independent)
- In-memory models (~50MB RAM per instance)
- ~100-200 names/sec per core
- Easily scales horizontally

---

## Configuration & Customization

### Adding New Countries

1. Add n-gram model to `load_models()` in `name_classifier.py`:
```python
self.ngram_models["NewCountry"] = {
    "bigrams": {"xx": 0.10, "yy": 0.08, ...},
    "trigrams": {"xxx": 0.05, ...}
}
```

2. Add pattern rules:
```python
self.pattern_rules["NewCountry"] = [
    {"suffix": "ski", "score": 0.80},
    {"pattern": "cz", "score": 0.70},
]
```

3. Add training data to `name_database`:
```python
self.name_database[("firstname", "lastname")] = ("NewCountry", 0.95)
```

### Adjusting Confidence Thresholds

In `classify()` method, adjust the 0.70 threshold:
```python
# Current: Include results within 70% of top score
if score >= (top_score * 0.70):
    results.append(...)

# More strict (only very confident results):
if score >= (top_score * 0.85):
    results.append(...)
```

---

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs aml-name-classifier

# Verify port isn't in use
lsof -i :5050

# Rebuild image
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### High latency
- Check system resources: `docker stats`
- Reduce batch size (test with <100 names)
- Increase container CPU allocation

### Low accuracy on specific names
- May be rare/new names - add to training database
- Check for transliteration issues
- Consider manual review for edge cases

---

## Development & Contribution

### Running Tests Locally
```bash
# Install dev dependencies
pip install -r requirements.txt

# Run classifier directly
python name_classifier.py

# Start Flask app
python app.py

# In another terminal
./test_api.sh
```

### Possible Model Improvement
- Add training data from census databases
- Incorporate additional transliteration rules
- Extend pattern rules for underrepresented countries
- Validate accuracy improvements

---

## ⚠️ PoC Limitations & Future Work

### Current Implementation Status

This is a **Proof of Concept** demonstrating the algorithmic approach. Key limitations:

#### 1. Synthetic Training Data
- **N-gram models**: Manually curated probability distributions (NOT trained on real datasets)
- **Name database**: Only ~30 hardcoded examples (production needs 10,000+)
- **Pattern rules**: Hand-crafted linguistic rules (incomplete coverage)

**Production Requirements**: Replace with models trained on:
- Geonames database (2.7M+ names)
- Census data (US Census, UK ONS, Statistics Poland, etc.)
- Wikipedia biography dataset (6M+ entries)

#### 2. Transliteration Approach
- **Current**: Using `unidecode` for all script conversions
- **Limitations**:
  - Cyrillic: Basic transliteration, doesn't follow ISO 9/BGN standards precisely
  - Arabic: Simplified approximation, doesn't capture all romanization variants
  - Chinese: Basic Pinyin, Wade-Giles variants not handled

**PoC Rationale**: `unidecode` provides acceptable coverage for demonstrating the approach without complex dependencies.

**Production Requirements**:
- `transliterate` package for Cyrillic (ISO 9 compliant)
- `pyarabic` or custom Arabic engine (DIN 31635)
- Enhanced Chinese romanization (Pinyin + Wade-Giles + variants)

#### 3. Model Weighting
Current implementation uses:
- 40% N-gram probability models
- 30% Linguistic pattern matching
- 20% Phonetic analysis
- 10% Database lookup
- Component weighting: 70% last name, 30% first name

These weights are heuristic and should be optimized on real validation data.

#### 4. Coverage
- **Countries**: 10 origins/regions (US, UK, Poland, Russia, France, Germany, Spain, Italy, China, Arab)
- **Production needs**: 50+ countries with regional variants

### Validation Results

Run `python evaluate.py` to see current performance on 120-name test set:
- Expected Top-1 accuracy: 75-85% (PoC level with synthetic data)
- Expected Top-3 accuracy: 85-92%
- Production target (with real training data): 85%+ Top-1, 92%+ Top-3

### Before Production Deployment

**Critical Steps**:
1. Replace synthetic n-gram models with trained models from real datasets
2. Expand name database to at least 10,000+ entries
3. Implement proper transliteration libraries (transliterate, pyarabic)
4. Validate on large test set (10,000+ names) with ground truth
5. Optimize model weights using validation data
6. Add comprehensive error handling and logging
7. Implement rate limiting and authentication
8. Set up monitoring and alerting
9. Conduct bias audit and fairness review
10. Get compliance and legal approval

**Compliance Note**: This PoC provides name origin suggestions for AML screening. It should NEVER be used as the sole factor for risk assessment. Always combine with other KYC factors (document verification, source of funds, transaction patterns, etc.).

---
