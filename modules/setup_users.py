
from getpass import getpass

from modules.authentication import create_user, hash_password
from modules.database_connection import get_connection


ACCOUNTS = [
    ("admin_demo", "Data Admin", None),
    ("student_demo", "Student", "CSE001"),
    ("faculty_demo", "Faculty", "F001"),
    ("committee_demo", "Curriculum Committee", None),
    ("academic_admin_demo", "Academic Administrator", None),
]


def main():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        for username, role, linked_id in ACCOUNTS:
            print(f"\nAccount: {username} ({role})")
            password = getpass("Enter NEW password: ")
            confirm = getpass("Confirm NEW password: ")

            if password != confirm:
                print("Passwords do not match. Skipped.")
                continue

            try:
                password_hash = hash_password(password)

                cursor.execute(
                    "SELECT user_id FROM users WHERE username = %s",
                    (username,)
                )
                existing = cursor.fetchone()

                if existing:
                    cursor.execute(
                        """
                        UPDATE users
                        SET password_hash = %s,
                            role = %s,
                            linked_id = %s,
                            is_active = TRUE
                        WHERE username = %s
                        """,
                        (password_hash, role, linked_id, username)
                    )
                    print("Existing account password reset.")
                else:
                    cursor.execute(
                        """
                        INSERT INTO users
                            (username, password_hash, role, linked_id)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (username, password_hash, role, linked_id)
                    )
                    print("New account created.")

                connection.commit()

            except Exception as error:
                connection.rollback()
                print(f"Could not update this account: {error}")

    finally:
        cursor.close()
        connection.close()

    print("\nAccount setup completed.")


if __name__ == "__main__":
    main()
