from app.main import app


def test_test_mode_api_routes_are_registered_without_authentication() -> None:
    paths = {route.path for route in app.routes}

    assert "/api/v1/health" in paths
    assert "/api/v1/sessions" in paths
    assert "/api/v1/sessions/{session_id}/messages" in paths
    assert "/api/v1/sessions/{session_id}/reports" in paths
