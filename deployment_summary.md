# AML Name Origin Classifier - Deployment Summary

## Executive Summary

This document provides a high-level overview of the deployment architecture for the AML Name Origin Classifier microservice designed for on-premise enterprise environments.

---

## 1. OpenAPI Contract

### API Specification

**Location:** [`openapi.yaml`](openapi.yaml)

**Standard:** OpenAPI 3.0.3

**Endpoints:**

| Method | Path | Purpose | SLA |
|--------|------|---------|-----|
| `GET` | `/health` | Health check for load balancer | < 1ms P95 |
| `GET` | `/health/ready` | Readiness probe (models loaded) | < 2ms |
| `GET` | `/health/live` | Liveness probe for orchestration | < 2ms |
| `POST` | `/api/classify` | Classify single name | < 15ms P95 |
| `POST` | `/api/batch` | Classify up to 1000 names | < 150ms P95 |
| `GET` | `/api/version` | Get model and API version | < 5ms |
| `GET` | `/api/metrics` | Prometheus metrics export | < 10ms |

**Authentication:**
- Bearer token (JWT) issued by corporate IAM
- API key for service-to-service communication
- No authentication required for health endpoints

**Example Request:**

```bash
curl -X POST https://aml-name-classifier.internal.example.com/v1/api/classify \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Vladimir",
    "last_name": "Putin",
    "request_id": "req-12345-abc"
  }'
```

**Example Response:**

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
  "explanation": "Ensemble classification with database match boost for Russia",
  "method": "ensemble_with_database",
  "request_id": "req-12345-abc",
  "model_version": "2024.12.01",
  "processing_time_ms": 8.5
}
```

---

## 2. Scaling Strategy

### Horizontal Auto-Scaling

**Configuration:**
- **Minimum Replicas:** 3 (high availability)
- **Maximum Replicas:** 20 (capacity limit)
- **Scaling Triggers:**
  - CPU > 70% → scale up
  - Memory > 80% → scale up
  - CPU < 40% for 5 min → scale down

**Capacity Planning:**

```
Per Pod Capacity:
- Single requests: 100-200 req/s
- CPU: 1-2 cores
- Memory: 2-4 GB

Expected Load:
- Average: 5,000 req/s → 10 pods
- Peak: 15,000 req/s → 20 pods
- Off-hours: 3,000 req/s → 6 pods (min 3 for HA)
```

**Multi-Data Center:**
- **DC1 (Primary):** 10 replicas baseline
- **DC2 (Secondary):** 5 replicas baseline
- **Failover:** DNS/GSLB automatic routing
- **RTO:** 15 minutes
- **RPO:** 5 minutes

---

## 3. Quality Monitoring

### Metrics Collection

**Infrastructure:**
- **Prometheus:** Scrapes `/api/metrics` every 15s
- **Grafana:** Real-time dashboards
- **ELK Stack:** Centralized logging
- **Splunk:** SIEM and compliance

### Key Metrics Tracked

**Performance Metrics:**
```
✓ Requests per second (total, by method)
✓ Latency percentiles (P50, P95, P99)
✓ Error rate by type
✓ Pod CPU/Memory usage
```

**Quality Metrics:**
```
✓ Confidence score distribution
✓ Country prediction distribution
✓ Low-confidence prediction rate
✓ Multiple origin detection rate
```

**Business Metrics:**
```
✓ Classification method breakdown
✓ Database hit rate
✓ Batch vs single ratio
✓ Unique names per hour
```

### Alerting Rules

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| **High Error Rate** | > 1% for 2 min | Critical | Immediate investigation |
| **High Latency** | P95 > 50ms for 3 min | Warning | Check resource usage |
| **Low Confidence** | > 30% predictions < 0.5 | Warning | Data science review |
| **Data Drift** | Country distribution shift > 50% | Info | Investigate patterns |
| **Scale Limit** | > 18 pods for 5 min | Warning | Plan capacity increase |

### Quality Dashboard Panels

1. **Request Overview** - Total requests, success rate, latency
2. **Confidence Distribution** - Histogram by confidence bucket
3. **Country Mix** - Pie chart and trends
4. **Model Performance** - Component score contributions
5. **Operational Health** - Pod status, resource usage, errors

---

## 4. Model Versioning & Rollback

### Versioning Strategy

**Version Format:** `vYYYY.MM.DD[.hotfix]`

**Example:**
```
/mnt/models/
├── current -> v2024.12.01              # Symlink to active version
├── v2024.12.01/                        # Latest
│   ├── metadata.json                   # Validation metrics, approval
│   ├── ngram_models.pkl
│   ├── pattern_rules.json
│   ├── name_database.pkl
│   └── checksums.sha256
├── v2024.11.15/                        # Previous (rollback target)
└── v2024.10.30/                        # Archived
```

**Metadata Example:**

```json
{
  "model_version": "2024.12.01",
  "training_date": "2024-11-25",
  "deployment_date": "2024-12-01T10:00:00Z",
  "validation_metrics": {
    "top1_accuracy": 0.87,
    "top3_accuracy": 0.94,
    "mrr": 0.89,
    "ece": 0.04
  },
  "approval": {
    "approved_by": "data-science-team",
    "approved_date": "2024-11-30",
    "reviewer": "john.doe@example.com"
  }
}
```

### Deployment Process (Blue-Green)

**Steps:**

1. **Deploy Green** - New version deployed alongside Blue (0% traffic)
2. **Smoke Tests** - Automated validation of new version
3. **Canary** - 10% traffic to Green, monitor for 15 min
4. **Gradual Increase** - 50% traffic, monitor for 15 min
5. **Full Cutover** - 100% traffic to Green
6. **Standby Period** - Keep Blue for 24h (instant rollback capability)

**Timeline:** ~45 minutes for full deployment (with monitoring)

### Rollback Procedures

**Automated Rollback Triggers:**
- Error rate > 2% for 5 minutes → Immediate rollback
- P95 latency > 100ms for 10 minutes → Immediate rollback
- Pod crash loop (3+ crashes in 10 min) → Immediate rollback

**Manual Rollback:**

```bash
# Instant rollback to previous version
kubectl rollout undo deployment/aml-name-classifier -n aml-prod

# Update model symlink
ssh model-store-server
cd /mnt/models && rm current && ln -s v2024.11.15 current

# Verify rollback
kubectl rollout status deployment/aml-name-classifier -n aml-prod

# Expected rollback time: < 2 minutes
```

---

## 5. Non-Functional Requirements

### 5.1 Latency

**SLA Targets:**

| Operation | P50 | P95 | P99 | Max |
|-----------|-----|-----|-----|-----|
| Single classification | < 5ms | < 15ms | < 30ms | 50ms |
| Batch (100 names) | < 50ms | < 150ms | < 300ms | 500ms |
| Health check | < 1ms | < 2ms | < 5ms | 10ms |

**Latency Breakdown (Single Request):**

```
Total: 5ms
├── API Gateway: 0.5ms
├── Network: 0.3ms
├── Flask routing: 0.2ms
├── Name normalization: 0.5ms
├── N-gram scoring: 1.5ms       (40% weight)
├── Pattern matching: 0.8ms      (30% weight)
├── Phonetic analysis: 1.0ms     (20% weight)
├── Database lookup: 0.5ms       (10% weight)
├── Aggregation: 0.3ms
└── Serialization: 0.4ms
```

**Optimization Strategies:**
- Optional Redis caching (20-30% hit rate → 3-4ms savings)
- Connection pooling for database
- Pre-loaded models on pod startup
- Warm-up procedures for new pods

### 5.2 Security

**Encryption:**

| Component | Method | Key Management |
|-----------|--------|----------------|
| **Data in Transit** | TLS 1.3 (min TLS 1.2) | Corporate PKI |
| **Data at Rest (DB)** | AES-256 | HashiCorp Vault |
| **API Traffic** | mTLS (optional) | Service mesh |
| **Logs (PII)** | Field-level encryption | Vault transit engine |

**Authentication Flow:**

```
Client
  │ 1. Obtain JWT from Corporate IAM
  ├──► IAM: Issues JWT (signed RS256, 1h TTL)
  │
  │ 2. API Request with JWT
  ├──► API Gateway
       │ 3. Validate JWT signature
       │ 4. Check expiration
       │ 5. Verify scope: "aml:classify:read"
       │ 6. Rate limit by user_id (1000 req/min)
       │
       ├──► AML Classifier Service
            │ 7. Process request (no auth logic)
            │ 8. Log user context from JWT
            │
            ├──► PostgreSQL (Audit Log)
                 │ 9. Store encrypted PII
                 │ 10. Retention: 90 days
```

**PII Handling:**

| Data | Classification | Retention | Encryption |
|------|---------------|-----------|------------|
| First Name | PII - High | 90 days | At rest + transit |
| Last Name | PII - High | 90 days | At rest + transit |
| Classification Result | Non-PII | 365 days | Transit only |
| Confidence Score | Non-PII | 365 days | Transit only |

**Access Control (RBAC):**

| Role | Permissions |
|------|-------------|
| `aml-analyst` | Read classifications, view audit logs |
| `aml-admin` | All analyst + manage API keys |
| `data-scientist` | Read metrics, trigger model updates |
| `infra-admin` | Deploy services, manage infrastructure |
| `audit-viewer` | Read-only audit database access |

### 5.3 Auditability

**Request-Level Audit (PostgreSQL):**

Every classification request stored with:
- Encrypted PII (first_name, last_name)
- Prediction results (countries, confidence)
- User context (user_id, client_id, source_ip)
- Model details (version, method, component scores)
- Performance metrics (processing_time_ms)
- Request tracking (request_id, timestamp)

**Decision Explainability:**

```json
{
  "explainability": {
    "method": "ensemble_with_database",
    "component_scores": {
      "last_name": {
        "ngram": 0.45,
        "pattern": 0.32,
        "phonetic": 0.18,
        "database": 0.10
      },
      "first_name": {
        "ngram": 0.38,
        "pattern": 0.28,
        "phonetic": 0.15,
        "database": 0.05
      }
    },
    "matched_patterns": [
      {
        "country": "Russia",
        "pattern": "suffix:-in",
        "score": 0.80
      }
    ],
    "database_match": {
      "matched": true,
      "similarity": 1.00,
      "entry": "vladimir putin"
    },
    "reasoning": "Strong pattern match on Russian suffix '-in'. Database exact match. High phonetic similarity to Russian phonetic profile."
  }
}
```

**Audit Query Examples:**

```sql
-- Find all classifications for specific user
SELECT timestamp, request_id,
       pgp_sym_decrypt(first_name_encrypted, 'key') as first_name,
       predicted_countries, confidence_score
FROM classification_audit
WHERE user_id = 'analyst-john-doe'
  AND timestamp >= NOW() - INTERVAL '7 days'
ORDER BY timestamp DESC;

-- Identify low-confidence predictions for review
SELECT DATE_TRUNC('hour', timestamp) as hour,
       COUNT(*) as total,
       COUNT(*) FILTER (WHERE confidence_score < 0.5) as low_confidence,
       AVG(confidence_score) as avg_confidence
FROM classification_audit
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY hour;

-- Complete audit trail for specific decision
SELECT ca.*, mda.model_version, mda.validation_top1_accuracy,
       mda.deployed_by, mda.deployment_timestamp
FROM classification_audit ca
LEFT JOIN model_deployment_audit mda 
  ON ca.model_version = mda.model_version
WHERE ca.request_id = 'req-abc-123';
```

**Compliance Reports:**

Monthly automated reports include:
- Usage statistics (total classifications, users, success rate)
- Model performance (version, latency, no rollbacks)
- Quality metrics (confidence distribution)
- Security events (auth failures, rate limits)
- Data protection compliance (encryption, retention)
- Changes and deployments (approvals, validation metrics)

---

## 6. Operational Procedures

### Daily Health Check

```bash
#!/bin/bash
# Automated daily health check

# 1. Service health
curl -s https://aml-classifier.internal/v1/health | jq .

# 2. Pod status
kubectl get pods -n aml-prod -l app=aml-name-classifier

# 3. Resource usage
kubectl top pods -n aml-prod -l app=aml-name-classifier

# 4. Error rate (last 24h)
curl -s 'http://prometheus:9090/api/v1/query' \
  --data-urlencode 'query=rate(aml_classifier_requests_total{status="error"}[24h])'

# 5. Model version
curl -s https://aml-classifier.internal/v1/api/version | jq .model_version
```

### Incident Response

**Scenario 1: High Latency (P95 > 50ms)**

```
1. Check Grafana dashboard → Identify spike
2. Investigate:
   - Database slow queries?
   - CPU/Memory pressure?
   - Network issues?
3. Mitigate:
   - Scale up: kubectl scale deployment aml-name-classifier --replicas=15
   - Enable caching if not already active
4. Monitor for 15 minutes
5. Document root cause and update capacity planning
```

**Scenario 2: Model Quality Degradation**

```
1. Identify: Grafana alert or manual report
2. Gather data: Export recent predictions, check patterns
3. Decision:
   - Data quality issue → Work with upstream
   - Model issue → Prepare rollback
   - Expected behavior → Document and monitor
4. Rollback if needed:
   - kubectl rollout undo deployment/aml-name-classifier
   - Verify metrics return to normal
5. Root cause analysis and improvement plan
```

### Disaster Recovery

**RTO:** 15 minutes  
**RPO:** 5 minutes

**Procedure:**

1. **Automatic Failover** (DC1 → DC2): < 5 minutes
2. **Restore from Backup** (both DCs down): 10-15 minutes
   - Deploy fresh Kubernetes cluster
   - Restore model artifacts from NFS backup
   - Restore PostgreSQL from daily backup
   - Deploy service: `kubectl apply -f deployment.yaml`
3. **Validation**
   - Run smoke tests
   - Verify model version
   - Check audit log continuity
4. **Communication**
   - Notify AML team
   - Document incident

---

## Summary

This AML Name Origin Classifier microservice is designed for conservative enterprise environments with:

**Production-Ready API** - OpenAPI 3.0 contract, comprehensive error handling  
**Horizontal Scaling** - 3 to 20+ pods auto-scaling based on load  
**Quality Monitoring** - Real-time dashboards, alerts, data drift detection  
**Model Governance** - Versioning, blue-green deployment, instant rollback  
**Low Latency** - < 15ms P95 for single requests  
**Enterprise Security** - TLS 1.3, PII encryption, JWT authentication  
**Full Auditability** - Every request logged, explainable decisions, compliance reports  
**Operational Excellence** - Health checks, incident playbooks, disaster recovery  


