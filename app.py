#!/usr/bin/env python3
"""
Flask API for AML Name-to-Country Origin Classification System
Exposes REST endpoints for name origin prediction
"""

from flask import Flask, request, jsonify
from name_classifier import classifier
from datetime import datetime

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# simple in-memory request log for monitoring
request_log = []


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "AML Name Origin Classifier",
        "timestamp": datetime.utcnow().isoformat()
    }), 200


@app.route('/api/classify', methods=['POST'])
def classify_name():
    """
    Classify person name to country of origin.
    
    Expected JSON payload:
    {
        "first_name": "John",
        "last_name": "Smith"
    }
    
    Returns:
    {
        "success": true,
        "query": {"first_name": "John", "last_name": "Smith"},
        "results": [["US", 0.85], ["UK", 0.10]],
        "confidence": 0.85,
        "explanation": "..."
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "No JSON payload provided"}), 400
        
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        
        if not first_name or not last_name:
            return jsonify({
                "success": False, 
                "error": "Both 'first_name' and 'last_name' are required"
            }), 400
        
        result = classifier.classify(first_name, last_name)
        
        if "results" in result:
            result["results"] = [[country, float(score)] for country, score in result["results"]]
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "first_name": first_name,
            "last_name": last_name,
            "top_result": result["results"][0][0] if result["results"] else None,
            "confidence": float(result.get("confidence", 0))
        }
        request_log.append(log_entry)
        
        if len(request_log) > 10000:
            request_log.pop(0)
        
        return jsonify({
            "success": True,
            "query": result["query"],
            "results": result["results"],
            "confidence": float(result.get("confidence", 0)),
            "explanation": result.get("explanation", ""),
            "method": result.get("method", "")
        }), 200
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Classification error: {str(e)}"
        }), 500


@app.route('/api/batch', methods=['POST'])
def batch_classify():
    """
    Batch classify multiple names.
    
    Expected JSON payload:
    {
        "names": [
            {"first_name": "John", "last_name": "Smith"},
            {"first_name": "Vladimir", "last_name": "Putin"}
        ]
    }
    
    Returns:
    {
        "success": true,
        "count": 2,
        "results": [
            {"name": "John Smith", "origins": [...], "confidence": 0.85},
            ...
        ]
    }
    """
    try:
        data = request.get_json()
        
        if not data or "names" not in data:
            return jsonify({"success": False, "error": "Missing 'names' array"}), 400
        
        names = data.get("names", [])
        
        if not isinstance(names, list):
            return jsonify({"success": False, "error": "'names' must be an array"}), 400
        
        if len(names) > 1000:
            return jsonify({
                "success": False, 
                "error": "Maximum 1000 names per batch"
            }), 400
        
        results = []
        for name_entry in names:
            first_name = name_entry.get("first_name", "").strip()
            last_name = name_entry.get("last_name", "").strip()
            
            if not first_name or not last_name:
                results.append({
                    "error": "first_name and last_name are required"
                })
                continue
            
            result = classifier.classify(first_name, last_name)
            
            results.append({
                "name": f"{first_name} {last_name}",
                "origins": [[country, float(score)] for country, score in result["results"]],
                "confidence": float(result.get("confidence", 0))
            })
        
        return jsonify({
            "success": True,
            "count": len(results),
            "results": results
        }), 200
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Batch classification error: {str(e)}"
        }), 500


@app.route('/api/version', methods=['GET'])
def version():
    """Get API version and model info."""
    return jsonify({
        "version": "1.0.0",
        "service": "AML Name Origin Classifier PoC",
        "description": "Multi-stage pipeline for predicting country of origin from person names",
        "countries_supported": list(classifier.ngram_models.keys()),
        "features": [
            "n-gram probability models",
            "linguistic pattern matching",
            "database lookup with fuzzy matching",
            "confidence scoring",
            "batch processing"
        ]
    }), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "available_endpoints": [
            "GET /health",
            "GET /api/version",
            "POST /api/classify",
            "POST /api/batch"
        ]
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({
        "success": False,
        "error": "Method not allowed"
    }), 405


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=False)
