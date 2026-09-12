from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_upload(file):
    """Restrict customer uploads (artwork, documents) by size and extension."""
    if file.size > settings.MAX_UPLOAD_SIZE:
        raise ValidationError(f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE // (1024 * 1024)} MB.")
    ext = Path(file.name).suffix.lower().lstrip(".")
    if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        raise ValidationError(
            "Unsupported file type. Allowed: " + ", ".join(settings.ALLOWED_UPLOAD_EXTENSIONS)
        )
