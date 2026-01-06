# AML Name Origin Classifier - Architecture Diagrams

## Visual Architecture Reference

This document contains visual representations of the deployment architecture for the AML Name Origin Classifier PoC.

---

## 1. High-Level System Architecture

```
                                Internet (Limited/Blocked)
                                        │
                                        │ (No external dependencies)
                                        │
═══════════════════════════════════════════════════════════════════════
                            Enterprise DMZ / Internal Network
═══════════════════════════════════════════════════════════════════════
                                        │
                              ┌─────────▼──────────┐
                              │   Corporate IAM    │
                              │  (OAuth 2.0 / JWT) │
                              └─────────┬──────────┘
                                        │ Tokens
        ┌───────────────────────────────┼───────────────────────────────┐
        │                               │                               │
        │                               │                               │
┌───────▼────────┐             ┌────────▼────────┐             ┌────────▼───────┐
│  AML Screening │             │   Investigation │             │  Batch Import  │
│    Portal      │             │      Tool       │             │     Service    │
│  (Web UI)      │             │   (Desktop)     │             │   (Backend)    │
└───────┬────────┘             └────────┬────────┘             └────────┬───────┘
        │                               │                               │
        │                               │                               │
        └───────────────────────────────┼───────────────────────────────┘
                                        │ HTTPS + JWT
                              ┌─────────▼──────────┐
                              │   F5 Load Balancer │
                              │   (L4/L7 routing)  │
                              │  - SSL Termination │
                              │  - Health Checks   │
                              └─────────┬──────────┘
                                        │
                              ┌─────────▼──────────┐
                              │   API Gateway      │
                              │   (Kong / Apigee)  │
                              │                    │
                              │  • Auth validation │
                              │  • Rate limiting   │
                              │  • Request logging │
                              │  • Circuit breaker │
                              └─────────┬──────────┘
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        │                               │                               │
        │            Kubernetes / OpenShift Cluster                     │
        │                                                               │
        │  ┌────────────────────────────────────────────────────────┐   │
        │  │  AML Name Classifier Service (Namespace: aml-prod)     │   │
        │  │                                                        │   │
        │  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐      │   │
        │  │  │ Pod1 │  │ Pod2 │  │ Pod3 │  │ ...  │  │ PodN │      │   │
        │  │  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘      │   │
        │  │     │         │         │         │         │          │   │
        │  │     │  Each pod contains:                              │   │
        │  │     │  - Flask API (Python)                            │   │
        │  │     │  - ML Models (loaded in memory)                  │   │
        │  │     │  - Metrics exporter                              │   │
        │  │     │                                                  │   │
        │  │  Horizontal Pod Autoscaler (HPA)                       │   │
        │  │  Min: 3, Max: 20, Target: 70% CPU / 80% Memory         │   │
        │  └────────────────────────────────────────────────────────┘   │
        │                                                               │
        │  ┌────────────────────────────────────────────────────────┐   │
        │  │             Supporting Services                        │   │
        │  │                                                        │   │
        │  │  ┌────────────┐  ┌────────────┐  ┌────────────┐        │   │
        │  │  │ PostgreSQL │  │   Redis    │  │ Prometheus │        │   │
        │  │  │ (Audit DB) │  │  (Cache)   │  │ (Metrics)  │        │   │
        │  │  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘        │   │
        │  │         │               │               │              │   │
        │  │  ┌────────────┐  ┌────────────┐  ┌────────────┐        │   │
        │  │  │  Grafana   │  │ ELK Stack  │  │   Splunk   │        │   │
        │  │  │(Dashboard) │  │   (Logs)   │  │   (SIEM)   │        │   │
        │  │  └────────────┘  └────────────┘  └────────────┘        │   │
        │  └────────────────────────────────────────────────────────┘   │
        └───────────────────────────────────────────────────────────────┘
                                        │
                              ┌─────────▼──────────┐
                              │   Model Store      │
                              │   (NFS / MinIO)    │
                              │                    │
                              │   /models/         │
                              │   ├── current @    │
                              │   ├── v2024.12.01/ │
                              │   └── v2024.11.15/ │
                              └────────────────────┘
```

---

## 2. Request Flow Diagram

```
┌────────────┐
│   Client   │
│  (AML App) │
└──────┬─────┘
       │ 1. POST /api/classify
       │    Authorization: Bearer <JWT>
       │    Body: {"first_name": "Vladimir", "last_name": "Putin"}
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│                       Load Balancer                              │
│  • Health check: GET /health (every 10s)                         │
│  • Route to healthy pods only                                    │
└──────┬───────────────────────────────────────────────────────────┘
       │ 2. Forward to API Gateway
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│                       API Gateway                                │
│  Step 1: Validate JWT                                            │
│    - Check signature                                             │
│    - Check expiration                                            │
│    - Extract user_id, client_id                                  │
│  Step 2: Rate Limiting                                           │
│    - Check: client_id has < 1000 req/min                         │
│  Step 3: Audit Log                                               │
│    - Log: timestamp, user_id, endpoint, source_ip                │
│  Step 4: Forward                                                 │
└──────┬───────────────────────────────────────────────────────────┘
       │ 3. Route to Service
       │    X-User-ID: analyst-john-doe
       │    X-Client-ID: aml-prod-001
       │    X-Request-ID: req-abc-123
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│              Kubernetes Service (ClusterIP)                      │
│  • Load balance across healthy pods (round-robin)                │
└──────┬───────────────────────────────────────────────────────────┘
       │ 4. Forward to Pod
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Classifier Pod                               │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Flask Application                                         │  │
│  │                                                            │  │
│  │  1. Receive request (5-10ms total processing)              │  │
│  │     ├─ Parse JSON (0.2ms)                                  │  │
│  │     ├─ Normalize names (0.5ms)                             │  │
│  │     │   • Unidecode transliteration                        │  │
│  │     │   • Lowercase                                        │  │
│  │     │   • Remove special chars                             │  │
│  │     │                                                      │  │
│  │  2. Check cache (optional) (0.5ms)                         │  │
│  │     └─ Redis: key = sha256(first+last)                     │  │
│  │                                                            │  │
│  │  3. Ensemble Classification (4ms)                          │  │
│  │     ├─ N-gram scoring (1.5ms) - 40% weight                 │  │
│  │     │   • Extract bigrams/trigrams                         │  │
│  │     │   • Score against 10 country models                  │  │
│  │     │                                                      │  │
│  │     ├─ Pattern matching (0.8ms) - 30% weight               │  │
│  │     │   • Check suffixes: -ski, -ov, -ez, etc.             │  │
│  │     │   • Check prefixes: Al-, El-                         │  │
│  │     │                                                      │  │
│  │     ├─ Phonetic analysis (1.0ms) - 20% weight              │  │
│  │     │   • Vowel ratio                                      │  │
│  │     │   • Double consonants                                │  │
│  │     │   • Consonant clusters                               │  │
│  │     │                                                      │  │
│  │     └─ Database lookup (0.5ms) - 10% weight                │  │
│  │         • Fuzzy match against known names                  │  │
│  │                                                            │  │
│  │  4. Aggregate scores (0.3ms)                               │  │
│  │     • Weight: Last name 70%, First name 30%                │  │
│  │     • Rank countries by score                              │  │
│  │     • Filter: Include results within 70% of top score      │  │
│  │                                                            │  │
│  │  5. Generate response (0.4ms)                              │  │
│  │     • JSON serialization                                   │  │
│  │     • Add metadata (model_version, processing_time)        │  │
│  │                                                            │  │
│  │  6. Emit metrics (async, non-blocking)                     │  │
│  │     • Increment request counter                            │  │
│  │     • Record latency histogram                             │  │
│  │     • Track confidence distribution                        │  │
│  │     • Update country prediction counts                     │  │
│  │                                                            │  │
│  │  7. Store audit record (async, non-blocking)               │  │
│  │     • Encrypt PII fields                                   │  │
│  │     • Insert to PostgreSQL                                 │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Response:                                                 │  │
│  │  {                                                         │  │
│  │    "success": true,                                        │  │
│  │    "results": [["Russia", 0.98]],                          │  │
│  │    "confidence": 0.98,                                     │  │
│  │    "model_version": "2024.12.01",                          │  │
│  │    "request_id": "req-abc-123",                            │  │
│  │    "processing_time_ms": 8.5                               │  │
│  │  }                                                         │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────┬───────────────────────────────────────────────────────────┘
       │ 5. Return response
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│                    API Gateway                                   │
│  • Log response (status, latency)                                │
│  • Return to client                                              │
└──────┬───────────────────────────────────────────────────────────┘
       │ 6. HTTPS Response
       │    Status: 200 OK
       │    X-Request-ID: req-abc-123
       │    X-Model-Version: 2024.12.01
       │
       ▼
┌────────────┐
│   Client   │
│  (AML App) │
└────────────┘
```

---

## 3. Scaling Architecture

```
                            Normal Load (5,000 req/s)
                            ═══════════════════════════
                                      │
                            ┌─────────▼─────────┐
                            │  Load Balancer    │
                            │  5,000 req/s      │
                            └─────────┬─────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            │                         │                         │
    ┌───────▼────────┐        ┌──────▼──────┐        ┌────────▼───────┐
    │   Pod 1        │        │   Pod 2     │        │   Pod 3        │
    │   CPU: 45%     │        │   CPU: 50%  │        │   CPU: 48%     │
    │   500 req/s    │        │   500 req/s │        │   500 req/s    │
    └────────────────┘        └─────────────┘        └────────────────┘
    
                       ... 7 more pods (10 total) ...
                       
    Each pod: ~500 req/s → Total capacity: 5,000 req/s
    CPU usage: ~45-50% (healthy, below 70% threshold)
    

                            Peak Load (15,000 req/s)
                            ══════════════════════════
                                      │
                                      │ HPA detects CPU > 70%
                                      │ Scales up to 20 pods
                                      │
                            ┌─────────▼─────────┐
                            │  Load Balancer    │
                            │  15,000 req/s     │
                            └─────────┬─────────┘
                                      │
            ┌─────────────────────────┼────────────────────────┐
            │                         │                        │
    ┌───────▼────────┐         ┌──────▼──────┐        ┌────────▼───────┐
    │   Pod 1        │         │   Pod 2     │        │   Pod 3        │
    │   CPU: 70%     │         │   CPU: 68%  │        │   CPU: 72%     │
    │   750 req/s    │         │   750 req/s │        │   750 req/s    │
    └────────────────┘         └─────────────┘        └────────────────┘
    
                      ... 17 more pods (20 total) ...
                      
    Each pod: ~750 req/s → Total capacity: 15,000 req/s
    CPU usage: ~70% (at scaling threshold)
    

                         Scale-Down (Load drops to 3,000 req/s)
                         ═══════════════════════════════════════
                                      │
                                      │ HPA waits 5 min stabilization
                                      │ CPU < 40% sustained
                                      │ Scales down to 6 pods
                                      │
                            ┌─────────▼─────────┐
                            │  Load Balancer    │
                            │  3,000 req/s      │
                            └─────────┬─────────┘
                                      │
            ┌─────────────────────────┼────────────────────────┐
            │                         │                        │
    ┌───────▼────────┐         ┌──────▼──────┐        ┌────────▼───────┐
    │   Pod 1        │         │   Pod 2     │        │   Pod 3        │
    │   CPU: 55%     │         │   CPU: 52%  │        │   CPU: 58%     │
    │   500 req/s    │         │   500 req/s │        │   500 req/s    │
    └────────────────┘         └─────────────┘        └────────────────┘
    
                       ... 3 more pods (6 total) ...
                       
    Minimum replicas: 3 (never scales below for HA)
    Each pod: ~500 req/s → Total capacity: 3,000 req/s
    CPU usage: ~55% (healthy operating range)
```

---

## 4. Model Deployment Flow (Blue-Green)

```
                       Initial State: Blue (v2024.11.15)
                       ═════════════════════════════════
                                      │
                            ┌─────────▼─────────┐
                            │  Load Balancer    │
                            │   100% → Blue     │
                            └─────────┬─────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────┐
                    │   Blue Environment (v2024.11)   │
                    │   ┌──────┐ ┌──────┐ ┌──────┐    │
                    │   │ Pod1 │ │ Pod2 │ │ Pod3 │    │
                    │   └──────┘ └──────┘ └──────┘    │
                    │   10 pods serving traffic       │
                    └─────────────────────────────────┘


              Step 1: Deploy Green (v2024.12.01) - 0% traffic
              ═══════════════════════════════════════════════
                                      │
                            ┌─────────▼─────────┐
                            │  Load Balancer    │
                            │   100% → Blue     │
                            │     0% → Green    │
                            └──────┬────────┬───┘
                                   │        │
                      ┌────────────┘        └────────────┐
                      ▼                                  ▼
    ┌────────────────────────────┐      ┌────────────────────────────┐
    │  Blue (v2024.11)           │      │  Green (v2024.12) - NEW    │
    │  ┌──────┐ ┌──────┐         │      │  ┌──────┐ ┌──────┐         │
    │  │ Pod1 │ │ Pod2 │  ...    │      │  │ Pod1 │ │ Pod2 │  ...    │
    │  └──────┘ └──────┘         │      │  └──────┘ └──────┘         │
    │  10 pods (serving)         │      │  10 pods (standby)         │
    └────────────────────────────┘      └────────────────────────────┘
                                         • Warm-up complete
                                         • Health checks pass
                                         • Ready for traffic


              Step 2: Canary Testing - 10% traffic to Green
              ═════════════════════════════════════════════
                                      │
                            ┌─────────▼─────────┐
                            │  Load Balancer    │
                            │    90% → Blue     │
                            │    10% → Green    │
                            └──────┬────────┬───┘
                                   │        │
                      ┌────────────┘        └────────────┐
                      ▼                                  ▼
    ┌────────────────────────────┐      ┌────────────────────────────┐
    │  Blue (v2024.11)           │      │  Green (v2024.12)          │
    │  90% traffic               │      │  10% traffic (CANARY)      │
    │  10 pods                   │      │  10 pods                   │
    └────────────────────────────┘      └────────────────────────────┘
                                         Monitor for 15 minutes:
                                         • Error rate
                                         • Latency P95
                                         • Confidence distribution


              Step 3: Increase to 50% - If canary successful
              ══════════════════════════════════════════════
                                      │
                            ┌─────────▼─────────┐
                            │  Load Balancer    │
                            │    50% → Blue     │
                            │    50% → Green    │
                            └──────┬────────┬───┘
                                   │        │
                      ┌────────────┘        └────────────┐
                      ▼                                  ▼
    ┌────────────────────────────┐      ┌────────────────────────────┐
    │  Blue (v2024.11)           │      │  Green (v2024.12)          │
    │  50% traffic               │      │  50% traffic               │
    │  10 pods                   │      │  10 pods                   │
    └────────────────────────────┘      └────────────────────────────┘
                                         Monitor for 15 minutes


              Step 4: Full Cutover - 100% to Green
              ════════════════════════════════════
                                      │
                            ┌─────────▼─────────┐
                            │  Load Balancer    │
                            │     0% → Blue     │
                            │   100% → Green    │
                            └──────┬────────┬───┘
                                   │        │
                      ┌────────────┘        └────────────┐
                      ▼                                  ▼
    ┌────────────────────────────┐      ┌────────────────────────────┐
    │  Blue (v2024.11)           │      │  Green (v2024.12)          │
    │  0% traffic (STANDBY)      │      │  100% traffic              │
    │  10 pods (kept 24h)        │      │  10 pods                   │
    └────────────────────────────┘      └────────────────────────────┘
                                         Keep Blue for 24h as
                                         instant rollback target


              Step 5: Rollback (if issues detected)
              ════════════════════════════════════
                                      │
                            ┌─────────▼─────────┐
                            │  Load Balancer    │
                            │   100% → Blue     │  ← Instant switch
                            │     0% → Green    │
                            └──────┬────────┬───┘
                                   │        │
                      ┌────────────┘        └────────────┐
                      ▼                                  ▼
    ┌────────────────────────────┐      ┌────────────────────────────┐
    │  Blue (v2024.11)           │      │  Green (v2024.12)          │
    │  100% traffic (RESTORED)   │      │  0% traffic (ROLLED BACK)  │
    │  10 pods                   │      │  Being decommissioned      │
    └────────────────────────────┘      └────────────────────────────┘
                                         Rollback time: < 2 minutes
                                         No downtime
```

---

## 5. Monitoring & Observability Flow

```
┌────────────────────────────────────────────────────────────────┐
│                  AML Classifier Pods (10+)                     │
│                                                                │
│  Each pod emits:                                               │
│  • Metrics (Prometheus format on /api/metrics)                 │
│  • Logs (JSON to stdout/stderr)                                │
│  • Traces (optional - OpenTelemetry)                           │
│  • Audit records (to PostgreSQL)                               │
└───┬─────────────┬─────────────┬─────────────┬──────────────────┘
    │             │             │             │
    │ Metrics     │ Logs        │ Traces      │ Audit
    │             │             │             │
    ▼             ▼             ▼             ▼
┌──────────┐   ┌─────────┐   ┌──────────┐   ┌─────────────┐
│Prometheus│   │  ELK    │   │  Jaeger  │   │ PostgreSQL  │
│          │   │  Stack  │   │(optional)│   │  (Audit DB) │
│• Scrape  │   │         │   │          │   │             │
│  /metrics│   │• Parse  │   │• Span    │   │• Encrypted  │
│  every   │   │  JSON   │   │  collect │   │  PII        │
│  15s     │   │  logs   │   │          │   │• Partitioned│
│          │   │• Index  │   │          │   │  by month   │
│• Store   │   │  in ES  │   │          │   │             │
│  15d     │   │         │   │          │   │             │
└────┬─────┘   └────┬────┘   └────┬─────┘   └──────┬──────┘
     │              │             │                │
     └──────┬───────┴──────┬──────┴────────────────┘
            │              │
            ▼              ▼
     ┌─────────────┐   ┌────────────┐
     │ Grafana     │   │  Splunk    │
     │             │   │  (SIEM)    │
     │• Dashboards │   │  • Security│
     │• Alerts     │   │    alerts  │
     │• Panels     │   │• Audit     │
     │             │   │   review   │
     └─────────────┘   └────────────┘
            │
            │ Alerts
            ▼
     ┌──────────────────┐
     │  PagerDuty /     │
     │  Slack / Email   │
     │                  │
     │  On-call team    │
     │  notified        │
     └──────────────────┘


Grafana Dashboard Panels Proposition:
══════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│  AML Name Classifier - Operations Dashboard                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │  Requests/sec   │  │   Success Rate  │  │  P95 Latency│  │
│  │      5,247      │  │     99.97%      │  │    12.3ms   │  │
│  │  ▲ Trending up  │  │   ✓ Healthy     │  │ ✓ < 15ms    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Request Latency (P50, P95, P99)                     │   │
│  │  ╭─────────────────────────────────────────────────╮ │   │
│  │  │              P99 (28ms)                         │ │   │
│  │  │           P95 (12ms)                            │ │   │
│  │  │       P50 (4.5ms)                               │ │   │
│  │  ╰─────────────────────────────────────────────────╯ │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Confidence Score Distribution                       │   │
│  │  ╔════════════════════════════════════════════════╗  │   │
│  │  ║ 0.9-1.0  ████████████████████████ 45.2%        ║  │   │
│  │  ║ 0.7-0.9  ██████████████████████ 42.8%          ║  │   │
│  │  ║ 0.5-0.7  ████████ 9.0%                         ║  │   │
│  │  ║ 0.3-0.5  ██ 2.5%                               ║  │   │
│  │  ║ 0.0-0.3  █ 0.5%                                ║  │   │
│  │  ╚════════════════════════════════════════════════╝  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Top Countries (Last 24h)                            │   │
│  │                                                      │   │
│  │   US         ████████████████████████ 25.3%          │   │
│  │   UK         ██████████████████ 18.7%                │   │
│  │   Poland     ███████████ 12.1%                       │   │
│  │   Russia     █████████ 9.8%                          │   │
│  │   China      ████████ 8.5%                           │   │
│  │   Germany    ██████ 6.2%                             │   │
│  │   France     █████ 5.4%                              │   │
│  │   Spain      ████ 4.8%                               │   │
│  │   Italy      ███ 3.6%                                │   │
│  │   Arab       ███ 3.2%                                │   │
│  │   Other      ██ 2.4%                                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐    │
│  │ Active Pods   │  │  CPU Usage    │  │ Memory Usage  │    │
│  │      10       │  │     55%       │  │     62%       │    │
│  │  (min: 3)     │  │  (target:70%) │  │ (target: 80%) │    │
│  └───────────────┘  └───────────────┘  └───────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Security Layers                              │
└─────────────────────────────────────────────────────────────────┘

Layer 1: Network Security
═════════════════════════

    Internet
       ║
       ║ (Blocked / Firewall)
       ║
    ═══════════════════════════════════════
       Corporate Network Perimeter
    ═══════════════════════════════════════
       │
       │ • VPN required
       │ • IP whitelist
       │
    ┌──▼─────────────────────────────┐
    │  Internal Network (VLAN)       │
    │  • Segmented                   │
    │  • No internet egress          │
    └──┬─────────────────────────────┘
       │
       └─► AML Services Zone


Layer 2: Authentication & Authorization
═══════════════════════════════════════

    ┌──────────────────────┐
    │  Corporate IAM       │
    │  (AD / OAuth 2.0)    │
    └──────┬───────────────┘
           │ Issues JWT
           ▼
    ┌─────────────────────────────────────┐
    │  JWT Token                          │
    │  {                                  │
    │    "sub": "aml-service",            │
    │    "scope": "aml:classify:read",    │
    │    "user_id": "john.doe",           │
    │    "exp": 1704550800                │
    │  }                                  │
    │  Signed with RS256                  │
    └──────┬──────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────┐
    │  API Gateway                        │
    │  • Validates signature              │
    │  • Checks expiration                │
    │  • Verifies scope                   │
    │  • Rate limits by user_id           │
    └──────┬──────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────┐
    │  AML Classifier Service             │
    │  • No auth logic                    │
    │  • Trusts API Gateway               │
    │  • Logs user context                │
    └─────────────────────────────────────┘


Layer 3: Encryption
═══════════════════

    Data in Transit:
    ───────────────
    Client ──[TLS 1.3]──► Load Balancer
                           │
    Load Balancer ──[TLS 1.2+]──► API Gateway
                                    │
    API Gateway ──[mTLS (optional)]──► Kubernetes Service
                                         │
    Kubernetes Service ──[HTTP]──► Pods (internal network)
                                    │
    Pods ──[TLS 1.2+]──► PostgreSQL (audit DB)


    Data at Rest:
    ────────────
    ┌─────────────────────────────────────┐
    │  PostgreSQL Database                │
    │                                     │
    │  Table: classification_audit        │
    │  ┌───────────────────────────────┐  │
    │  │ first_name_encrypted (BYTEA)  │  │ ◄── AES-256 encrypted
    │  │ last_name_encrypted (BYTEA)   │  │ ◄── AES-256 encrypted
    │  │ predicted_countries (JSONB)   │  │ ◄── Not encrypted (not PII)
    │  │ confidence_score (NUMERIC)    │  │ ◄── Not encrypted
    │  └───────────────────────────────┘  │
    │                                     │
    │  Encryption keys stored in:         │
    │  ┌───────────────────────────────┐  │
    │  │  HashiCorp Vault              │  │
    │  │  - Key rotation every 90 days │  │
    │  │  - Audit log of key access    │  │
    │  └───────────────────────────────┘  │
    └─────────────────────────────────────┘


Layer 4: Secrets Management
═══════════════════════════

    ┌──────────────────────────────────────┐
    │  HashiCorp Vault / Kubernetes Secrets│
    │                                      │
    │  Secrets stored:                     │
    │  • Database credentials              │
    │  • API keys (for internal services)  │
    │  • Encryption keys                   │
    │  • TLS certificates                  │
    └──────┬───────────────────────────────┘
           │ Injected at runtime
           ▼
    ┌───────────────────────────────────────┐
    │  Pod Environment Variables            │
    │  (Never in container image)           │
    │                                       │
    │  DATABASE_URL=postgresql://...        │
    │  (from secret: aml-classifier-secrets)│
    └───────────────────────────────────────┘
```

---

This architecture ensures:
- **High availability** through multi-pod deployment and auto-scaling
- **Low latency** with optimized code paths and optional caching  
- **Security** via multiple layers (network, auth, encryption)
- **Auditability** with comprehensive logging and explainability
- **Operability** with health checks, metrics, and blue-green deployments
- **Scalability** from 3 to 20+ pods based on demand

