from unittest.mock import MagicMock, patch

from src.services.storage import presign_put


def test_presign_put_returns_url() -> None:
    mock_cli = MagicMock()
    mock_cli.generate_presigned_url.return_value = "https://example.com/upload"
    with patch("src.services.storage._client", return_value=mock_cli):
        url = presign_put("users/abc/resume.pdf", "application/pdf")
    assert url == "https://example.com/upload"
    mock_cli.generate_presigned_url.assert_called_once()
