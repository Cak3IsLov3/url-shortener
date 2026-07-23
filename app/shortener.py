"""Short code generation."""
import secrets
import string

from sqlmodel import Session, select

from app.models import ShortURL

# Alphabet used for the random codes: 26 + 26 + 10 = 62 characters.
ALPHABET = string.ascii_letters + string.digits


def generate_code(length: int) -> str:
    """Generate a random code of the given length using a CSPRNG."""
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def generate_unique_code(session: Session, length: int, max_attempts: int) -> str:
    """Generate a code that does not yet exist in the database.

    Retries up to `max_attempts` times before giving up. In practice a
    collision is astronomically unlikely for 6+ character codes until the
    table has billions of rows, but we still guard against it because a
    duplicate `code` would violate the UNIQUE constraint on ShortURL.code.
    """
    for _ in range(max_attempts):
        code = generate_code(length)
        exists = session.exec(select(ShortURL).where(ShortURL.code == code)).first()
        if exists is None:
            return code
    raise RuntimeError(
        f"Failed to generate a unique code after {max_attempts} attempts"
    )
