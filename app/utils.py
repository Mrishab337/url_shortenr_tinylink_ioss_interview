import secrets
import string

ALPHABET = string.ascii_letters + string.digits  # base62

def gen_code(length: int = 6) -> str:
    # URL-safe, collision-resistant short code
    return ''.join(secrets.choice(ALPHABET) for _ in range(length))
