#!/bin/bash
# Comprehensive API testing suite for AML Name Classifier

set -e

API_URL="http://localhost:5050"
FAILED=0
PASSED=0

echo "=========================================="
echo "AML Name Classifier API Test Suite"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo -e "${YELLOW}Test 1: Health Check${NC}"
if curl -s "${API_URL}/health" | grep -q "healthy"; then
    echo -e "${GREEN}✓ PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED${NC}"
    ((FAILED++))
fi
echo ""

# Test 2: Version Check
echo -e "${YELLOW}Test 2: Version Endpoint${NC}"
RESPONSE=$(curl -s "${API_URL}/api/version")
if echo "$RESPONSE" | grep -q "AML Name Origin Classifier"; then
    echo -e "${GREEN}✓ PASSED${NC}"
    echo "  Version: $(echo "$RESPONSE" | grep -o '"version":"[^"]*"')"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED${NC}"
    ((FAILED++))
fi
echo ""

# Test 3: Classify - John Smith (US)
echo -e "${YELLOW}Test 3: Classify John Smith${NC}"
RESPONSE=$(curl -s -X POST "${API_URL}/api/classify" \
    -H "Content-Type: application/json" \
    -d '{"first_name":"John","last_name":"Smith"}')

if echo "$RESPONSE" | grep -q '"success":true'; then
    echo -e "${GREEN}✓ PASSED${NC}"
    RESULT=$(echo "$RESPONSE" | grep -o '"results":\[\[.*?\]\]' | head -1)
    echo "  Result: $RESULT"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED${NC}"
    echo "  Response: $RESPONSE"
    ((FAILED++))
fi
echo ""

# Test 4: Classify - Michał Wilkowski (Poland)
echo -e "${YELLOW}Test 4: Classify Michał Wilkowski (Polish name)${NC}"
RESPONSE=$(curl -s -X POST "${API_URL}/api/classify" \
    -H "Content-Type: application/json" \
    -d '{"first_name":"Michał","last_name":"Wilkowski"}')

if echo "$RESPONSE" | grep -q "Poland"; then
    echo -e "${GREEN}✓ PASSED - Correctly identified as Polish${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED${NC}"
    ((FAILED++))
fi
echo ""

# Test 5: Classify - Vladimir Putin (Russia)
echo -e "${YELLOW}Test 5: Classify Vladimir Putin (Russian name)${NC}"
RESPONSE=$(curl -s -X POST "${API_URL}/api/classify" \
    -H "Content-Type: application/json" \
    -d '{"first_name":"Vladimir","last_name":"Putin"}')

if echo "$RESPONSE" | grep -q "Russia"; then
    echo -e "${GREEN}✓ PASSED - Correctly identified as Russian${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED${NC}"
    ((FAILED++))
fi
echo ""

# Test 6: Classify - Ahmed Al-Rashid (Arab)
echo -e "${YELLOW}Test 6: Classify Ahmed Al-Rashid (Arab name)${NC}"
RESPONSE=$(curl -s -X POST "${API_URL}/api/classify" \
    -H "Content-Type: application/json" \
    -d '{"first_name":"Ahmed","last_name":"Al-Rashid"}')

if echo "$RESPONSE" | grep -q "Arab"; then
    echo -e "${GREEN}✓ PASSED - Correctly identified as Arab${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED${NC}"
    ((FAILED++))
fi
echo ""

# Test 7: Classify - Jean Dupont (France)
echo -e "${YELLOW}Test 7: Classify Jean Dupont (French name)${NC}"
RESPONSE=$(curl -s -X POST "${API_URL}/api/classify" \
    -H "Content-Type: application/json" \
    -d '{"first_name":"Jean","last_name":"Dupont"}')

if echo "$RESPONSE" | grep -q "France"; then
    echo -e "${GREEN}✓ PASSED - Correctly identified as French${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED${NC}"
    ((FAILED++))
fi
echo ""

# Test 8: Classify - José García (Spain)
echo -e "${YELLOW}Test 8: Classify José García (Spanish name)${NC}"
RESPONSE=$(curl -s -X POST "${API_URL}/api/classify" \
    -H "Content-Type: application/json" \
    -d '{"first_name":"José","last_name":"García"}')

if echo "$RESPONSE" | grep -q "Spain"; then
    echo -e "${GREEN}✓ PASSED - Correctly identified as Spanish${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED${NC}"
    ((FAILED++))
fi
echo ""

# Test 9: Batch Classification
echo -e "${YELLOW}Test 9: Batch Classification${NC}"
RESPONSE=$(curl -s -X POST "${API_URL}/api/batch" \
    -H "Content-Type: application/json" \
    -d '{
        "names": [
            {"first_name":"John","last_name":"Smith"},
            {"first_name":"Vladimir","last_name":"Putin"},
            {"first_name":"José","last_name":"García"}
        ]
    }')

if echo "$RESPONSE" | grep -q '"count":3'; then
    echo -e "${GREEN}✓ PASSED - Batch processed 3 names${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED${NC}"
    ((FAILED++))
fi
echo ""

# Test 10: Missing Parameters
echo -e "${YELLOW}Test 10: Error Handling - Missing Parameters${NC}"
RESPONSE=$(curl -s -X POST "${API_URL}/api/classify" \
    -H "Content-Type: application/json" \
    -d '{"first_name":"John"}')

if echo "$RESPONSE" | grep -q '"success":false'; then
    echo -e "${GREEN}✓ PASSED - Correctly rejected invalid request${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED${NC}"
    ((FAILED++))
fi
echo ""

# Test 11: Non-existent endpoint
echo -e "${YELLOW}Test 11: 404 Error Handling${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/api/nonexistent")
if [ "$HTTP_CODE" = "404" ]; then
    echo -e "${GREEN}✓ PASSED - 404 returned correctly${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED - Expected 404, got $HTTP_CODE${NC}"
    ((FAILED++))
fi
echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo "Total:  $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi
