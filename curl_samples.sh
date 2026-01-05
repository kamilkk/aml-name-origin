#!/bin/bash
# Quick reference cURL commands for AML Name Origin Classifier API
# Usage: Copy and paste any command below to test the API

API_URL="http://localhost:5050"

echo "=========================================="
echo "AML Name Origin Classifier - cURL Examples"
echo "=========================================="
echo ""

# Example 1: Health Check
echo "1. HEALTH CHECK"
echo "================"
echo "curl ${API_URL}/health"
echo ""

# Example 2: Get Version
echo "2. GET API VERSION"
echo "==================="
echo "curl ${API_URL}/api/version"
echo ""

# Example 3: Classify John Smith (US)
echo "3. CLASSIFY: John Smith (US)"
echo "============================="
echo "curl -X POST ${API_URL}/api/classify \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -d '{\"first_name\":\"John\",\"last_name\":\"Smith\"}'"
echo ""
echo "Expected: US with high confidence"
echo ""

# Example 4: Classify Michał Wilkowski (Poland)
echo "4. CLASSIFY: Michał Wilkowski (Poland)"
echo "========================================"
echo "curl -X POST ${API_URL}/api/classify \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -d '{\"first_name\":\"Michał\",\"last_name\":\"Wilkowski\"}'"
echo ""
echo "Expected: Poland with very high confidence (0.90+)"
echo ""

# Example 5: Classify Vladimir Putin (Russia)
echo "5. CLASSIFY: Vladimir Putin (Russia)"
echo "===================================="
echo "curl -X POST ${API_URL}/api/classify \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -d '{\"first_name\":\"Vladimir\",\"last_name\":\"Putin\"}'"
echo ""
echo "Expected: Russia with very high confidence (0.95+)"
echo ""

# Example 6: Classify Ahmed Al-Rashid (Arab)
echo "6. CLASSIFY: Ahmed Al-Rashid (Arab)"
echo "===================================="
echo "curl -X POST ${API_URL}/api/classify \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -d '{\"first_name\":\"Ahmed\",\"last_name\":\"Al-Rashid\"}'"
echo ""
echo "Expected: Arab with high confidence"
echo ""

# Example 7: Classify Jean Dupont (France)
echo "7. CLASSIFY: Jean Dupont (France)"
echo "=================================="
echo "curl -X POST ${API_URL}/api/classify \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -d '{\"first_name\":\"Jean\",\"last_name\":\"Dupont\"}'"
echo ""
echo "Expected: France with high confidence"
echo ""

# Example 8: Classify José García (Spain)
echo "8. CLASSIFY: José García (Spain)"
echo "================================"
echo "curl -X POST ${API_URL}/api/classify \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -d '{\"first_name\":\"José\",\"last_name\":\"García\"}'"
echo ""
echo "Expected: Spain with high confidence"
echo ""

# Example 9: Multicultural Name - Mary Wang
echo "9. CLASSIFY: Mary Wang (Multicultural)"
echo "======================================"
echo "curl -X POST ${API_URL}/api/classify \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -d '{\"first_name\":\"Mary\",\"last_name\":\"Wang\"}'"
echo ""
echo "Expected: China primary, US/UK secondary"
echo ""

# Example 10: Typo tolerance - Wladimir Putin
echo "10. CLASSIFY: Wladimir Putin (Typo - Transliteration Variant)"
echo "=============================================================="
echo "curl -X POST ${API_URL}/api/classify \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -d '{\"first_name\":\"Wladimir\",\"last_name\":\"Putin\"}'"
echo ""
echo "Expected: Russia with high confidence (via fuzzy matching)"
echo ""

# Example 11: Batch Classification
echo "11. BATCH CLASSIFICATION (4 names)"
echo "=================================="
echo "curl -X POST ${API_URL}/api/batch \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -d '{"
echo "        \"names\": ["
echo "            {\"first_name\":\"John\",\"last_name\":\"Smith\"},"
echo "            {\"first_name\":\"Michał\",\"last_name\":\"Wilkowski\"},"
echo "            {\"first_name\":\"Ahmed\",\"last_name\":\"Al-Rashid\"},"
echo "            {\"first_name\":\"Jean\",\"last_name\":\"Dupont\"}"
echo "        ]"
echo "    }'"
echo ""
echo "Expected: 4 results with country classifications"
echo ""

# Example 12: Error Case - Missing Parameters
echo "12. ERROR CASE: Missing Last Name"
echo "=================================="
echo "curl -X POST ${API_URL}/api/classify \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -d '{\"first_name\":\"John\"}'"
echo ""
echo "Expected: 400 error with message about missing last_name"
echo ""

# Example 13: Error Case - Invalid JSON
echo "13. ERROR CASE: Invalid Batch (too many names)"
echo "=============================================="
echo "curl -X POST ${API_URL}/api/batch \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -d '{\"names\": [" + ("{\"first_name\":\"Name\",\"last_name\":\"Test\"}," | sed 's/,$//' | awk '{for(i=0;i<1001;i++) print}' | head -1001) + "]}'"
echo ""
echo "Expected: 400 error about exceeding 1000 names limit"
echo ""

# Example 14: Non-existent Endpoint
echo "14. ERROR CASE: Non-existent Endpoint"
echo "====================================="
echo "curl http://localhost:5050/api/nonexistent"
echo ""
echo "Expected: 404 error with list of available endpoints"
echo ""

echo ""
echo "=========================================="
echo "Tips:"
echo "=========================================="
echo "• Add -v flag to curl commands for verbose output"
echo "• Use 'jq' to pretty-print JSON: curl ... | jq ."
echo "• Use 'time' to measure response time: time curl ..."
echo "• Check container logs: docker-compose logs -f"
echo ""
