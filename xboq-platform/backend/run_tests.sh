#!/bin/bash

# XBOQ Platform - End-to-End Test Script
# Tests all backend endpoints

echo "======================================"
echo "XBOQ Platform - E2E Test Suite"
echo "======================================"
echo ""

BASE_URL="http://localhost:5000"
PASSED=0
FAILED=0

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test helper function
test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local expected_status="$5"

    echo -n "Testing: $name ... "

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint")
    elif [ "$method" = "POST" ] && [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL$endpoint")
    elif [ "$method" = "POST_JSON" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    elif [ "$method" = "POST_FILE" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL$endpoint" \
            -F "$data")
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} (Expected $expected_status, got $http_code)"
        ((FAILED++))
    fi
}

# 1. Health Check
test_endpoint "Health Check" "GET" "/health" "" "200"

# 2. Products Endpoint
test_endpoint "Products List" "GET" "/api/products" "" "200"

# 3. Trades Endpoint
test_endpoint "Trades List" "GET" "/api/trades" "" "200"

# 4. Manual Drywall Estimate
test_endpoint "Manual Drywall Estimate" "POST_JSON" "/api/estimate/manual" \
    '{"trade":"drywall","rooms":[{"name":"Test","length":10,"width":10,"height":8}]}' "200"

# 5. Manual Painting Estimate
test_endpoint "Manual Painting Estimate" "POST_JSON" "/api/estimate/manual" \
    '{"trade":"painting","rooms":[{"name":"Test","length":10,"width":10,"height":8}]}' "200"

# 6. Manual Estimate - Empty Data (should fail)
test_endpoint "Manual Estimate - No Data" "POST_JSON" "/api/estimate/manual" '{}' "400"

# 7. BOQ Upload - No File (should fail)
test_endpoint "BOQ Upload - No File" "POST" "/api/boq/upload" "" "400"

# 8. Floor Plan Upload - No File (should fail)
test_endpoint "Floor Plan Upload - No File" "POST" "/api/estimate/upload" "" "400"

# File upload tests (if test files exist)
if [ -f "test_tender.pdf" ]; then
    test_endpoint "BOQ Upload - With File" "POST_FILE" "/api/boq/upload" \
        "file=@test_tender.pdf" "200"
fi

if [ -f "test_floorplan.pdf" ]; then
    test_endpoint "Floor Plan Upload - Drywall" "POST_FILE" "/api/estimate/upload" \
        "file=@test_floorplan.pdf;trade=drywall" "200"
    test_endpoint "Floor Plan Upload - Painting" "POST_FILE" "/api/estimate/upload" \
        "file=@test_floorplan.pdf;trade=painting" "200"
fi

# Summary
echo ""
echo "======================================"
echo "Test Results Summary"
echo "======================================"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo "Total:  $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed! ✗${NC}"
    exit 1
fi
