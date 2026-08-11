"""
Thin wrapper around the Neo4j driver for talking to CognoDB.
All queries are parameterised. Connection details come from env vars only.
"""
import os
from contextlib import contextmanager
from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError

load_dotenv()

URI = os.getenv("COGNODB_URI")
USER = os.getenv("COGNODB_USER")
PASSWORD = os.getenv("COGNODB_PASSWORD")

_driver = None


def get_driver():
    """Lazily create a single shared driver instance."""
    global _driver
    if _driver is None:
        if not all([URI, USER, PASSWORD]):
            raise RuntimeError(
                "Missing CognoDB connection details. Set COGNODB_URI, "
                "COGNODB_USER, COGNODB_PASSWORD as environment variables."
            )
        _driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    return _driver


@contextmanager
def get_session():
    """Yields a Neo4j session, raising a friendly error if the DB is unreachable."""
    driver = get_driver()
    session = None
    try:
        session = driver.session()
        yield session
    except (ServiceUnavailable, AuthError) as e:
        raise ConnectionError(f"Could not reach CognoDB: {e}") from e
    finally:
        if session:
            session.close()


def run_query(query: str, params: dict | None = None):
    """Run a parameterised Cypher query and return a list of records as dicts."""
    with get_session() as session:
        result = session.run(query, params or {})
        return [record.data() for record in result]


def check_connection() -> bool:
    try:
        run_query("RETURN 1 AS ok")
        return True
    except Exception:
        return False
