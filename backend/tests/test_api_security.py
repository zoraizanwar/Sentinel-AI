"""Security and Payload Hardening Tests for Sentinel AI."""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.security import sanitize_filename




class TestApiSecurity:

    def test_filename_sanitization(self):
        # Path traversal attack
        assert sanitize_filename("../../../etc/passwd.csv") == "passwd.csv"
        assert sanitize_filename("..\\..\\windows\\system32\\cmd.exe.csv") == "cmd.exe.csv"

        # Dangerous characters and null bytes
        sanitized = sanitize_filename("exploit;rm -rf /;test.csv")
        assert ";" not in sanitized
        assert " " not in sanitized

        # Hidden file
        assert sanitize_filename(".hidden.csv") == "upload_hidden.csv"

    def test_path_traversal_upload_sanitized_cleanly(self, client, sample_valid_df):
        import io
        buf = io.BytesIO()
        sample_valid_df.to_csv(buf, index=False)
        buf.seek(0)

        files = {"file": ("../../../../malicious.csv", buf.getvalue(), "text/csv")}
        response = client.post("/api/v1/dataset/inspect", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data["dataset_name"] == "malicious.csv"
        assert ".." not in data["dataset_name"]

    def test_production_error_sanitization_no_stack_traces(self, client):
        # Trigger an invalid analysis ID
        response = client.get("/api/v1/analysis/invalid-format-id")
        assert response.status_code == 404
        data = response.json()
        assert "error_code" in data
        assert "message" in data
        # Ensure no traceback or internal python code is exposed
        assert "Traceback" not in str(data)
        assert "File \"" not in str(data)
