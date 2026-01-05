# AML Name-to-Country Origin Matching System

## Design Document

---

## 1. Data Sources

### Primary Data Sources

**A. Name Databases**
- **Geonames Database** (publicly available): Contains ~2.7M place names and person names across multiple countries
- **Social Media Datasets**: LinkedIn, Twitter profiles with location/country information
- **Census Data**: US Census Bureau, UK ONS, Statistics Poland provide name frequency by country
- **UN Name Database**: Curated names from official UN documents
- **Custom Curated Datasets**: 
  - English-origin names (Anglo-Saxon, Celtic prefixes/suffixes)
  - German-origin names (endings: -mann, -meyer, -schmidt, -meyer)
  - Polish-origin names (endings: -ski, -ska, -czyk, -owski)
  - Russian-origin names (endings: -ov, -ova, -enko, -ev, -evich)
  - Arabic-origin names (patterns: Al-, El-, prefixes/suffixes)
  - Spanish-origin names (endings: -ez, -oz, -az)
  - Italian-origin names (endings: -ini, -etti, -ucci)

**B. Transliteration Mappings**
- **Unicode CLDR** (Common Locale Data Repository): Standard transliteration rules
- **ISO 9 (Russian to Latin)**: For Cyrillic names
- **DIN 31635 (Arabic to Latin)**: For Arabic names
- **Pinyin (Chinese to Latin)**: For Chinese names

### Data Quality

The system must handle:
- Spelling variations (Smith, Smyth, Smythe)
- Transliteration variants (Vladimir, Wladimir; Ahmed, Ahmad, Ahmad)
- Phonetic variations (Phillip, Phillip, Philip)

---

## 2. Algorithmic Approach

### Architecture Overview

**Multi-stage Pipeline:**

```
Input Name (First + Last)
    ↓
[Stage 1] Data Normalization
    - Unicode normalization (NFC/NFD)
    - Remove accents/diacritics
    - Transliteration normalization
    - Lowercase conversion
    ↓
[Stage 2] Character & Linguistic Feature Extraction
    - N-gram analysis (2-grams, 3-grams, 4-grams)
    - Phonetic patterns (n-gram frequency per country)
    - Linguistic patterns (prefixes, suffixes, vowel patterns)
    - Script detection (Cyrillic, Arabic, Latin)
    ↓
[Stage 3] Multi-Model Classification
    - Model A: N-gram probability model
    - Model B: Linguistic pattern matching
    - Model C: Phonetic similarity model
    - Model D: Database lookup (exact/fuzzy match)
    ↓
[Stage 4] Score Aggregation & Confidence
    - Weighted ensemble of models
    - Confidence scoring
    - Ambiguity detection
    ↓
Output: Ranked list of countries with confidence scores
```

### Stage 1: Normalization

```python
def normalize_name(name):
    # Remove diacritics (é → e, ø → o)
    name = unidecode(name)
    
    # Transliteration normalization
    if contains_cyrillic(name):
        name = transliterate_cyrillic_to_latin(name)
    if contains_arabic(name):
        name = transliterate_arabic_to_latin(name)
    
    # Lowercase
    name = name.lower()
    
    # Remove special characters
    name = re.sub(r'[^a-z\s]', '', name)
    
    return name.strip()
```

### Stage 2: Feature Extraction

**N-gram Model** (most effective):
- Extract character n-grams from the name
- Calculate n-gram frequency distribution for each country
- Example: "smith" → ["sm", "mi", "it", "th"] (2-grams)

**Training Data**: Build per-country n-gram models from databases
```
English model: {"th": 0.15, "er": 0.12, "in": 0.10, "ed": 0.09, ...}
Polish model:  {"sk": 0.18, "cz": 0.14, "wi": 0.11, "ow": 0.10, ...}
Russian model: {"ov": 0.16, "en": 0.12, "uk": 0.10, "ev": 0.09, ...}
```

**Linguistic Pattern Matching**:
- Rule-based suffix/prefix detection
- Example rules:
  - Suffix "-ski"/"-ska" → Poland (confidence: 0.85)
  - Suffix "-ov"/"-ova"/"-enko" → Russia (confidence: 0.80)
  - Prefix "Al-"/"El-" + Arabic patterns → Middle East (confidence: 0.70)
  - Suffix "-ez"/"-oz" → Spain/Latin America (confidence: 0.75)

**Phonetic Patterns**:
- Consonant-vowel sequences
- Double consonants (common in Slavic languages)
- Vowel patterns (a,e,i,o,u frequency)

### Stage 3: Probabilistic Scoring

For each country, calculate score using Naive Bayes:

```
P(Country | name_features) ∝ P(features | Country) × P(Country)

Where:
P(features | Country) = Π P(n-gram_i | Country)
P(Country) = prior probability from training data

Example:
P(Poland | "Wilkowski") = P("wi"|Poland) × P("il"|Poland) × 
                          P("lk"|Poland) × P("ko"|Poland) × 
                          P(Poland) × BONUS_SUFFIX("-ski")
```

### Stage 4: Ensemble & Confidence

```
Final_Score(Country) = 
    0.40 × NgramScore(Country) +
    0.30 × PatternScore(Country) +
    0.20 × PhoneticScore(Country) +
    0.10 × DatabaseLookupScore(Country)

Confidence = max(Final_Score) / sum(all_scores)
```

---

## 3. Handling Complex Scenarios

### A. Multiple Possible Countries

**Strategy: Probability Distribution**

For names like "John Smith" (common in multiple English-speaking countries):
- Return ranked list: [(US, 0.35), (UK, 0.30), (Canada, 0.15), (Australia, 0.10)]
- Confidence threshold: Accept multiple countries if top 2-3 scores are close (within 15%)

**Implementation**:
```python
results = []
for country, score in sorted_scores:
    if len(results) == 0:  # First result
        results.append((country, score))
    elif score > (results[0][1] * 0.70):  # Within 70% of top score
        results.append((country, score))
    else:
        break

return results  # Multiple results possible
```

### B. Typos and Transliteration

**Typo Handling - Levenshtein Distance**:
- For names not found in database, calculate similarity to known names
- Accept matches with Levenshtein distance ≤ 2
- Example: "Wladimir" (typo) → fuzzy match to "Vladimir"

```python
def fuzzy_match(name, database):
    matches = []
    for db_name, country in database:
        distance = levenshtein(name, db_name)
        if distance <= 2:
            matches.append((db_name, country, distance))
    return sorted(matches, key=lambda x: x[2])
```

**Transliteration Normalization**:
- Multiple romanization standards exist (e.g., Russian: Vladimir = Wladimir = Vladimeer)
- Create variant databases:
  - Russian: ISO 9 + BGN/PCGN standards
  - Arabic: DIN 31635 + ISO 9960 + custom variants
  - Chinese: Pinyin + Wade-Giles
- Store all variants in lookup database with single canonical form

**Example**:
```
Arabic name "محمد" variants: 
  [Mohammad, Mohammed, Mohammad, Muhammad, Mohamad]
  → All map to canonical: "muhammad" → Country: ["Egypt", "Saudi Arabia", "UAE"]
```

### C. Multicultural Names

**Problem**: Names combining origins (e.g., "Mary Wang" = English + Chinese)

**Strategy: Component-Based Analysis**

1. **Parse the name** into components (first name, last name)
   - Heuristic: Last name usually carries stronger origin signal
   - First name may indicate cultural preference/immigration

2. **Score each component separately**:
   ```
   For "Mary Wang":
   - First name "Mary" → (US, 0.30), (UK, 0.25), (France, 0.20), ...
   - Last name "Wang" → (China, 0.95), (Singapore, 0.03), (Taiwan, 0.02)
   ```

3. **Weight last name more heavily** (70%) than first name (30%)
   ```
   Final Score = 0.30 × First_Component + 0.70 × Last_Component
   ```

4. **Return multicultural signal**:
   ```
   Result: {
     "primary": [("China", 0.68), ("Singapore", 0.15)],
     "cultural_mix": "East-Asian + Western",
     "components": {
       "first_name_origin": ["USA", "UK"],
       "last_name_origin": ["China"]
     }
   }
   ```

---

## 4. Evaluation Methodology

### A. Building Test Set

**Data Sources for Ground Truth**:
1. **Wikipedia Bio Database**: ~6M biographies with nationality/birthplace
2. **Geonames Dataset**: Names with known countries
3. **LinkedIn Data** (anonymized): Company location + profile names
4. **Manual Curation**: Domain experts validate ~500 names

**Test Set Composition** (minimum 10,000 names):
- 40% Common names (Smith, Johnson, Garcia, Lee, etc.)
- 30% Distinctive names (Wilkowski, Putin, Sato, Al-Rashid)
- 20% Edge cases (Multicultural, typos, transliterations)
- 10% Ambiguous cases (Multiple plausible origins)

**Stratification by Origin**:
- Major Western countries: 30% (US, UK, Germany, France)
- Eastern European: 20% (Poland, Russia, Ukraine, Czech Rep.)
- Asian: 20% (China, Japan, India, Korea)
- Middle Eastern: 15% (Saudi Arabia, UAE, Egypt, Lebanon)
- Latin American: 10% (Mexico, Brazil, Argentina)
- Other: 5%

### B. Quality Metrics

**1. Top-1 Accuracy**
```
Accuracy@1 = (# correct top result) / (# total tests)
Target: ≥ 85%
```

**2. Top-3 Accuracy**
```
Accuracy@3 = (# correct in top 3) / (# total tests)
Target: ≥ 92%
```

**3. Mean Reciprocal Rank (MRR)**
```
MRR = (1/N) × Σ(1/rank_i) for correct country
Target: ≥ 0.88
Measures: How high does correct answer rank on average?
```

**4. Precision & Recall @ K**
```
Precision@K = (# correct in top K) / K
Recall@K = (# correct in top K) / (# total with that country)

For AML use case: 
- Precision is critical (false positives waste compliance resources)
- Recall is important (missed sanctions names = regulatory risk)
```

**5. Confidence Calibration**
```
For samples where model reports confidence C:
- Accuracy should be ≈ C
- Example: When confidence = 0.80, actual accuracy should be 75-85%

Measure: Expected Calibration Error (ECE)
ECE = Σ |confidence_i - accuracy_i| / N
Target: ≤ 0.05
```

**6. Per-Country F1 Score**
```
F1 = 2 × (Precision × Recall) / (Precision + Recall)

Report separately for:
- Distinctive origin countries (F1 > 0.90 expected)
- Ambiguous countries (F1 > 0.75 expected)
- Rare countries (F1 > 0.60 acceptable)
```

### C. Testing Protocol

**Phase 1: Baseline Testing**
- Run full test set
- Report Top-1, Top-3, MRR, F1 per country

**Phase 2: Error Analysis**
- Categorize failures:
  - Transliteration/typos (should be <5% of errors)
  - Multicultural names (should be <15% of errors)
  - Ambiguous origins (should be <25% of errors)
  - True mistakes (should be <10% of errors)

**Phase 3: Confidence Calibration**
- Bin results by confidence level
- Verify accuracy matches confidence
- Adjust thresholds if needed

**Phase 4: Production Monitoring**
- Log all queries and results
- Sample review by compliance team (5% monthly)
- Update models quarterly with new data

### D. Specific Test Cases

```python
test_cases = [
    ("John Smith", ["US", "UK"], "Common Western"),
    ("Michał Wilkowski", ["Poland"], "Distinctive Polish"),
    ("Vladimir Putin", ["Russia"], "Distinctive Russian"),
    ("Mohammed Al-Rashid", ["Saudi Arabia", "UAE"], "Arab Middle East"),
    ("Mary Wang", ["China", "US"], "Multicultural"),
    ("Andrzej Kowalski", ["Poland"], "Very common Polish"),
    ("Jean Dupont", ["France"], "Common French"),
    ("José García", ["Spain", "Mexico"], "Spanish/Latin America"),
    ("李明", ["China"], "Chinese names in ideographic script"),
    ("Владимир Иванов", ["Russia"], "Cyrillic script"),
    ("Ahmad Mohamed", ["Egypt", "Saudi Arabia"], "Multiple Arab countries"),
]
```

---

## 5. Implementation Stack

### Architecture

- **Language**: Python 3.9+
- **Database**: SQLite (development) / PostgreSQL (production)
- **API Framework**: Flask (lightweight, easy containerization)
- **NLP Libraries**: 
  - `unidecode` (transliteration)
  - `fuzzywuzzy` (fuzzy matching)
  - `unicodedata` (normalization)
  - `scikit-learn` (feature extraction, naive bayes)
- **Deployment**: Docker + Docker Compose
- **API Testing**: cURL scripts

### Suggested Directory Structure

```
aml-name-origin/
├── Dockerfile
├── docker-compose.yml
├── setup_db.py
├── app.py (Flask API)
├── name_classifier.py (core logic)
├── data/
│   ├── ngrams/
│   │   ├── english.json
│   │   ├── polish.json
│   │   ├── russian.json
│   │   └── ... (other languages)
│   └── patterns.json
├── tests/
│   ├── test_cases.json
│   └── test_runner.py
└── scripts/
    ├── build.sh
    ├── run.sh
    └── test_api.sh
```

---

## 6. PoC Implementation Notes

### Data Sources Used in PoC

**Important:** The current PoC implementation uses **synthetic training data** for demonstration purposes:

1. **N-gram Models**: The bigram and trigram probability distributions in `name_classifier.py` are manually curated approximations based on linguistic patterns, NOT trained on real datasets. For production use, these should be replaced with models trained on:
   - Geonames database (2.7M+ names)
   - Census data (US, UK, Poland, etc.)
   - Wikipedia biography dataset (6M+ entries)

2. **Name Database**: Contains only ~30 hardcoded examples for fuzzy matching. Production would require 10,000+ names minimum.

3. **Pattern Rules**: Hand-crafted linguistic rules (e.g., "-ski" → Poland) are reasonably accurate but incomplete. Production should include comprehensive pattern libraries.

### Transliteration Approach

**Current Implementation**: Uses `unidecode` library for all script conversions.

**Limitations:**
- **Cyrillic names**: `unidecode` provides basic transliteration but doesn't follow ISO 9 or BGN/PCGN standards precisely
- **Arabic names**: `unidecode` approximation may not capture all phonetic variants (e.g., "محمد" has many valid romanizations)
- **Chinese names**: Pinyin conversion is simplified; Wade-Giles variants not handled

**PoC Rationale**: For proof-of-concept purposes, `unidecode` provides acceptable coverage to demonstrate the algorithmic approach without requiring specialized transliteration libraries.

**Production Requirements**: Replace with:
- `transliterate` package for Cyrillic (ISO 9 compliant)
- `pyarabic` or custom Arabic transliteration engine (DIN 31635)
- Enhanced Chinese romanization handling (Pinyin + Wade-Giles)

### Evaluation Framework

The PoC includes a comprehensive evaluation module (`evaluate.py`) with:

**Test Dataset**: 120 names across categories:
- Common Western names (US, UK)
- Distinctive names (Polish, Russian, French, German, Spanish, Italian, Arab, Chinese)
- Multicultural names (e.g., "Mary Wang")
- Typo/transliteration variants

**Metrics Implemented**:
- Top-1 Accuracy (target: ≥85%)
- Top-3 Accuracy (target: ≥92%)
- Mean Reciprocal Rank / MRR (target: ≥0.88)
- Per-country F1 scores
- Expected Calibration Error / ECE (target: ≤0.05)
- Per-category accuracy breakdown

**Usage**: `python evaluate.py`

---

## 7. Risk Mitigation

### Known Limitations

1. **Uncommon Names**: Model will have lower accuracy for rare names
   - Mitigation: Report lower confidence; require manual review

2. **Name Swapping**: Some cultures use different first/last name conventions
   - Mitigation: Try both orders; report multicultural matches

3. **Privacy**: Historical name data may perpetuate stereotypes
   - Mitigation: Use recent census data; regularly audit for bias

4. **Regulatory**: Names not reliable sole indicator for AML
   - Mitigation: Always combine with other risk factors (KYC, source of funds, etc.)

5. **PoC Data Limitations**: Synthetic n-gram models and limited training data
   - Mitigation: Document limitations; replace with real datasets before production deployment

---

## Conclusion

This system uses probabilistic n-gram models combined with linguistic pattern matching to predict name origin with expected 85%+ accuracy for Top-1 results. It should handle complex scenarios (transliteration, typos, multicultural names) through ensemble methods and explicit component analysis. Quality - as assumed - is validated through rigorous testing protocols including per-country metrics, error analysis, and confidence calibration.

## References

### Academic Papers Used
- Yu Fu, Feiyu Xu, Hans Uszkoreit (2010): [Determining the Origin and Structure of Person Names](http://www.lrec-conf.org/proceedings/lrec2010/pdf/763_Paper.pdf)
- Vladimir Pervouchine, Min Zhang, Ming Liu, Haizhou Li (2010): [Improving Name Origin Recognition with Context Features and Unlabelled Data](https://www.semanticscholar.org/paper/Improving-Name-Origin-Recognition-with-Context-and-Pervouchine-Zhang/b1322b37bf9e8bd67a9dc0dbb8ba31aac14c4f58)
- Mehdi M. Kashani, Fred Popowich, Fatiha Sadat (2006): [Automatic Transliteration of Proper Nouns from Arabic to English](https://aclanthology.org/2006.bcs-1.7.pdf)
- Kai On Wong, Osmar R. Zaïane, Faith G. Davis, Yutaka Yasui (2020): [A machine learning approach to predict ethnicity using personal name and census location in Canada](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0241239)

### Data Sources
- Geonames Database (2.7M+ names)
- US Census Bureau (name frequency by state)
- [Wikipedia Biography Database](https://github.com/DavidGrangier/wikipedia-biography-dataset) (6M+ entries)
- UN Name Database
- ISO 9, DIN 31635, CLDR standards for transliteration
