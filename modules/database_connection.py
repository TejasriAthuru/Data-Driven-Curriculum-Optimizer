import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv


# Find the project root folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load .env from the project root
load_dotenv(PROJECT_ROOT / ".env")


def get_connection():
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT", "3306")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    database = os.getenv("DB_NAME")

    # Check that all required settings are available
    missing = []

    if not host:
        missing.append("DB_HOST")
    if not user:
        missing.append("DB_USER")
    if not password:
        missing.append("DB_PASSWORD")
    if not database:
        missing.append("DB_NAME")

    if missing:
        raise RuntimeError(
            "Missing database settings in .env: "
            + ", ".join(missing)
        )

    connection = mysql.connector.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database=database,
        connection_timeout=10
    )

    return connection


if __name__ == "__main__":
    connection = get_connection()

    if connection.is_connected():
        print("Successfully connected to MySQL.")
        print("Database: curriculum_optimizer")

    connection.close()
    print("Connection closed.")