from unittest.mock import MagicMock, patch

import pytest

from lexflow_api.auth.rate_limit import check_auth_rate_limit
from lexflow_api.exceptions import RateLimitError
from lexflow_api.services.virus_scan import scan_object_stub


def test_virus_scan_stub_always_clean() -> None:
    result = scan_object_stub(s3_key="firm/case/doc.pdf", mime_type="application/pdf")
    assert result.clean is True
    assert result.engine == "stub"


def test_rate_limit_raises_after_limit() -> None:
    cache = MagicMock()
    cache.get.return_value = "10"
    with patch("lexflow_api.auth.rate_limit._client", return_value=cache):
        with pytest.raises(RateLimitError):
            check_auth_rate_limit(scope="login", identifier="1.2.3.4", limit=10, window_sec=60)


def test_rate_limit_increments() -> None:
    cache = MagicMock()
    cache.get.return_value = None
    with patch("lexflow_api.auth.rate_limit._client", return_value=cache):
        check_auth_rate_limit(scope="login", identifier="1.2.3.4", limit=10, window_sec=60)
    cache.set.assert_called_once_with("ratelimit:login:1.2.3.4", "1", ttl=60)
