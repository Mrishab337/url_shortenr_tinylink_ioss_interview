from pydantic import BaseModel, HttpUrl, field_validator
from typing import Optional

class ShortenRequest(BaseModel):
    url: HttpUrl
    custom_alias: Optional[str] = None
    expires_in_days: Optional[int] = None

    @field_validator('custom_alias')
    @classmethod
    def validate_alias(cls, v):
        if v is None:
            return v
        if not v.replace('-', '').replace('_','').isalnum():
            raise ValueError('Alias may contain only letters, numbers, hyphens, and underscores.')
        if len(v) < 3 or len(v) > 32:
            raise ValueError('Alias must be between 3 and 32 characters.')
        return v

    @field_validator('expires_in_days')
    @classmethod
    def validate_expiry(cls, v):
        if v is None:
            return v
        if v <= 0 or v > 3650:
            raise ValueError('Expiry must be between 1 and 3650 days.')
        return v

class ShortenResponse(BaseModel):
    short_url: str
    code: str
