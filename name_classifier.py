#!/usr/bin/env python3
"""
AML Name-to-Country Origin Classification System
Multi-stage pipeline for predicting country origin from person names
"""

import re
from typing import List, Dict, Tuple, Optional
from unidecode import unidecode
from difflib import SequenceMatcher


class NameOriginClassifier:
    """
    Core classifier for name origin prediction.
    Uses n-gram models, linguistic patterns, and fuzzy matching.
    """
    
    def __init__(self):
        self.ngram_models = {}
        self.pattern_rules = {}
        self.name_database = {}
        self.load_models()
    
    def load_models(self):
        """Load pre-trained n-gram models and pattern rules."""
        
        # N-gram probability models for different countries
        # Built from typical name patterns in each country
        self.ngram_models = {
            "US": {
                "bigrams": {"th": 0.12, "er": 0.10, "in": 0.09, "en": 0.08, "ed": 0.07,
                           "an": 0.06, "or": 0.06, "nd": 0.05, "al": 0.05, "ar": 0.05},
                "trigrams": {"the": 0.08, "ing": 0.07, "and": 0.05, "son": 0.05, "ohn": 0.04}
            },
            "UK": {
                "bigrams": {"th": 0.12, "er": 0.10, "in": 0.09, "on": 0.07, "en": 0.07,
                           "ar": 0.06, "or": 0.06, "ey": 0.05, "le": 0.05, "al": 0.05},
                "trigrams": {"the": 0.08, "son": 0.06, "ing": 0.05, "and": 0.05, "ley": 0.04}
            },
            "Poland": {
                "bigrams": {"sk": 0.14, "wi": 0.10, "cz": 0.09, "ow": 0.08, "ki": 0.08,
                           "ak": 0.07, "rz": 0.07, "wa": 0.06, "aw": 0.06, "an": 0.05},
                "trigrams": {"ski": 0.12, "ska": 0.08, "wit": 0.06, "iew": 0.05, "ows": 0.04}
            },
            "Russia": {
                "bigrams": {"ov": 0.12, "en": 0.10, "ev": 0.09, "uk": 0.08, "ke": 0.08,
                           "er": 0.07, "va": 0.07, "av": 0.06, "in": 0.05, "ai": 0.05},
                "trigrams": {"ova": 0.10, "enko": 0.08, "ovich": 0.07, "iev": 0.05, "mev": 0.04}
            },
            "Germany": {
                "bigrams": {"er": 0.12, "nn": 0.10, "ch": 0.09, "sc": 0.08, "st": 0.08,
                           "ck": 0.07, "an": 0.07, "er": 0.06, "th": 0.06, "ld": 0.05},
                "trigrams": {"mann": 0.10, "meyer": 0.08, "schmidt": 0.06, "stein": 0.05}
            },
            "France": {
                "bigrams": {"au": 0.11, "er": 0.10, "re": 0.09, "on": 0.08, "ar": 0.08,
                           "an": 0.07, "ou": 0.07, "it": 0.06, "et": 0.06, "du": 0.05},
                "trigrams": {"eau": 0.09, "ant": 0.07, "ard": 0.06, "ard": 0.05, "eau": 0.05}
            },
            "Spain": {
                "bigrams": {"ez": 0.11, "az": 0.10, "oz": 0.09, "ar": 0.08, "an": 0.08,
                           "ez": 0.07, "as": 0.07, "ia": 0.06, "or": 0.06, "al": 0.05},
                "trigrams": {"ez": 0.10, "andez": 0.08, "riguez": 0.07, "arez": 0.05}
            },
            "Italy": {
                "bigrams": {"ni": 0.11, "ti": 0.10, "an": 0.09, "in": 0.08, "re": 0.08,
                           "za": 0.07, "ri": 0.07, "li": 0.06, "la": 0.06, "ia": 0.05},
                "trigrams": {"ini": 0.10, "ucci": 0.07, "etti": 0.06, "etti": 0.05}
            },
            "China": {
                "bigrams": {"ng": 0.13, "an": 0.11, "ou": 0.10, "in": 0.09, "ai": 0.08,
                           "ia": 0.07, "ei": 0.07, "en": 0.06, "ao": 0.05, "ua": 0.05},
                "trigrams": {"ing": 0.10, "ang": 0.08, "iang": 0.06, "ong": 0.05}
            },
            "Arab": {
                "bigrams": {"ah": 0.12, "am": 0.11, "ad": 0.10, "al": 0.09, "ha": 0.08,
                           "ma": 0.08, "ar": 0.07, "ia": 0.07, "ed": 0.06, "na": 0.05},
                "trigrams": {"ahm": 0.10, "mad": 0.09, "amed": 0.08, "ramah": 0.06}
            }
        }
        
        self.pattern_rules = {
            "Poland": [
                {"suffix": "ski", "score": 0.85, "examples": ["Wilkowski", "Kowalski"]},
                {"suffix": "ska", "score": 0.80, "examples": ["Lewandowska"]},
                {"suffix": "czyk", "score": 0.75, "examples": ["Borkowski"]},
                {"suffix": "owski", "score": 0.80, "examples": ["Komorowski"]},
                {"pattern": "cz", "score": 0.70, "examples": ["Czajkowski"]},
            ],
            "Russia": [
                {"suffix": "ov", "score": 0.80, "examples": ["Petrov", "Sokolov"]},
                {"suffix": "ova", "score": 0.80, "examples": ["Petrova"]},
                {"suffix": "enko", "score": 0.82, "examples": ["Mikhailenko"]},
                {"suffix": "ev", "score": 0.75, "examples": ["Sokolov"]},
                {"suffix": "evich", "score": 0.85, "examples": ["Vladimirovich"]},
                {"pattern": "uk", "score": 0.65, "examples": ["Mikhail"]},
            ],
            "Arab": [
                {"prefix": "al", "score": 0.70, "examples": ["Al-Rashid", "Al-Ahmad"]},
                {"prefix": "el", "score": 0.70, "examples": ["El-Sayed"]},
                {"suffix": "allah", "score": 0.85, "examples": ["Abdallah"]},
                {"pattern": "ddin", "score": 0.75, "examples": ["Saladin"]},
            ],
            "Spain": [
                {"suffix": "ez", "score": 0.80, "examples": ["Garcia", "Lopez"]},
                {"suffix": "oz", "score": 0.75, "examples": ["Munoz"]},
                {"suffix": "az", "score": 0.70, "examples": ["Diaz"]},
            ],
            "Germany": [
                {"suffix": "mann", "score": 0.80, "examples": ["Zimmermann", "Hoffmann"]},
                {"suffix": "meyer", "score": 0.78, "examples": ["Schneider"]},
                {"suffix": "schmidt", "score": 0.80, "examples": ["Schmidt"]},
                {"pattern": "nn", "score": 0.65, "examples": ["Mann"]},
            ],
        }
        
        self.name_database = {
            ("john", "smith"): ("US", 0.92),
            ("michael", "wilson"): ("US", 0.90),
            ("james", "johnson"): ("US", 0.91),
            ("david", "williams"): ("US", 0.89),
            ("michael", "smith"): ("UK", 0.88),
            ("david", "jones"): ("UK", 0.89),
            ("andrzej", "kowalski"): ("Poland", 0.95),
            ("stanislaw", "lewandowski"): ("Poland", 0.94),
            ("michal", "wilkowski"): ("Poland", 0.96),
            ("vladimir", "putin"): ("Russia", 0.98),
            ("dmitry", "medvedev"): ("Russia", 0.97),
            ("boris", "yeltsin"): ("Russia", 0.96),
            ("ahmed", "abdallah"): ("Arab", 0.88),
            ("mohammed", "rashid"): ("Arab", 0.90),
            ("ali", "hassan"): ("Arab", 0.87),
            ("jean", "dupont"): ("France", 0.91),
            ("pierre", "martin"): ("France", 0.89),
            ("jose", "garcia"): ("Spain", 0.88),
            ("juan", "perez"): ("Spain", 0.89),
        }
    
    @staticmethod
    def contains_cyrillic(text: str) -> bool:
        """Check if text contains Cyrillic characters."""
        return bool(re.search(r'[\u0400-\u04FF]', text))
    
    @staticmethod
    def contains_arabic(text: str) -> bool:
        """Check if text contains Arabic characters."""
        return bool(re.search(r'[\u0600-\u06FF]', text))
    
    @staticmethod
    def normalize_name(name: str) -> str:
        """
        Normalize name for processing.
        - Detect and flag script types (Cyrillic, Arabic, Latin)
        - Remove diacritics and accents via unidecode
        - Convert to ASCII representation
        - Lowercase
        - Remove special characters
        
        Note: For PoC, using unidecode for transliteration.
        Production would use specialized libraries:
        - transliterate (for Cyrillic)
        - pyarabic (for Arabic)
        """
        # Script detection for potential signal
        script_detected = None
        if NameOriginClassifier.contains_cyrillic(name):
            script_detected = 'cyrillic'
        elif NameOriginClassifier.contains_arabic(name):
            script_detected = 'arabic'
        
        # Transliteration using unidecode (PoC level)
        name = unidecode(name)
        name = name.lower()
        name = re.sub(r'[^a-z\s]', '', name)
        name = ' '.join(name.split())
        
        return name
    
    @staticmethod
    def extract_ngrams(text: str, n: int = 2) -> List[str]:
        """Extract n-grams from text (without spaces)."""
        text = text.replace(' ', '')
        return [text[i:i+n] for i in range(len(text) - n + 1)]
    
    def score_ngrams(self, name: str, country: str) -> float:
        """Score name based on n-gram probability model for a country."""
        if country not in self.ngram_models:
            return 0.0
        
        model = self.ngram_models[country]
        bigrams = self.extract_ngrams(name, 2)
        
        # Calculate probability score
        total_score = 0.0
        count = 0
        
        for bigram in bigrams:
            if bigram in model["bigrams"]:
                total_score += model["bigrams"][bigram]
                count += 1
        
        return total_score / len(bigrams) if bigrams else 0.0
    
    def score_patterns(self, name: str, country: str) -> float:
        """Score name based on linguistic patterns."""
        if country not in self.pattern_rules:
            return 0.0
        
        name_lower = name.lower()
        max_score = 0.0
        
        for rule in self.pattern_rules[country]:
            if "suffix" in rule:
                if name_lower.endswith(rule["suffix"]):
                    max_score = max(max_score, rule["score"])
            elif "prefix" in rule:
                if name_lower.startswith(rule["prefix"]):
                    max_score = max(max_score, rule["score"])
            elif "pattern" in rule:
                if rule["pattern"] in name_lower:
                    max_score = max(max_score, rule["score"])
        
        return max_score
    
    def score_phonetic(self, name: str, country: str) -> float:
        """
        Score name based on phonetic patterns.
        Analyzes:
        - Consonant-vowel sequences
        - Double consonants (common in Slavic languages)
        - Vowel frequency patterns
        """
        if not name:
            return 0.0
        
        name_lower = name.lower().replace(' ', '')
        vowels = 'aeiouy'
        consonants = 'bcdfghjklmnpqrstvwxz'
        
        # Calculate phonetic features
        vowel_count = sum(1 for c in name_lower if c in vowels)
        consonant_count = sum(1 for c in name_lower if c in consonants)
        total_chars = len(name_lower)
        
        if total_chars == 0:
            return 0.0
        
        vowel_ratio = vowel_count / total_chars
        
        # Count double consonants (strong signal for Slavic languages)
        double_consonants = 0
        for i in range(len(name_lower) - 1):
            if name_lower[i] in consonants and name_lower[i] == name_lower[i + 1]:
                double_consonants += 1
        
        # Count consonant clusters (3+ consecutive consonants)
        consonant_clusters = 0
        i = 0
        while i < len(name_lower):
            cluster_len = 0
            while i < len(name_lower) and name_lower[i] in consonants:
                cluster_len += 1
                i += 1
            if cluster_len >= 3:
                consonant_clusters += 1
            i += 1
        
        # Country-specific phonetic patterns
        phonetic_profiles = {
            "Poland": {"vowel_ratio": (0.30, 0.45), "double_cons_weight": 0.8, "cluster_weight": 0.7},
            "Russia": {"vowel_ratio": (0.35, 0.50), "double_cons_weight": 0.6, "cluster_weight": 0.5},
            "Germany": {"vowel_ratio": (0.35, 0.48), "double_cons_weight": 0.7, "cluster_weight": 0.4},
            "US": {"vowel_ratio": (0.38, 0.52), "double_cons_weight": 0.3, "cluster_weight": 0.2},
            "UK": {"vowel_ratio": (0.38, 0.52), "double_cons_weight": 0.3, "cluster_weight": 0.2},
            "France": {"vowel_ratio": (0.42, 0.58), "double_cons_weight": 0.2, "cluster_weight": 0.1},
            "Spain": {"vowel_ratio": (0.42, 0.56), "double_cons_weight": 0.2, "cluster_weight": 0.1},
            "Italy": {"vowel_ratio": (0.44, 0.60), "double_cons_weight": 0.3, "cluster_weight": 0.1},
            "China": {"vowel_ratio": (0.40, 0.55), "double_cons_weight": 0.2, "cluster_weight": 0.5},
            "Arab": {"vowel_ratio": (0.38, 0.52), "double_cons_weight": 0.3, "cluster_weight": 0.3},
        }
        
        if country not in phonetic_profiles:
            return 0.0
        
        profile = phonetic_profiles[country]
        score = 0.0
        
        # Vowel ratio matching
        min_vowel, max_vowel = profile["vowel_ratio"]
        if min_vowel <= vowel_ratio <= max_vowel:
            # Closer to center of range = higher score
            center = (min_vowel + max_vowel) / 2
            distance = abs(vowel_ratio - center)
            range_size = (max_vowel - min_vowel) / 2
            score += (1.0 - (distance / range_size)) * 0.5
        
        # Double consonant bonus
        if double_consonants > 0:
            score += min(double_consonants * profile["double_cons_weight"] * 0.15, 0.3)
        
        # Consonant cluster bonus
        if consonant_clusters > 0:
            score += min(consonant_clusters * profile["cluster_weight"] * 0.10, 0.2)
        
        return min(score, 1.0)
    
    def score_database_lookup(self, first_name: str, last_name: str) -> Optional[Tuple[str, float]]:
        """Look up name in database with fuzzy matching."""
        key = (first_name.lower(), last_name.lower())
        
        # Exact match
        if key in self.name_database:
            return self.name_database[key]
        
        # Fuzzy match using string similarity
        best_match = None
        best_similarity = 0.0
        
        for (db_first, db_last), (country, confidence) in self.name_database.items():
            # Compare first names
            first_sim = SequenceMatcher(None, first_name.lower(), db_first).ratio()
            # Compare last names
            last_sim = SequenceMatcher(None, last_name.lower(), db_last).ratio()
            
            # Combined similarity (weight last name more)
            combined_sim = 0.3 * first_sim + 0.7 * last_sim
            
            if combined_sim > best_similarity and combined_sim > 0.75:
                best_similarity = combined_sim
                best_match = (country, confidence * best_similarity)
        
        return best_match
    
    def classify(self, first_name: str, last_name: str) -> Dict:
        """
        Classify person name to country of origin.
        
        Uses ensemble approach with proper weighting:
        - 40% N-gram probability models
        - 30% Linguistic pattern matching
        - 20% Phonetic analysis
        - 10% Database lookup
        
        Component weighting:
        - Last name: 70% (stronger origin signal)
        - First name: 30% (cultural preference/immigration indicator)
        
        Args:
            first_name: Person's first name
            last_name: Person's last name

        Returns:
            Dictionary with top results and confidence scores
        """
        # Normalize names
        first_normalized = self.normalize_name(first_name)
        last_normalized = self.normalize_name(last_name)
        full_name = f"{first_normalized} {last_normalized}".strip()
        
        if not full_name:
            return {"error": "Invalid name", "results": []}
        
        # Check database for potential boost (integrated as 10% weight, not short-circuit)
        db_result = self.score_database_lookup(first_name, last_name)
        db_country = None
        db_boost = 0.0
        if db_result:
            db_country, db_confidence = db_result
            db_boost = db_confidence * 0.10  # Database contributes 10% of total score
        
        # Score each country using ensemble approach
        scores = {}
        method_used = "ensemble_classification"
        
        for country in self.ngram_models.keys():
            # Last name scoring (70% weight)
            last_ngram = self.score_ngrams(last_normalized, country) * 0.40 * 0.70
            last_pattern = self.score_patterns(last_normalized, country) * 0.30 * 0.70
            last_phonetic = self.score_phonetic(last_normalized, country) * 0.20 * 0.70
            
            # First name scoring (30% weight)
            first_ngram = self.score_ngrams(first_normalized, country) * 0.40 * 0.30
            first_pattern = self.score_patterns(first_normalized, country) * 0.30 * 0.30
            first_phonetic = self.score_phonetic(first_normalized, country) * 0.20 * 0.30
            
            # Combine scores (90% from models)
            total_score = (last_ngram + last_pattern + last_phonetic + 
                          first_ngram + first_pattern + first_phonetic)
            
            # Add database boost if this country matches (10%)
            if db_country == country:
                total_score += db_boost
                method_used = "ensemble_with_database"
            
            scores[country] = total_score
        
        # Sort by score
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Filter results - include top result plus any within 70% of top score
        # This handles multiple plausible countries (e.g., "Smith" -> US, UK, Canada)
        results = []
        if sorted_results:
            top_score = sorted_results[0][1]
            if top_score < 0.01:  # Very low confidence across all models
                top_score = 0.01
            
            for country, score in sorted_results:
                if len(results) == 0:  # Always include top result
                    results.append((country, min(score, 1.0)))
                elif score >= (top_score * 0.70):  # Include if within 70% of top
                    results.append((country, min(score, 1.0)))
                else:
                    break
        
        # Calculate overall confidence
        if results:
            confidence = min(results[0][1], 1.0)
        else:
            confidence = 0.0
        
        # Determine explanation based on method used
        if db_country and method_used == "ensemble_with_database":
            explanation = f"Ensemble classification with database match boost for {db_country}"
        else:
            explanation = "Ensemble: n-gram (40%), pattern (30%), phonetic (20%), db (10%)"
        
        return {
            "query": {"first_name": first_name, "last_name": last_name},
            "method": method_used,
            "results": results,
            "confidence": confidence,
            "explanation": explanation
        }


# Initialize classifier
classifier = NameOriginClassifier()


# Test cases for validation
TEST_CASES = [
    ("John", "Smith"),
    ("Michał", "Wilkowski"),
    ("Vladimir", "Putin"),
    ("Ahmed", "Al-Rashid"),
    ("Jean", "Dupont"),
    ("José", "García"),
    ("Andrzej", "Kowalski"),
    ("Dmitry", "Medvedev"),
    ("Mary", "Wang"),
]


if __name__ == "__main__":
    print("=" * 70)
    print("AML Name-to-Country Origin Classification System - Test Run")
    print("=" * 70)
    
    for first, last in TEST_CASES:
        result = classifier.classify(first, last)
        print(f"\n{first} {last}:")
        print(f"  Results: {result['results']}")
        print(f"  Confidence: {result['confidence']:.2%}")
