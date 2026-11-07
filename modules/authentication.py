
"""Authentication and account creation for the curriculum optimizer."""

import bcrypt

from modules.database_connection import get_connection

ALLOWED_ROLES = {
    "Data Admin",
    "Student",
    "Faculty",
    "Curriculum Committee",
    "Academic Administrator",
}


def hash_password(password):
    """Hash a password securely using bcrypt."""
    if not isinstance(password, str) or len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")

    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(password, password_hash):
    """Verify a password against its stored bcrypt hash."""
    if not password or not password_hash:
        return False

    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8")
        )
    except (ValueError, TypeError, AttributeError):
        return False


def authenticate_user(username, password):
    """
    Authenticate an active user.

    Returns a user dictionary without the password hash,
    or None when authentication fails.
    """
    if not username or not password:
        return None

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE username = %s
              AND is_active = 1
            LIMIT 1
            """,
            (username.strip(),),
        )

        user = cursor.fetchone()

        if not user:
            return None

        stored_hash = user.get("password_hash")
        if not verify_password(password, stored_hash):
            return None

        if user.get("role") not in ALLOWED_ROLES:
            return None

        user.pop("password_hash", None)
        return user

    except Exception as exc:
        print(f"Authentication error: {exc}")
        return None

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def create_user(username, password, role, linked_id=None):
    """
    Create a user account.

    Returns True if created. Raises an error if validation or
    database insertion fails.
    """
    username = username.strip() if isinstance(username, str) else ""

    if not username:
        raise ValueError("Username is required.")

    if role not in ALLOWED_ROLES:
        raise ValueError("Invalid role.")

    password_hash = hash_password(password)

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO users
                (username, password_hash, role, linked_id, is_active)
            VALUES
                (%s, %s, %s, %s, %s)
            """,
            (username, password_hash, role, linked_id, 1),
        )

        conn.commit()
        return True

    except Exception:
        if conn is not None:
            conn.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    print("Authentication module loaded.")
    print("Supported roles:")
    for role in sorted(ALLOWED_ROLES):
        print(f" - {role}")
