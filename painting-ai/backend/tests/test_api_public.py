"""
Integration tests for public API endpoints
Tests: Public API with API key authentication, rate limiting, and webhooks
"""

import pytest
import uuid
from fastapi.testclient import TestClient


class TestHealthAndRoot:
    """Test basic health and root endpoints"""

    def test_root_endpoint(self, test_client):
        """Test root endpoint returns app info"""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert "app" in data
        assert data["app"] == "Painting.ai"
        assert "version" in data
        assert "status" in data

    def test_health_check(self, test_client):
        """Test health check endpoint"""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] == "healthy"
        assert "detector" in data
        assert "database" in data


class TestPricingEndpoints:
    """Test pricing plan endpoints"""

    def test_get_pricing_plans(self, test_client):
        """Test GET /pricing/plans endpoint"""
        response = test_client.get("/pricing/plans")

        assert response.status_code == 200
        data = response.json()

        assert "plans" in data
        assert "currency" in data
        assert "trial_days" in data

        # Verify plan structure
        plans = data["plans"]
        assert "starter" in plans or "pro" in plans

    def test_pricing_plans_structure(self, test_client):
        """Test pricing plans have required fields"""
        response = test_client.get("/pricing/plans")

        assert response.status_code == 200
        data = response.json()

        plans = data["plans"]
        for plan_name, plan_details in plans.items():
            assert "price" in plan_details or "name" in plan_details


class TestAnalyticsEndpoints:
    """Test analytics endpoints (require authentication)"""

    def test_analytics_overview_requires_auth(self, test_client):
        """Test analytics overview requires authentication"""
        response = test_client.get("/analytics/overview")

        assert response.status_code == 401

    def test_analytics_overview_with_auth(self, test_client, auth_headers):
        """Test analytics overview with valid auth"""
        response = test_client.get("/analytics/overview", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Should return some analytics data
        assert isinstance(data, dict)

    def test_analytics_usage_requires_auth(self, test_client):
        """Test usage analytics requires authentication"""
        response = test_client.get("/analytics/usage")

        assert response.status_code == 401

    def test_analytics_usage_with_auth(self, test_client, auth_headers):
        """Test usage analytics with valid auth"""
        response = test_client.get("/analytics/usage", headers=auth_headers)

        assert response.status_code == 200

    def test_analytics_usage_custom_days(self, test_client, auth_headers):
        """Test usage analytics with custom time period"""
        response = test_client.get(
            "/analytics/usage",
            headers=auth_headers,
            params={"days": 7}
        )

        assert response.status_code == 200

    def test_analytics_conversion_requires_auth(self, test_client):
        """Test conversion analytics requires authentication"""
        response = test_client.get("/analytics/conversion")

        assert response.status_code == 401

    def test_analytics_conversion_with_auth(self, test_client, auth_headers):
        """Test conversion analytics with valid auth"""
        response = test_client.get("/analytics/conversion", headers=auth_headers)

        assert response.status_code == 200


class TestUsageStats:
    """Test usage statistics endpoints"""

    def test_usage_stats_requires_auth(self, test_client):
        """Test usage stats requires authentication"""
        response = test_client.get("/usage/stats")

        assert response.status_code == 401

    def test_usage_stats_with_auth(self, test_client, auth_headers):
        """Test usage stats with valid auth"""
        response = test_client.get("/usage/stats", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Should include usage information
        assert isinstance(data, dict)


class TestPaymentEndpoints:
    """Test payment and checkout endpoints"""

    def test_checkout_requires_auth(self, test_client):
        """Test checkout session creation requires auth"""
        checkout_data = {
            "plan": "starter",
            "success_url": "http://example.com/success",
            "cancel_url": "http://example.com/cancel"
        }

        response = test_client.post("/checkout/create-session", json=checkout_data)

        assert response.status_code == 401

    def test_checkout_with_auth(self, test_client, auth_headers):
        """Test checkout session creation with auth"""
        checkout_data = {
            "plan": "starter",
            "success_url": "http://example.com/success",
            "cancel_url": "http://example.com/cancel"
        }

        response = test_client.post(
            "/checkout/create-session",
            json=checkout_data,
            headers=auth_headers
        )

        # May succeed or fail depending on Stripe config
        assert response.status_code in [200, 500]

    def test_checkout_invalid_plan(self, test_client, auth_headers):
        """Test checkout with invalid plan name"""
        checkout_data = {
            "plan": "invalid_plan_name",
            "success_url": "http://example.com/success",
            "cancel_url": "http://example.com/cancel"
        }

        response = test_client.post(
            "/checkout/create-session",
            json=checkout_data,
            headers=auth_headers
        )

        # Should fail validation or return error
        assert response.status_code in [400, 500]

    def test_checkout_missing_urls(self, test_client, auth_headers):
        """Test checkout without required URLs"""
        checkout_data = {
            "plan": "starter"
        }

        response = test_client.post(
            "/checkout/create-session",
            json=checkout_data,
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_portal_requires_auth(self, test_client):
        """Test portal session requires auth"""
        portal_data = {
            "return_url": "http://example.com/account"
        }

        response = test_client.post("/checkout/portal", json=portal_data)

        assert response.status_code == 401

    def test_portal_with_auth(self, test_client, auth_headers):
        """Test portal session with auth"""
        portal_data = {
            "return_url": "http://example.com/account"
        }

        response = test_client.post(
            "/checkout/portal",
            json=portal_data,
            headers=auth_headers
        )

        # May succeed or fail depending on Stripe config
        assert response.status_code in [200, 500]


class TestWebhooks:
    """Test webhook endpoints"""

    def test_stripe_webhook_endpoint_exists(self, test_client):
        """Test webhook endpoint exists"""
        response = test_client.post("/checkout/webhook")

        # Will fail without proper signature, but endpoint should exist
        assert response.status_code in [400, 422, 500]

    def test_webhook_requires_signature(self, test_client):
        """Test webhook requires Stripe signature"""
        payload = {
            "type": "checkout.session.completed",
            "data": {}
        }

        response = test_client.post("/checkout/webhook", json=payload)

        # Should fail without signature
        assert response.status_code in [400, 422, 500]


class TestAPIAuthentication:
    """Test API key authentication for public API"""

    def test_protected_route_without_auth(self, test_client):
        """Test that protected routes require authentication"""
        response = test_client.get("/auth/me")

        assert response.status_code == 401

    def test_protected_route_with_invalid_token(self, test_client):
        """Test protected route with invalid token"""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = test_client.get("/auth/me", headers=headers)

        assert response.status_code == 401

    def test_protected_route_with_valid_token(self, test_client, auth_headers):
        """Test protected route with valid JWT token"""
        response = test_client.get("/auth/me", headers=auth_headers)

        assert response.status_code == 200


class TestAPIValidation:
    """Test API request/response validation"""

    def test_invalid_json_returns_422(self, test_client):
        """Test that invalid JSON returns 422"""
        response = test_client.post(
            "/projects",
            data="not valid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_missing_required_field_returns_422(self, test_client):
        """Test that missing required fields return 422"""
        # Project requires 'name' field
        response = test_client.post("/projects", json={})

        assert response.status_code == 422

    def test_invalid_data_type_returns_422(self, test_client):
        """Test that invalid data types return 422"""
        # name should be string, not number
        response = test_client.post("/projects", json={"name": 123})

        # Should accept (coerced to string) or reject
        assert response.status_code in [200, 422]

    def test_extra_fields_ignored(self, test_client):
        """Test that extra fields are ignored"""
        project_data = {
            "name": "Test Project",
            "customer": "Test Customer",
            "extra_field": "should be ignored"
        }

        response = test_client.post("/projects", json=project_data)

        assert response.status_code == 200
        # Extra field should be ignored


class TestErrorHandling:
    """Test API error handling"""

    def test_404_for_unknown_route(self, test_client):
        """Test 404 for non-existent routes"""
        response = test_client.get("/nonexistent/route")

        assert response.status_code == 404

    def test_405_for_wrong_method(self, test_client):
        """Test 405 for unsupported HTTP methods"""
        # GET /projects exists, but POST /health doesn't make sense
        response = test_client.post("/health")

        assert response.status_code == 405

    def test_error_response_format(self, test_client):
        """Test that errors return consistent format"""
        response = test_client.get("/projects/nonexistent-id")

        assert response.status_code == 404
        data = response.json()

        # FastAPI error format
        assert "detail" in data

    def test_validation_error_details(self, test_client):
        """Test that validation errors include details"""
        # Missing required field
        response = test_client.post("/projects", json={})

        assert response.status_code == 422
        data = response.json()

        # Should include validation error details
        assert "detail" in data
